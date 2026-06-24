import os
import uuid
import json
from backend.app.db.database import execute, rows, one
from backend.app.services.config_service import providers, agents
from backend.app.adapters.openai_compatible import chat as openai_chat
from backend.app.services.audit_service import record

def _provider(name):
    for p in providers():
        if p.get('name') == name: return p
    raise ValueError('provider not configured')

def _agent(name):
    for a in agents():
        if a.get('name') == name: return a
    return None

def _agent_can_chat(agent_cfg: dict) -> bool:
    allowed=set(agent_cfg.get('allowed_tools') or []) | set(agent_cfg.get('capabilities') or [])
    provider=agent_cfg.get('provider')
    return 'chat' in allowed or 'memory-read' in allowed or provider in {'deepseek','openwebui','hermes'}

def _scoped_memory(agent_name: str, agent_cfg: dict) -> list[dict]:
    allowed=set(agent_cfg.get('allowed_tools') or []) | set(agent_cfg.get('capabilities') or [])
    if 'memory-read' not in allowed and 'memory' not in allowed:
        return []
    scopes=agent_cfg.get('memory_scopes') or []
    workspace_access=agent_cfg.get('workspace_access') or []
    conditions=[]
    params=[]
    if 'global' in scopes:
        conditions.append("scope='global'")
    if 'agent' in scopes:
        conditions.append("agent=?")
        params.append(agent_name)
    if 'workspace' in scopes and workspace_access:
        placeholders=','.join(['?']*len(workspace_access))
        conditions.append(f"workspace IN ({placeholders})")
        params.extend(workspace_access)
    if 'project' in scopes:
        conditions.append("scope='project'")
    if not conditions:
        return []
    sql='SELECT title, content, scope, workspace, agent FROM memory_records WHERE ' + ' OR '.join(f'({c})' for c in conditions) + ' ORDER BY updated_at DESC LIMIT 12'
    return rows(sql, tuple(params))

def _system_messages(agent_name: str, agent_cfg: dict) -> list[dict[str,str]]:
    messages=[]
    system=agent_cfg.get('system_prompt') or agent_cfg.get('role')
    if system:
        messages.append({'role':'system','content':system})
    grants={
        'agent': agent_name,
        'allowed_tools': agent_cfg.get('allowed_tools') or [],
        'capabilities': agent_cfg.get('capabilities') or [],
        'workspace_access': agent_cfg.get('workspace_access') or [],
        'memory_scopes': agent_cfg.get('memory_scopes') or [],
        'mcp_channels': agent_cfg.get('mcp_channels') or [],
        'approval_policy': agent_cfg.get('approval_policy') or 'ask-before-run',
    }
    messages.append({'role':'system','content':'Agentic OS grants for this agent: '+json.dumps(grants, ensure_ascii=False)+'. Do not claim access to tools, files, memory, or external actions outside these grants. Ask for approval when the approval policy requires it.'})
    memory=_scoped_memory(agent_name, agent_cfg)
    if memory:
        block='\n\n'.join([f"[{m.get('scope') or 'memory'}] {m.get('title')}\n{m.get('content')}" for m in memory])
        messages.append({'role':'system','content':'Allowed Agentic OS memory/context for this turn:\n'+block[:12000]})
    return messages

async def send_chat(message: str, agent: str='deepseek-chat', thread_id: str | None=None, actor='local-admin', model_override: str | None=None):
    a=_agent(agent) or {}
    if not a:
        raise ValueError(f'agent {agent} is not configured')
    if not _agent_can_chat(a):
        raise ValueError(f'agent {agent} does not have chat or memory-read capability enabled')
    p=_provider(a.get('provider','openwebui'))
    model=model_override or p.get('default_model') or a.get('model')
    endpoint=p.get('endpoint')
    if not endpoint:
        raise ValueError('missing endpoint')
    if not model or str(model).startswith('selected-'):
        raise ValueError('select a runtime model before chatting with this agent')
    tid=thread_id or str(uuid.uuid4())
    if not one('SELECT id FROM chat_threads WHERE id=?', (tid,)):
        execute('INSERT INTO chat_threads(id,title,agent,provider,model) VALUES (?,?,?,?,?)', (tid, message[:60] or f'{agent} chat', agent, p.get('name'), model))
    execute('INSERT INTO chat_messages(thread_id,role,content) VALUES (?,?,?)', (tid,'user',message))
    hist=rows('SELECT role, content FROM chat_messages WHERE thread_id=? ORDER BY id ASC', (tid,))
    llm_messages=_system_messages(agent, a)+hist
    try:
        api_key = os.getenv(p.get('api_key_env','')) if p.get('api_key_env') else None
        content = await openai_chat(endpoint, model, llm_messages, api_key)
        execute('INSERT INTO chat_messages(thread_id,role,content) VALUES (?,?,?)', (tid,'assistant',content))
        execute('UPDATE chat_threads SET updated_at=CURRENT_TIMESTAMP, agent=?, provider=?, model=? WHERE id=?', (agent, p.get('name'), model, tid))
        record('chat.request', 'ok', actor=actor, target_agent=agent, command_type='chat', metadata={'thread_id':tid,'provider':p.get('name'),'model':model,'memory_injected':len(_scoped_memory(agent,a))})
        return {'thread_id': tid, 'message': content}
    except Exception as e:
        record('chat.request', 'failed', actor=actor, target_agent=agent, command_type='chat', error=e, metadata={'thread_id':tid})
        raise

def threads(): return rows('SELECT * FROM chat_threads ORDER BY updated_at DESC')
def thread(tid): return {'thread': one('SELECT * FROM chat_threads WHERE id=?',(tid,)), 'messages': rows('SELECT * FROM chat_messages WHERE thread_id=? ORDER BY id',(tid,))}

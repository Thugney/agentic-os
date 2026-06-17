import os
import uuid
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

async def send_chat(message: str, agent: str='deepseek-chat', thread_id: str | None=None, actor='local-admin'):
    a=_agent(agent) or {}
    p=_provider(a.get('provider','openwebui'))
    model=a.get('model') or p.get('default_model')
    endpoint=p.get('endpoint')
    if not endpoint or not model:
        raise ValueError('missing endpoint or model')
    tid=thread_id or str(uuid.uuid4())
    if not one('SELECT id FROM chat_threads WHERE id=?', (tid,)):
        execute('INSERT INTO chat_threads(id,title,agent,provider,model) VALUES (?,?,?,?,?)', (tid, message[:60] or 'New chat', agent, p.get('name'), model))
    execute('INSERT INTO chat_messages(thread_id,role,content) VALUES (?,?,?)', (tid,'user',message))
    hist=rows('SELECT role, content FROM chat_messages WHERE thread_id=? ORDER BY id ASC', (tid,))
    try:
        api_key = os.getenv(p.get('api_key_env','')) if p.get('api_key_env') else None
        content = await openai_chat(endpoint, model, hist, api_key)
        execute('INSERT INTO chat_messages(thread_id,role,content) VALUES (?,?,?)', (tid,'assistant',content))
        execute('UPDATE chat_threads SET updated_at=CURRENT_TIMESTAMP WHERE id=?', (tid,))
        record('chat.request', 'ok', actor=actor, target_agent=agent, command_type='chat', metadata={'thread_id':tid,'provider':p.get('name'),'model':model})
        return {'thread_id': tid, 'message': content}
    except Exception as e:
        record('chat.request', 'failed', actor=actor, target_agent=agent, command_type='chat', error=e, metadata={'thread_id':tid})
        raise

def threads(): return rows('SELECT * FROM chat_threads ORDER BY updated_at DESC')
def thread(tid): return {'thread': one('SELECT * FROM chat_threads WHERE id=?',(tid,)), 'messages': rows('SELECT * FROM chat_messages WHERE thread_id=? ORDER BY id',(tid,))}

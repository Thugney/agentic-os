import json
import uuid
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from backend.app.core.settings import get_settings
from backend.app.core.security import actor_from_token
from backend.app.db.database import rows, execute, one
from backend.app.services import config_service
from backend.app.services.audit_service import list_audit, record
from backend.app.services.workspace_service import workspace_statuses
from backend.app.services.chat_service import send_chat, threads, thread
from backend.app.services.codex_service import start_codex, sessions as codex_sessions, get_session, cancel

router=APIRouter(prefix='/api')
class ChatIn(BaseModel):
    message: str
    agent: str='deepseek-chat'
    thread_id: str|None=None
class CodexIn(BaseModel):
    task: str
    workspace: str
    branch: str|None=None
    test_command: str|None=None
    auto_commit: bool=False
    background: bool=True
class KanbanIn(BaseModel):
    title: str
    description: str=''
    status: str='Backlog'
    workspace: str|None=None
    agent_session: str|None=None
    git_branch: str|None=None
    artifact: str|None=None
    chat_thread: str|None=None
class MemoryIn(BaseModel):
    title: str
    content: str
    scope: str='global'
    tags: list[str]=[]
    source_session: str|None=None

def actor(req: Request):
    return actor_from_token(req.headers.get('x-admin-token') or req.headers.get('authorization'))

@router.get('/health')
def health():
    s=get_settings()
    return {'status':'healthy','app':'Agentic OS','data_dir':str(s.data_dir),'sqlite_path':str(s.db_path)}

@router.get('/systems/status')
def systems_status():
    agents=config_service.agents()
    recent_failed=rows("SELECT * FROM audit_log WHERE status IN ('failed','error') ORDER BY id DESC LIMIT 5")
    return {'heartbeat':'online','systems':[{'name':a.get('name'),'provider':a.get('provider'),'enabled':a.get('enabled',True),'latency_ms':None,'active_sessions':0,'latest_activity':None} for a in agents], 'recent_failed_actions': recent_failed}

@router.get('/agents')
def get_agents(): return config_service.agents()
@router.get('/workspaces')
def get_workspaces(): return workspace_statuses()
@router.get('/settings/effective')
def settings_effective(): return config_service.effective_settings()
@router.get('/skills')
def get_skills(): return config_service.skills()

@router.get('/chat/threads')
def chat_threads(): return threads()
@router.get('/chat/threads/{tid}')
def chat_thread(tid: str): return thread(tid)
@router.post('/chat')
async def chat_post(body: ChatIn, request: Request):
    try: return await send_chat(body.message, body.agent, body.thread_id, actor(request))
    except Exception as e: raise HTTPException(502, str(e))

@router.get('/codex/sessions')
def codex_list(): return codex_sessions()
@router.post('/codex/run')
def codex_run(body: CodexIn, request: Request):
    try: return start_codex(**body.model_dump(), actor=actor(request))
    except Exception as e:
        record('codex.run.start','failed',actor=actor(request),target_agent='codex-worker',workspace=body.workspace,command_type='codex',error=e)
        raise HTTPException(400, str(e))
@router.get('/codex/sessions/{sid}')
def codex_get(sid: str):
    s=get_session(sid)
    if not s: raise HTTPException(404,'not found')
    return s
@router.post('/codex/sessions/{sid}/cancel')
def codex_cancel(sid: str): return cancel(sid)

@router.get('/kanban/tasks')
def kanban_tasks(): return rows('SELECT * FROM kanban_tasks ORDER BY created_at DESC')
@router.post('/kanban/tasks')
def kanban_create(body: KanbanIn, request: Request):
    tid=str(uuid.uuid4())
    execute('INSERT INTO kanban_tasks(id,title,description,status,workspace,agent_session,git_branch,artifact,chat_thread) VALUES (?,?,?,?,?,?,?,?,?)', (tid, body.title, body.description, body.status, body.workspace, body.agent_session, body.git_branch, body.artifact, body.chat_thread))
    record('kanban.create','ok',actor=actor(request),workspace=body.workspace,metadata={'task_id':tid})
    return one('SELECT * FROM kanban_tasks WHERE id=?',(tid,))
@router.patch('/kanban/tasks/{tid}')
def kanban_patch(tid: str, body: dict, request: Request):
    allowed={'title','description','status','workspace','agent_session','git_branch','artifact','chat_thread'}
    for k,v in body.items():
        if k in allowed:
            execute(f'UPDATE kanban_tasks SET {k}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',(v,tid))
    record('kanban.update','ok',actor=actor(request),metadata={'task_id':tid})
    return one('SELECT * FROM kanban_tasks WHERE id=?',(tid,))

@router.get('/memory')
def memory(q: str|None=None):
    if q: return rows('SELECT * FROM memory_records WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC', (f'%{q}%', f'%{q}%'))
    return rows('SELECT * FROM memory_records ORDER BY updated_at DESC')
@router.post('/memory')
def memory_create(body: MemoryIn, request: Request):
    mid=str(uuid.uuid4())
    execute('INSERT INTO memory_records(id,title,content,scope,tags,source_session) VALUES (?,?,?,?,?,?)', (mid, body.title, body.content, body.scope, json.dumps(body.tags), body.source_session))
    record('memory.create','ok',actor=actor(request),metadata={'memory_id':mid,'scope':body.scope})
    return one('SELECT * FROM memory_records WHERE id=?',(mid,))

@router.get('/audit')
def audit(agent: str|None=None, workspace: str|None=None, status: str|None=None, limit: int=250): return list_audit(limit, agent, workspace, status)
@router.get('/audit/export.jsonl')
def audit_export():
    lines='\n'.join(json.dumps(r) for r in list_audit(10000))
    return PlainTextResponse(lines, media_type='application/jsonl')

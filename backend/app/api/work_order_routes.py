from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.app.core.security import actor_from_token
from backend.app.db.database import rows
from backend.app.services.runtime_adapter_service import runtime_statuses, runtime_status
from backend.app.services.work_order_service import list_work_orders, get_work_order, create_work_order, patch_work_order, approve_work_order, run_work_order

API_ROUTE = chr(47)
router = APIRouter(prefix=API_ROUTE + 'api')


class WorkOrderIn(BaseModel):
    title: str
    description: str = ''
    status: str = 'Backlog'
    priority: str = 'normal'
    assigned_agent: str | None = None
    agent: str | None = None
    capability_id: str | None = None
    workspace: str | None = None
    memory_scope: str = 'workspace'
    schedule: str = 'manual'
    schedule_intent: str | None = None
    due_at: str | None = None
    approval_gate: str = 'ask-before-run'
    approval_state: str = 'needs_approval'
    validation_command: str | None = None
    agent_session: str | None = None
    run_session_id: str | None = None
    git_branch: str | None = None
    artifact: str | None = None
    artifact_refs: list[str] | str | None = None
    chat_thread: str | None = None


def actor(req: Request):
    return actor_from_token(req.headers.get('x-admin-token') or req.headers.get('authorization'))


@router.get(API_ROUTE + 'systems/status')
def systems_status():
    recent_failed = rows("SELECT * FROM audit_log WHERE status IN ('failed','error','blocked') ORDER BY id DESC LIMIT 5")
    active = rows("SELECT * FROM agent_processes WHERE status='running' ORDER BY started_at DESC")
    return {'heartbeat': 'online', 'systems': runtime_statuses(), 'active_processes': active, 'recent_failed_actions': recent_failed}


@router.get(API_ROUTE + 'runtime/adapters')
def runtime_adapters():
    return runtime_statuses()


@router.get(API_ROUTE + 'runtime/adapters/{name}')
def runtime_adapter(name: str):
    status = runtime_status(name)
    if not status:
        raise HTTPException(404, 'runtime adapter not found')
    return status


@router.get(API_ROUTE + 'kanban/tasks')
def work_orders():
    return list_work_orders()


@router.get(API_ROUTE + 'kanban/tasks/{tid}')
def work_order(tid: str):
    task = get_work_order(tid)
    if not task:
        raise HTTPException(404, 'work order not found')
    return task


@router.post(API_ROUTE + 'kanban/tasks')
def work_order_create(body: WorkOrderIn, request: Request):
    try:
        return create_work_order(body.model_dump(), actor=actor(request))
    except Exception as e:
        raise HTTPException(400, str(e))


@router.patch(API_ROUTE + 'kanban/tasks/{tid}')
def work_order_patch(tid: str, body: dict, request: Request):
    try:
        return patch_work_order(tid, body, actor=actor(request))
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post(API_ROUTE + 'kanban/tasks/{tid}' + API_ROUTE + 'approve')
def work_order_approve(tid: str, request: Request):
    try:
        return approve_work_order(tid, actor=actor(request))
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post(API_ROUTE + 'kanban/tasks/{tid}' + API_ROUTE + 'run')
async def work_order_run(tid: str, request: Request):
    try:
        return await run_work_order(tid, actor=actor(request))
    except Exception as e:
        raise HTTPException(400, str(e))

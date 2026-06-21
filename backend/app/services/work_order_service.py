import json
import uuid
from typing import Any

from backend.app.db.database import execute, one, rows
from backend.app.services.audit_service import record
from backend.app.services.runtime_adapter_service import runtime_status, can_use_workspace
from backend.app.services.codex_service import start_codex
from backend.app.services.chat_service import send_chat

WORK_ORDER_COLUMNS = {
    'title', 'description', 'status', 'priority', 'assigned_agent', 'agent', 'capability_id',
    'workspace', 'memory_scope', 'schedule', 'schedule_intent', 'due_at', 'approval_gate',
    'approval_state', 'validation_command', 'agent_session', 'run_session_id', 'git_branch',
    'artifact', 'artifact_refs', 'chat_thread'
}

STATUS_FLOW = {'Backlog', 'Ready', 'Running', 'Review', 'Done', 'Failed'}
APPROVAL_STATES = {'draft', 'needs_approval', 'approved', 'blocked', 'running', 'completed', 'failed'}


def _json(value: Any) -> str:
    if value is None:
        return '[]'
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _normalize_agent(payload: dict[str, Any]) -> str | None:
    return payload.get('agent') or payload.get('assigned_agent')


def _row(tid: str) -> dict[str, Any] | None:
    return one('SELECT * FROM kanban_tasks WHERE id=?', (tid,))


def list_work_orders() -> list[dict[str, Any]]:
    return rows('SELECT * FROM kanban_tasks ORDER BY created_at DESC')


def get_work_order(tid: str) -> dict[str, Any] | None:
    task = _row(tid)
    if not task:
        return None
    agent = task.get('agent') or task.get('assigned_agent')
    task['runtime'] = runtime_status(agent) if agent else None
    return task


def create_work_order(payload: dict[str, Any], actor: str = 'local-admin') -> dict[str, Any]:
    title = (payload.get('title') or '').strip()
    if not title:
        raise ValueError('title is required')
    tid = str(uuid.uuid4())
    agent = _normalize_agent(payload)
    approval_state = payload.get('approval_state') or 'needs_approval'
    if approval_state not in APPROVAL_STATES:
        raise ValueError('invalid approval_state')
    status = payload.get('status') or 'Backlog'
    if status not in STATUS_FLOW:
        raise ValueError('invalid status')
    execute('''
        INSERT INTO kanban_tasks(
            id,title,description,status,priority,assigned_agent,agent,capability_id,workspace,
            memory_scope,schedule,schedule_intent,due_at,approval_gate,approval_state,
            validation_command,agent_session,run_session_id,git_branch,artifact,artifact_refs,chat_thread
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        tid, title, payload.get('description', ''), status, payload.get('priority', 'normal'),
        agent, agent, payload.get('capability_id'), payload.get('workspace'), payload.get('memory_scope', 'workspace'),
        payload.get('schedule', 'manual'), payload.get('schedule_intent') or payload.get('schedule', 'manual'),
        payload.get('due_at'), payload.get('approval_gate', 'ask-before-run'), approval_state,
        payload.get('validation_command'), payload.get('agent_session'), payload.get('run_session_id'),
        payload.get('git_branch'), payload.get('artifact'), _json(payload.get('artifact_refs')), payload.get('chat_thread')
    ))
    record('work_order.create', 'ok', actor=actor, target_agent=agent, workspace=payload.get('workspace'), command_type='work_order', metadata={'task_id': tid, 'capability_id': payload.get('capability_id'), 'approval_state': approval_state})
    return get_work_order(tid) or {}


def patch_work_order(tid: str, payload: dict[str, Any], actor: str = 'local-admin') -> dict[str, Any]:
    if not _row(tid):
        raise ValueError('work order not found')
    for key, value in payload.items():
        if key not in WORK_ORDER_COLUMNS:
            continue
        if key == 'status' and value not in STATUS_FLOW:
            raise ValueError('invalid status')
        if key == 'approval_state' and value not in APPROVAL_STATES:
            raise ValueError('invalid approval_state')
        if key in {'artifact_refs'}:
            value = _json(value)
        execute(f'UPDATE kanban_tasks SET {key}=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (value, tid))
    record('work_order.update', 'ok', actor=actor, metadata={'task_id': tid, 'fields': sorted([k for k in payload if k in WORK_ORDER_COLUMNS])})
    return get_work_order(tid) or {}


def approve_work_order(tid: str, actor: str = 'local-admin') -> dict[str, Any]:
    if not _row(tid):
        raise ValueError('work order not found')
    execute('UPDATE kanban_tasks SET approval_state=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', ('approved', 'Ready', tid))
    task = get_work_order(tid) or {}
    record('work_order.approve', 'ok', actor=actor, target_agent=task.get('agent') or task.get('assigned_agent'), workspace=task.get('workspace'), command_type='approval', metadata={'task_id': tid})
    return task


async def run_work_order(tid: str, actor: str = 'local-admin') -> dict[str, Any]:
    task = get_work_order(tid)
    if not task:
        raise ValueError('work order not found')
    agent = task.get('agent') or task.get('assigned_agent')
    if not agent:
        raise ValueError('work order has no assigned agent/runtime')
    if task.get('approval_state') != 'approved':
        execute('UPDATE kanban_tasks SET approval_state=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', ('blocked', tid))
        record('work_order.run.blocked', 'blocked', actor=actor, target_agent=agent, workspace=task.get('workspace'), command_type='work_order', metadata={'task_id': tid, 'reason': 'approval required'})
        raise ValueError('approval_state must be approved before run')
    runtime = runtime_status(agent)
    if not runtime:
        raise ValueError(f'no runtime adapter registered for {agent}')
    if not runtime.get('ready'):
        execute('UPDATE kanban_tasks SET approval_state=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', ('blocked', tid))
        record('work_order.run.blocked', 'blocked', actor=actor, target_agent=agent, workspace=task.get('workspace'), command_type='work_order', metadata={'task_id': tid, 'reason': runtime.get('detail')})
        raise ValueError(runtime.get('detail') or 'runtime is not ready')
    ok, msg = can_use_workspace(agent, task.get('workspace'))
    if runtime.get('adapter_key') == 'codex' and not ok:
        record('work_order.run.blocked', 'blocked', actor=actor, target_agent=agent, workspace=task.get('workspace'), command_type='work_order', metadata={'task_id': tid, 'reason': msg})
        raise ValueError(msg)

    execute('UPDATE kanban_tasks SET approval_state=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', ('running', 'Running', tid))
    record('work_order.run.start', 'ok', actor=actor, target_agent=agent, workspace=task.get('workspace'), command_type='work_order', metadata={'task_id': tid, 'adapter': runtime.get('adapter_key')})

    adapter = runtime.get('adapter_key')
    if adapter == 'codex':
        session = start_codex(
            task=f"{task.get('title')}\n\n{task.get('description') or ''}",
            workspace=task.get('workspace'),
            branch=task.get('git_branch'),
            test_command=task.get('validation_command'),
            auto_commit=False,
            background=True,
            actor=actor,
        )
        sid = session.get('id')
        execute('UPDATE kanban_tasks SET run_session_id=?, agent_session=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (sid, sid, 'Running', tid))
        return get_work_order(tid) or {}
    if adapter == 'deepseek':
        result = await send_chat(f"Work order: {task.get('title')}\n\n{task.get('description') or ''}", agent=agent, thread_id=task.get('chat_thread'), actor=actor)
        thread_id = result.get('thread_id')
        execute('UPDATE kanban_tasks SET chat_thread=?, run_session_id=?, approval_state=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (thread_id, thread_id, 'completed', 'Review', tid))
        record('work_order.run.complete', 'ok', actor=actor, target_agent=agent, workspace=task.get('workspace'), command_type='chat', metadata={'task_id': tid, 'thread_id': thread_id})
        return get_work_order(tid) or {}

    execute('UPDATE kanban_tasks SET approval_state=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', ('blocked', 'Failed', tid))
    record('work_order.run.blocked', 'blocked', actor=actor, target_agent=agent, workspace=task.get('workspace'), command_type='work_order', metadata={'task_id': tid, 'reason': f'{adapter} execution path is not implemented'})
    raise ValueError(f'{adapter} execution path is not implemented')

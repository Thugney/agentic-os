from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from backend.app.core.security import actor_from_token
from backend.app.db.database import rows
from backend.app.services.audit_service import record
from backend.app.services.codex_service import start_codex
from backend.app.services.hermes_service import send_hermes_chat
from backend.app.services.runtime_service import runtime_status, test_provider
from backend.app.services import config_service

router = APIRouter(prefix='/api')

class RuntimeCodexIn(BaseModel):
    task: str
    workspace: str
    branch: str | None = None
    test_command: str | None = None
    auto_commit: bool = False
    background: bool = True

class RuntimeHermesChatIn(BaseModel):
    message: str
    thread_id: str | None = None

class ProviderPatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    label: str | None = None
    type: str | None = None
    connection_mode: str | None = None
    endpoint: str | None = None
    url_env: str | None = None
    default_model: str | None = None
    model_selection: str | None = None
    api_key_env: str | None = None
    cli_binary: str | None = None
    auth_mode: str | None = None
    enabled: bool | None = None
    notes: str | None = None

class AgentPatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    label: str | None = None
    provider: str | None = None
    model: str | None = None
    endpoint: str | None = None
    enabled: bool | None = None
    workspace: str | None = None
    role: str | None = None
    allowed_tools: list[str] | None = None
    workspace_access: list[str] | None = None
    memory_scopes: list[str] | None = None
    mcp_channels: list[str] | None = None
    system_prompt: str | None = None
    approval_policy: str | None = None

class WorkspaceRegister(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    path: str
    default_branch: str | None = None
    description: str | None = None
    allowed_commands: list[str] = []
    allowed_agents: list[str] = []
    memory_scopes: list[str] = []

def actor(req: Request):
    return actor_from_token(req.headers.get('x-admin-token') or req.headers.get('authorization'))

@router.get('/systems/status')
async def systems_status_runtime():
    status = await runtime_status()
    recent_failed = rows("SELECT * FROM audit_log WHERE status IN ('failed','error') ORDER BY id DESC LIMIT 5")
    active = rows("SELECT * FROM agent_processes WHERE status='running' ORDER BY started_at DESC")
    for system in status['systems']:
        prefix = str(system.get('name','')).split('-')[0]
        system['active_sessions'] = len([p for p in active if prefix in p.get('kind','')])
    status['active_processes'] = active
    status['recent_failed_actions'] = recent_failed
    return status

@router.post('/codex/run')
async def codex_run_runtime(body: RuntimeCodexIn, request: Request):
    try:
        return start_codex(**body.model_dump(), actor=actor(request))
    except Exception as e:
        record('codex.run.start','failed',actor=actor(request),target_agent='codex-worker',workspace=body.workspace,command_type='codex',error=e)
        raise HTTPException(400, str(e))

@router.post('/hermes/chat')
def hermes_chat_runtime(body: RuntimeHermesChatIn, request: Request):
    try:
        return send_hermes_chat(body.message, body.thread_id, actor(request))
    except Exception as e:
        raise HTTPException(502, str(e))

@router.post('/runtime/providers')
def update_provider(body: ProviderPatch, request: Request):
    payload = body.model_dump(exclude={'name'}, exclude_none=True)
    try:
        provider = config_service.set_provider(body.name, payload)
        record('runtime.provider.update','ok',actor=actor(request),command_type='config',metadata={'provider': body.name, 'fields': sorted(payload.keys())})
        return {'provider': provider, 'settings': config_service.effective_settings()}
    except Exception as e:
        record('runtime.provider.update','failed',actor=actor(request),command_type='config',error=e,metadata={'provider': body.name})
        raise HTTPException(400, str(e))

@router.post('/runtime/agents')
def update_agent(body: AgentPatch, request: Request):
    payload = body.model_dump(exclude={'name'}, exclude_none=True)
    try:
        agent = config_service.set_agent(body.name, payload)
        record('runtime.agent.update','ok',actor=actor(request),target_agent=body.name,command_type='config',metadata={'fields': sorted(payload.keys())})
        return {'agent': agent, 'settings': config_service.effective_settings()}
    except Exception as e:
        record('runtime.agent.update','failed',actor=actor(request),target_agent=body.name,command_type='config',error=e)
        raise HTTPException(400, str(e))

@router.post('/runtime/providers/{name}/test')
async def test_runtime_provider(name: str, request: Request):
    try:
        result = await test_provider(name)
        record('runtime.provider.test','ok' if result.get('ready') else 'failed',actor=actor(request),command_type='probe',metadata={'provider': name, 'status': result.get('status'), 'detail': result.get('detail')})
        return result
    except Exception as e:
        record('runtime.provider.test','failed',actor=actor(request),command_type='probe',error=e,metadata={'provider': name})
        raise HTTPException(400, str(e))

@router.post('/workspaces/register')
def register_workspace(body: WorkspaceRegister, request: Request):
    try:
        workspace = config_service.add_workspace(body.model_dump(exclude_none=True))
        record('workspace.register','ok',actor=actor(request),workspace=workspace.get('name'),command_type='config',metadata={'path': workspace.get('path'), 'allowed_agents': workspace.get('allowed_agents', [])})
        return {'workspace': workspace, 'settings': config_service.effective_settings()}
    except Exception as e:
        record('workspace.register','failed',actor=actor(request),workspace=body.name,command_type='config',error=e)
        raise HTTPException(400, str(e))

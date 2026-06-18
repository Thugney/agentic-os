import os
import shutil
import subprocess
import uuid
from typing import Any

import httpx

from backend.app.db.database import execute, one, rows
from backend.app.services.audit_service import record
from backend.app.services import config_service


def _hermes_binary() -> str | None:
    configured = os.getenv('HERMES_CLI')
    if configured and shutil.which(configured):
        return configured
    return shutil.which('hermes')


def _provider_endpoint() -> str | None:
    for provider in config_service.providers():
        if provider.get('name') == 'hermes':
            return provider.get('endpoint')
    return None


def _hermes_base_url() -> str | None:
    return (os.getenv('HERMES_URL') or _provider_endpoint() or '').rstrip('/') or None


def _thread(tid: str, title: str, provider: str, model: str):
    if not one('SELECT id FROM chat_threads WHERE id=?', (tid,)):
        execute('INSERT INTO chat_threads(id,title,agent,provider,model) VALUES (?,?,?,?,?)', (tid, title[:60] or 'Hermes chat', 'hermes-control', provider, model))


def _messages_for_thread(tid: str) -> list[dict[str, str]]:
    existing = rows('SELECT role, content FROM chat_messages WHERE thread_id=? ORDER BY id ASC', (tid,))
    return [{'role': item.get('role') if item.get('role') in {'system','user','assistant'} else 'user', 'content': item.get('content','')} for item in existing]


async def _send_remote_openai_compatible(base_url: str, message: str, tid: str, actor: str) -> dict[str, Any]:
    model = os.getenv('HERMES_API_MODEL', 'hermes')
    profile = os.getenv('HERMES_PROFILE') or os.getenv('HERMES_DEFAULT_PROFILE')
    messages = _messages_for_thread(tid) + [{'role': 'user', 'content': message}]
    payload: dict[str, Any] = {'model': model, 'messages': messages, 'stream': False}
    headers: dict[str, str] = {'Content-Type': 'application/json'}
    if profile:
        headers['X-Hermes-Profile'] = profile
    api_key = os.getenv('HERMES_API_KEY')
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    url = base_url.rstrip('/') + '/v1/chat/completions'
    async with httpx.AsyncClient(timeout=int(os.getenv('HERMES_CHAT_TIMEOUT', '180'))) as client:
        response = await client.post(url, json=payload, headers=headers)
    if response.status_code >= 400:
        raise RuntimeError(f'Hermes remote chat route {url} returned HTTP {response.status_code}: {response.text[:500]}')
    data = response.json()
    output = ''
    try:
        output = data['choices'][0]['message']['content']
    except Exception:
        output = str(data)
    execute('INSERT INTO chat_messages(thread_id,role,content) VALUES (?,?,?)', (tid, 'assistant', output))
    execute('UPDATE chat_threads SET updated_at=CURRENT_TIMESTAMP, provider=?, model=? WHERE id=?', ('hermes-remote-api', model, tid))
    record('hermes.chat', 'ok', actor=actor, target_agent='hermes-control', command_type='hermes-remote-api', metadata={'thread_id': tid, 'url': url, 'profile': profile or 'default'})
    return {'thread_id': tid, 'message': output, 'provider': 'hermes-remote-api', 'model': model, 'profile': profile or 'default'}


def _send_local_cli(message: str, tid: str, actor: str):
    binary = _hermes_binary()
    if not binary:
        raise ValueError('Hermes CLI is not installed in the Agentic OS runtime. Configure HERMES_URL for remote API mode, or mount/install Hermes and set HERMES_CLI.')
    result = subprocess.run([binary, 'chat', '-q', message, '--source', 'agentic-os'], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=int(os.getenv('HERMES_CHAT_TIMEOUT', '180')))
    output = (result.stdout or '').strip()
    if result.returncode != 0:
        raise RuntimeError(output or f'Hermes CLI exited {result.returncode}')
    execute('INSERT INTO chat_messages(thread_id,role,content) VALUES (?,?,?)', (tid, 'assistant', output))
    execute('UPDATE chat_threads SET updated_at=CURRENT_TIMESTAMP, provider=?, model=? WHERE id=?', ('hermes-cli', 'configured-in-hermes', tid))
    record('hermes.chat', 'ok', actor=actor, target_agent='hermes-control', command_type='hermes-cli', metadata={'thread_id': tid})
    return {'thread_id': tid, 'message': output, 'provider': 'hermes-cli', 'model': 'configured-in-hermes'}


async def send_hermes_chat(message: str, thread_id: str | None = None, actor='local-admin'):
    tid = thread_id or str(uuid.uuid4())
    base_url = _hermes_base_url()
    _thread(tid, message, 'hermes-remote-api' if base_url else 'hermes-cli', os.getenv('HERMES_API_MODEL', 'hermes'))
    execute('INSERT INTO chat_messages(thread_id,role,content) VALUES (?,?,?)', (tid, 'user', message))
    try:
        if base_url:
            return await _send_remote_openai_compatible(base_url, message, tid, actor)
        return _send_local_cli(message, tid, actor)
    except Exception as exc:
        record('hermes.chat', 'failed', actor=actor, target_agent='hermes-control', command_type='hermes-remote-api' if base_url else 'hermes-cli', error=exc, metadata={'thread_id': tid, 'base_url': base_url})
        raise

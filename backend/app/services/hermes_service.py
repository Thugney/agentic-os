import os
import shutil
import subprocess
import uuid
from backend.app.db.database import execute, one
from backend.app.services.audit_service import record


def _hermes_binary() -> str | None:
    configured = os.getenv('HERMES_CLI')
    if configured and shutil.which(configured):
        return configured
    return shutil.which('hermes')


def send_hermes_chat(message: str, thread_id: str | None = None, actor='local-admin'):
    binary = _hermes_binary()
    if not binary:
        raise ValueError('Hermes CLI is not installed in the Agentic OS runtime. Mount/install Hermes or set HERMES_CLI.')
    tid = thread_id or str(uuid.uuid4())
    if not one('SELECT id FROM chat_threads WHERE id=?', (tid,)):
        execute('INSERT INTO chat_threads(id,title,agent,provider,model) VALUES (?,?,?,?,?)', (tid, message[:60] or 'Hermes chat', 'hermes-control', 'hermes-cli', 'configured-in-hermes'))
    execute('INSERT INTO chat_messages(thread_id,role,content) VALUES (?,?,?)', (tid, 'user', message))
    try:
        result = subprocess.run([binary, 'chat', '-q', message, '--source', 'agentic-os'], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=int(os.getenv('HERMES_CHAT_TIMEOUT', '180')))
        output = (result.stdout or '').strip()
        if result.returncode != 0:
            raise RuntimeError(output or f'Hermes CLI exited {result.returncode}')
        execute('INSERT INTO chat_messages(thread_id,role,content) VALUES (?,?,?)', (tid, 'assistant', output))
        execute('UPDATE chat_threads SET updated_at=CURRENT_TIMESTAMP WHERE id=?', (tid,))
        record('hermes.chat', 'ok', actor=actor, target_agent='hermes-control', command_type='hermes-cli', metadata={'thread_id': tid})
        return {'thread_id': tid, 'message': output}
    except Exception as exc:
        record('hermes.chat', 'failed', actor=actor, target_agent='hermes-control', command_type='hermes-cli', error=exc, metadata={'thread_id': tid})
        raise

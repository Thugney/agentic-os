import asyncio
import uuid
import subprocess
from pathlib import Path
from backend.app.core.settings import get_settings
from backend.app.db.database import execute, rows, one
from backend.app.services.workspace_service import require_workspace
from backend.app.services.audit_service import record

DANGEROUS = ['--yolo', ' rm -rf', ' mkfs', ' dd if=', ' shutdown', ' reboot']

def _safe_task(task: str):
    if any(x in task.lower() for x in DANGEROUS):
        raise ValueError('task contains a refused dangerous command/pattern')

def _git(path, args):
    try:
        return subprocess.check_output(['git'] + args, cwd=path, text=True, stderr=subprocess.STDOUT, timeout=20).strip()
    except Exception as e:
        return f'unavailable: {e}'

async def _run_session(session_id: str, workspace_path: str, task: str, branch: str | None, test_command: str | None):
    log_path = get_settings().logs_dir / 'codex' / f'{session_id}.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    execute('UPDATE codex_sessions SET status=? WHERE id=?', ('running', session_id))
    cmd = ['codex', 'exec', '--sandbox', 'danger-full-access', task]
    with log_path.open('a', encoding='utf-8') as log:
        log.write(f'$ {" ".join(cmd)}\n')
        try:
            if branch:
                subprocess.run(['git','checkout','-B',branch], cwd=workspace_path, stdout=log, stderr=log, timeout=30)
            proc = await asyncio.create_subprocess_exec(*cmd, cwd=workspace_path, stdout=log, stderr=log)
            code = await proc.wait()
            test_result = None
            if test_command:
                log.write(f'\n$ {test_command}\n')
                tr = subprocess.run(test_command, cwd=workspace_path, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
                test_result = tr.stdout[-8000:]
                log.write(test_result)
            diff = _git(workspace_path, ['diff','--stat'])
            status = 'completed' if code == 0 else 'failed'
            execute('UPDATE codex_sessions SET status=?, exit_code=?, ended_at=CURRENT_TIMESTAMP, git_diff_summary=?, test_result=? WHERE id=?', (status, code, diff, test_result, session_id))
            record('codex.run.complete', status, target_agent='codex-worker', workspace=workspace_path, command_type='codex', workspace_path=workspace_path, metadata={'session_id':session_id,'exit_code':code})
        except FileNotFoundError:
            msg = 'codex CLI not installed in runtime environment'
            log.write(msg + '\n')
            execute('UPDATE codex_sessions SET status=?, error=?, ended_at=CURRENT_TIMESTAMP WHERE id=?', ('failed', msg, session_id))
            record('codex.run.complete','failed',target_agent='codex-worker',workspace=workspace_path,command_type='codex',error=msg,workspace_path=workspace_path,metadata={'session_id':session_id})
        except Exception as e:
            log.write(str(e) + '\n')
            execute('UPDATE codex_sessions SET status=?, error=?, ended_at=CURRENT_TIMESTAMP WHERE id=?', ('failed', str(e), session_id))
            record('codex.run.complete','failed',target_agent='codex-worker',workspace=workspace_path,command_type='codex',error=e,workspace_path=workspace_path,metadata={'session_id':session_id})

def start_codex(task: str, workspace: str, branch: str | None=None, test_command: str | None=None, auto_commit: bool=False, background: bool=True, actor='local-admin'):
    _safe_task(task)
    w = require_workspace(workspace)
    path = w['resolved_path']
    sid = str(uuid.uuid4())
    log_path = str(get_settings().logs_dir / 'codex' / f'{sid}.log')
    command = 'codex exec --sandbox danger-full-access <task>'
    execute('INSERT INTO codex_sessions(id,task,workspace,branch,test_command,auto_commit,status,command,log_path) VALUES (?,?,?,?,?,?,?,?,?)', (sid,task,workspace,branch,test_command,int(auto_commit),'queued',command,log_path))
    record('codex.run.start','queued',actor=actor,target_agent='codex-worker',workspace=workspace,command_type='codex',workspace_path=path,metadata={'session_id':sid,'auto_commit':auto_commit})
    asyncio.create_task(_run_session(sid,path,task,branch,test_command))
    return one('SELECT * FROM codex_sessions WHERE id=?',(sid,))

def sessions(): return rows('SELECT * FROM codex_sessions ORDER BY started_at DESC')

def get_session(sid):
    s = one('SELECT * FROM codex_sessions WHERE id=?',(sid,))
    if s and s.get('log_path') and Path(s['log_path']).exists():
        s['log'] = Path(s['log_path']).read_text(encoding='utf-8', errors='replace')[-20000:]
    return s

def cancel(sid):
    execute('UPDATE codex_sessions SET status=?, ended_at=CURRENT_TIMESTAMP, error=? WHERE id=? AND status IN (?,?,?)', ('cancelled','cancel requested',sid,'queued','running','starting'))
    record('codex.cancel','ok',target_agent='codex-worker',command_type='codex',metadata={'session_id':sid})
    return get_session(sid)

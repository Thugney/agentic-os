import asyncio
import json
import os
import signal
import subprocess
import uuid
from pathlib import Path
from backend.app.core.settings import get_settings
from backend.app.db.database import execute, rows, one
from backend.app.services.workspace_service import require_workspace, validate_allowed_command
from backend.app.services.audit_service import record

DANGEROUS = ['--yolo', ' rm -rf', ' mkfs', ' dd if=', ' shutdown', ' reboot']
RUNNING: dict[str, asyncio.subprocess.Process] = {}

def _safe_task(task: str):
    if any(x in task.lower() for x in DANGEROUS):
        raise ValueError('task contains a refused dangerous command/pattern')

def _git(path, args, timeout=20):
    try:
        return subprocess.check_output(['git'] + args, cwd=path, text=True, stderr=subprocess.STDOUT, timeout=timeout).strip()
    except Exception as e:
        return f'unavailable: {e}'

def _artifacts(path: str):
    status = _git(path, ['status', '--short'])
    changed=[]
    for line in status.splitlines():
        if len(line) > 3:
            changed.append(line[3:])
    return changed[:100]

async def _stream(pipe, log):
    while True:
        line = await pipe.readline()
        if not line:
            break
        log.write(line.decode(errors='replace'))
        log.flush()

async def _run_session(session_id: str, workspace_name: str, workspace_path: str, task: str, branch: str | None, test_command: str | None):
    log_path = get_settings().logs_dir / 'codex' / f'{session_id}.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    execute('UPDATE codex_sessions SET status=? WHERE id=?', ('running', session_id))
    cmd = ['codex', 'exec', '--sandbox', 'danger-full-access', task]
    with log_path.open('a', encoding='utf-8') as log:
        log.write(f'$ {" ".join(cmd)}\n')
        log.flush()
        try:
            if branch:
                subprocess.run(['git','checkout','-B',branch], cwd=workspace_path, stdout=log, stderr=log, timeout=30)
            proc = await asyncio.create_subprocess_exec(*cmd, cwd=workspace_path, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, start_new_session=True)
            RUNNING[session_id] = proc
            execute('INSERT OR REPLACE INTO agent_processes(id,kind,session_id,pid,status,metadata) VALUES (?,?,?,?,?,?)', (str(uuid.uuid4()), 'codex', session_id, proc.pid, 'running', json.dumps({'workspace':workspace_name})))
            await _stream(proc.stdout, log)  # type: ignore[arg-type]
            code = await proc.wait()
            RUNNING.pop(session_id, None)
            test_result = None
            if test_command:
                log.write(f'\n$ {test_command}\n')
                tr = subprocess.run(test_command, cwd=workspace_path, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
                test_result = tr.stdout[-12000:]
                log.write(test_result)
                if tr.returncode != 0 and code == 0:
                    code = tr.returncode
            diff = _git(workspace_path, ['diff','--stat'])
            artifacts = _artifacts(workspace_path)
            status = 'completed' if code == 0 else 'failed'
            execute('UPDATE codex_sessions SET status=?, exit_code=?, ended_at=CURRENT_TIMESTAMP, git_diff_summary=?, test_result=?, artifacts=? WHERE id=?', (status, code, diff, test_result, json.dumps(artifacts), session_id))
            execute('UPDATE agent_processes SET status=?, ended_at=CURRENT_TIMESTAMP WHERE session_id=?', (status, session_id))
            record('codex.run.complete', status, target_agent='codex-worker', workspace=workspace_name, command_type='codex', workspace_path=workspace_path, metadata={'session_id':session_id,'exit_code':code,'artifacts':artifacts})
        except FileNotFoundError:
            msg = 'codex CLI not installed in runtime environment'
            log.write(msg + '\n')
            execute('UPDATE codex_sessions SET status=?, error=?, ended_at=CURRENT_TIMESTAMP WHERE id=?', ('failed', msg, session_id))
            record('codex.run.complete','failed',target_agent='codex-worker',workspace=workspace_name,command_type='codex',error=msg,workspace_path=workspace_path,metadata={'session_id':session_id})
        except Exception as e:
            RUNNING.pop(session_id, None)
            log.write(str(e) + '\n')
            execute('UPDATE codex_sessions SET status=?, error=?, ended_at=CURRENT_TIMESTAMP WHERE id=?', ('failed', str(e), session_id))
            execute('UPDATE agent_processes SET status=?, ended_at=CURRENT_TIMESTAMP WHERE session_id=?', ('failed', session_id))
            record('codex.run.complete','failed',target_agent='codex-worker',workspace=workspace_name,command_type='codex',error=e,workspace_path=workspace_path,metadata={'session_id':session_id})

def start_codex(task: str, workspace: str, branch: str | None=None, test_command: str | None=None, auto_commit: bool=False, background: bool=True, actor='local-admin'):
    _safe_task(task)
    validate_allowed_command(workspace, test_command)
    w = require_workspace(workspace)
    path = w['resolved_path']
    sid = str(uuid.uuid4())
    log_path = str(get_settings().logs_dir / 'codex' / f'{sid}.log')
    command = 'codex exec --sandbox danger-full-access <task>'
    execute('INSERT INTO codex_sessions(id,task,workspace,branch,test_command,auto_commit,status,command,log_path) VALUES (?,?,?,?,?,?,?,?,?)', (sid,task,workspace,branch,test_command,int(auto_commit),'queued',command,log_path))
    record('codex.run.start','queued',actor=actor,target_agent='codex-worker',workspace=workspace,command_type='codex',workspace_path=path,metadata={'session_id':sid,'auto_commit':auto_commit})
    asyncio.create_task(_run_session(sid, workspace, path, task, branch, test_command))
    return get_session(sid)

def sessions(): return rows('SELECT * FROM codex_sessions ORDER BY started_at DESC')

def get_session(sid):
    s = one('SELECT * FROM codex_sessions WHERE id=?',(sid,))
    if s and s.get('log_path') and Path(s['log_path']).exists():
        s['log'] = Path(s['log_path']).read_text(encoding='utf-8', errors='replace')[-50000:]
    return s

def cancel(sid):
    proc = RUNNING.get(sid)
    if proc and proc.returncode is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            proc.terminate()
    execute('UPDATE codex_sessions SET status=?, ended_at=CURRENT_TIMESTAMP, error=? WHERE id=? AND status IN (?,?,?)', ('cancelled','cancel requested',sid,'queued','running','starting'))
    execute('UPDATE agent_processes SET status=?, ended_at=CURRENT_TIMESTAMP WHERE session_id=?', ('cancelled', sid))
    record('codex.cancel','ok',target_agent='codex-worker',command_type='codex',metadata={'session_id':sid})
    return get_session(sid)

def confirm_commit(sid: str, message: str, actor='local-admin'):
    s = get_session(sid)
    if not s: raise ValueError('session not found')
    w = require_workspace(s['workspace']); path = w['resolved_path']
    if s['status'] not in ('completed','failed'):
        raise ValueError('session must finish before commit')
    subprocess.check_call(['git','add','-A'], cwd=path)
    subprocess.check_call(['git','commit','-m', message], cwd=path)
    commit = _git(path, ['rev-parse','--short','HEAD'])
    record('codex.commit.confirmed','ok',actor=actor,target_agent='codex-worker',workspace=s['workspace'],command_type='git',workspace_path=path,metadata={'session_id':sid,'commit':commit})
    return {'session_id': sid, 'commit': commit, 'status': _git(path, ['status','--short'])}

def confirm_push(sid: str, remote='origin', branch: str | None=None, actor='local-admin'):
    s = get_session(sid)
    if not s: raise ValueError('session not found')
    w = require_workspace(s['workspace']); path = w['resolved_path']
    target_branch = branch or _git(path, ['branch','--show-current'])
    subprocess.check_call(['git','push','-u', remote, target_branch], cwd=path)
    record('codex.push.confirmed','ok',actor=actor,target_agent='codex-worker',workspace=s['workspace'],command_type='git',workspace_path=path,metadata={'session_id':sid,'remote':remote,'branch':target_branch})
    return {'session_id': sid, 'remote': remote, 'branch': target_branch}

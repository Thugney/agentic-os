import json
import subprocess
from backend.app.db.database import execute, rows
from backend.app.core.security import redact

def git_meta(workspace_path: str | None):
    if not workspace_path: return None, None
    try:
        branch = subprocess.check_output(['git','branch','--show-current'], cwd=workspace_path, text=True, timeout=3).strip()
        commit = subprocess.check_output(['git','rev-parse','--short','HEAD'], cwd=workspace_path, text=True, timeout=3).strip()
        return branch, commit
    except Exception:
        return None, None

def record(action: str, status: str='ok', actor: str='local-admin', target_agent=None, workspace=None, command_type=None, error=None, metadata=None, workspace_path=None):
    branch, commit = git_meta(workspace_path)
    execute('INSERT INTO audit_log(actor,action,target_agent,workspace,command_type,status,error,git_branch,git_commit,metadata) VALUES (?,?,?,?,?,?,?,?,?,?)',
            (actor, action, target_agent, workspace, command_type, status, str(error)[:1000] if error else None, branch, commit, json.dumps(redact(metadata or {}))))

def list_audit(limit=250, agent=None, workspace=None, status=None):
    sql='SELECT * FROM audit_log WHERE 1=1'; params=[]
    if agent: sql+=' AND target_agent=?'; params.append(agent)
    if workspace: sql+=' AND workspace=?'; params.append(workspace)
    if status: sql+=' AND status=?'; params.append(status)
    sql+=' ORDER BY id DESC LIMIT ?'; params.append(limit)
    return rows(sql, params)

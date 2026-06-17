from pathlib import Path
import subprocess
from backend.app.services.config_service import workspaces

def registered_workspace(name: str):
    for w in workspaces():
        if w.get('name') == name:
            p = Path(w.get('path','')).expanduser().resolve()
            w['resolved_path'] = str(p)
            return w
    return None

def require_workspace(name: str):
    w = registered_workspace(name)
    if not w:
        raise ValueError('workspace is not registered')
    p = Path(w['resolved_path'])
    if not p.exists() or not p.is_dir():
        raise ValueError('workspace path does not exist')
    return w

def git_info(path: str):
    def run(args):
        try: return subprocess.check_output(args, cwd=path, text=True, stderr=subprocess.STDOUT, timeout=5).strip()
        except Exception as e: return f'unavailable: {e}'
    return {'status': run(['git','status','--short']), 'branch': run(['git','branch','--show-current']), 'latest_commit': run(['git','log','-1','--oneline'])}

def workspace_statuses():
    out=[]
    for w in workspaces():
        p = Path(w.get('path','')).expanduser()
        item = dict(w); item['exists']=p.exists(); item['git']=git_info(str(p)) if p.exists() else None
        out.append(item)
    return out

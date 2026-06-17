from backend.app.db.database import connect

MIGRATIONS = [
("001_initial", """
CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP, actor TEXT, action TEXT NOT NULL, target_agent TEXT, workspace TEXT, command_type TEXT, status TEXT NOT NULL, error TEXT, git_branch TEXT, git_commit TEXT, metadata TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS chat_threads (id TEXT PRIMARY KEY, title TEXT NOT NULL, agent TEXT, provider TEXT, model TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(thread_id) REFERENCES chat_threads(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS codex_sessions (id TEXT PRIMARY KEY, task TEXT NOT NULL, workspace TEXT NOT NULL, branch TEXT, test_command TEXT, auto_commit INTEGER DEFAULT 0, status TEXT NOT NULL, command TEXT, log_path TEXT, exit_code INTEGER, started_at TEXT DEFAULT CURRENT_TIMESTAMP, ended_at TEXT, git_diff_summary TEXT, test_result TEXT, artifacts TEXT DEFAULT '[]', error TEXT);
CREATE TABLE IF NOT EXISTS kanban_tasks (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '', status TEXT DEFAULT 'Backlog', agent_session TEXT, workspace TEXT, git_branch TEXT, artifact TEXT, chat_thread TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS memory_records (id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL, scope TEXT NOT NULL, tags TEXT DEFAULT '[]', source_session TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
"""),
("002_control_plane", """
CREATE TABLE IF NOT EXISTS agent_processes (id TEXT PRIMARY KEY, kind TEXT NOT NULL, session_id TEXT, pid INTEGER, status TEXT NOT NULL, started_at TEXT DEFAULT CURRENT_TIMESTAMP, ended_at TEXT, metadata TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS goal_runs (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '', status TEXT DEFAULT 'Backlog', workspace TEXT, agent TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS mcp_registry (id TEXT PRIMARY KEY, name TEXT NOT NULL, endpoint TEXT, enabled INTEGER DEFAULT 0, status TEXT DEFAULT 'placeholder', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
""")]

def run_migrations():
    with connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations").fetchall()}
        for version, sql in MIGRATIONS:
            if version not in done:
                conn.executescript(sql)
                conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))
        conn.commit()

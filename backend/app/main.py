from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.core.logging import configure_logging
from backend.app.core.security import AdminTokenMiddleware
from backend.app.db.migrations import run_migrations
from backend.app.api.work_order_routes import router as work_order_router
from backend.app.api.routes import router

configure_logging()
app=FastAPI(title='Agentic OS', version='0.1.0')
app.add_middleware(AdminTokenMiddleware)
app.include_router(work_order_router)
app.include_router(router)

@app.on_event('startup')
def startup():
    run_migrations()

static_dir=Path(__file__).resolve().parents[1] / 'static'
if static_dir.exists():
    app.mount('/assets', StaticFiles(directory=static_dir/'assets'), name='assets')
    @app.get('/{full_path:path}')
    def spa(full_path: str):
        target=static_dir / full_path
        if full_path and target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(static_dir/'index.html')

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api import admin, auth, caseta, supervisor
from app.core.config import get_settings
from app.core.database import Base, engine


settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(caseta.router, prefix=settings.api_prefix)
app.include_router(supervisor.router, prefix=f"{settings.api_prefix}/supervisor")
app.include_router(admin.router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}


# --- Servir el frontend compilado (SPA) en el mismo puerto ---
# El frontend de Vite se compila en frontend/dist. Si existe, se sirve
# de forma estática y todas las rutas no-API devuelven index.html para
# que funcione el enrutamiento del lado del cliente (React Router).
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    index_file = FRONTEND_DIST / "index.html"

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        # No interceptar rutas de API ni health
        if full_path.startswith(("api/", "health")):
            raise HTTPException(status_code=404, detail="Not Found")
        # Servir archivos estáticos reales (favicon, imágenes, etc.)
        requested = FRONTEND_DIST / full_path
        if full_path and requested.is_file():
            return FileResponse(requested)
        # Cualquier otra ruta -> index.html (SPA)
        return FileResponse(index_file)

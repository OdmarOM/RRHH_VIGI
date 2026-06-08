from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

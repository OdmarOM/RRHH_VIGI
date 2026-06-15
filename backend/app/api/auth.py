from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models import UsuarioSistema
from app.schemas import LoginRequest, Token
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        logger.info(f"Login attempt for user: {payload.username}")
        user = db.scalar(
            select(UsuarioSistema)
            .options(joinedload(UsuarioSistema.rol))
            .where(UsuarioSistema.username == payload.username, UsuarioSistema.activo.is_(True))
        )
        logger.info(f"User found: {user is not None}")
        if user:
            logger.info(f"User role: {user.rol.nombre if user.rol else 'No role'}")
        if not user or not verify_password(payload.password, user.password_hash):
            logger.warning("Invalid credentials")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
        token = Token(access_token=create_access_token(user.username, user.rol.nombre), rol=user.rol.nombre)
        logger.info(f"Login successful for user: {payload.username}")
        return token
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise

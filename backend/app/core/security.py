from datetime import timedelta
from jose import jwt
from app.core.config import get_settings
from app.core.time import utc_now
import hashlib
import secrets


settings = get_settings()


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"sha256${salt}${hashed}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        # Handle old passlib hashes
        if password_hash.startswith("$pbkdf2-sha256$") or password_hash.startswith("$5$rounds=") or password_hash.startswith("pbkdf2_sha256$"):
            # For old hashes, temporarily use passlib
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["pbkdf2_sha256", "sha256_crypt"], deprecated="auto")
            try:
                return pwd_context.verify(password, password_hash)
            except:
                return False
        
        # Handle new simple hashes
        if password_hash.startswith("sha256$"):
            parts = password_hash.split("$")
            if len(parts) == 3:
                salt = parts[1]
                stored_hash = parts[2]
                computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                return secrets.compare_digest(computed_hash, stored_hash)
        
        return False
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False


def create_access_token(subject: str, role: str) -> str:
    expires = utc_now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "role": role, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except:
        return None

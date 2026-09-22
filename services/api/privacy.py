from datetime import datetime, timedelta, timezone
from pathlib import Path

class EncryptedMediaStore:
    """Fernet-backed storage helper. Production deployments must supply key management."""
    def __init__(self, key: bytes):
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:
            raise RuntimeError('Install cryptography and provide a managed Fernet key for encrypted media') from exc
        self._fernet=Fernet(key)
    def encrypt_bytes(self, content: bytes) -> bytes: return self._fernet.encrypt(content)
    def decrypt_bytes(self, content: bytes) -> bytes: return self._fernet.decrypt(content)

def delete_expired_files(directory: str | Path, retention_days: int, now: datetime | None = None) -> list[str]:
    if retention_days < 0: raise ValueError('retention_days must be non-negative')
    cutoff=(now or datetime.now(timezone.utc))-timedelta(days=retention_days); deleted=[]
    for path in Path(directory).glob('*'):
        if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < cutoff:
            path.unlink(); deleted.append(str(path))
    return deleted

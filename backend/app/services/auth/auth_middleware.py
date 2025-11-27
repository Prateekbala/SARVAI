from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.services.auth.auth_service import auth_service
from app.database import get_db
from app.services.storage.storage_service import storage_service

security = HTTPBearer(auto_error=False)

async def get_current_user_namespace(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    namespace: str = payload.get("sub")
    if not namespace:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = await storage_service.get_user_by_namespace(db, namespace)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return namespace
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid namespace",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user_namespace(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[str]:
    if not credentials:
        return None
    
    try:
        return await get_current_user_namespace(credentials, db)
    except HTTPException:
        return None

# Backward compatibility aliases
get_current_user_id = get_current_user_namespace
get_optional_user_id = get_optional_user_namespace

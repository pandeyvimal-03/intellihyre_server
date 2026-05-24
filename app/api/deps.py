from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import TokenData

# reusable_oauth2 is no longer needed as we're reading from cookies directly for get_current_user
# reusable_oauth2 = OAuth2PasswordBearer(
#     tokenUrl=f"{settings.API_V1_STR}/auth/login"
# )

async def get_current_user(
    request: Request, # Get the request object to access cookies
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token") # Read token from cookie
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        token_data = TokenData(email=email)
    except (JWTError, Exception) as e:
        print(f"JWT Validation Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    result = await db.execute(select(User).where(User.email == token_data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return user

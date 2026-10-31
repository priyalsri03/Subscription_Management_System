"""
Dependency injection helpers - Person 2
Provides dependency functions that return User objects.
"""
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_db
from backend.app.core.interfaces import ServiceRegistry, User


async def get_current_user(
    token: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user.

    This is a TEMPORARY mock implementation.
    Person 1's auth.py will provide: core/security.py: get_current_user() -> User
    """
    auth = ServiceRegistry.auth
    if auth is None:
        from backend.app.core.interfaces import initialize_mocks
        initialize_mocks()
        auth = ServiceRegistry.auth

    user = auth.get_current_user("", db)
    return user


def require_role(*roles: str):
    """Dependency that checks if user has required role."""
    async def _check_role(
        current_user: User = Depends(get_current_user),
    ):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {', '.join(roles)}",
            )
        return current_user

    return _check_role
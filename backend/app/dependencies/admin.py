"""
Admin-only dependency. Built on top of get_current_user, then enforces
is_superuser. Returns the User so handlers can use it.
"""

from __future__ import annotations

from fastapi import Depends

from backend.app.core.errors import ForbiddenError
from backend.app.dependencies.auth import get_current_user
from backend.app.models.user import User


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_superuser:
        raise ForbiddenError(
            "Admin access required.",
            code="admin_required",
        )
    return user

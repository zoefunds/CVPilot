"""
Versioned API router aggregator.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.routes import admin, applications, auth, evaluations, wallet

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(wallet.router)
api_router.include_router(applications.router)
api_router.include_router(evaluations.router)
api_router.include_router(admin.router)

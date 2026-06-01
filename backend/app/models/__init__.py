"""
Import all models here so Alembic autogenerate detects them.
"""

from backend.app.models.application import Application, FileAsset  # noqa: F401
from backend.app.models.audit_log import AuditLog  # noqa: F401
from backend.app.models.evaluation import Evaluation  # noqa: F401
from backend.app.models.password_reset_token import PasswordResetToken  # noqa: F401
from backend.app.models.user import User  # noqa: F401

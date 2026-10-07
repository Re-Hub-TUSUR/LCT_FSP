"""Admin panel endpoints, mounted under `/admin`. Every one of them is for admins only:
the guard sits on the router itself, not only on the handlers."""

from fastapi import APIRouter, Depends

from app.admin.routes import analytics, bank, banlist, employers, settings, verification
from app.dependencies.auth import require_roles
from app.models import UserRole

panel_router = APIRouter(dependencies=[Depends(require_roles(UserRole.ADMIN))])
for module in (bank, analytics, employers, banlist, settings, verification):
    panel_router.include_router(module.router)

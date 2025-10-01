"""Application configuration - root APIRouter.

Defines all FastAPI application endpoints.

Resources:
    1. https://fastapi.tiangolo.com/tutorial/bigger-applications

"""

from fastapi import APIRouter

from app.controllers import auth, payment, template, team
from app.monitoring import health
from app.controllers.v1 import llm, video

root_api_router = APIRouter()
# v1
root_api_router.include_router(video.router)
root_api_router.include_router(llm.router)

# auth
root_api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# payment
root_api_router.include_router(payment.router, prefix="/payment", tags=["Payment"])

# templates
root_api_router.include_router(template.router, prefix="/templates", tags=["Templates"])

# teams
root_api_router.include_router(team.router, prefix="/teams", tags=["Teams"])

# monitoring
root_api_router.include_router(health.router)

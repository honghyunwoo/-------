"""Application configuration - root APIRouter.

Defines all FastAPI application endpoints.

Resources:
    1. https://fastapi.tiangolo.com/tutorial/bigger-applications

"""

from fastapi import APIRouter

from app.controllers import auth, payment, template, team
from app.monitoring import health, performance
from app.controllers.v1 import llm, video, credits, history

root_api_router = APIRouter()
# v1
root_api_router.include_router(video.router)
root_api_router.include_router(llm.router)

# auth
root_api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# payment
root_api_router.include_router(payment.router, prefix="/payment", tags=["Payment"])

# credits
root_api_router.include_router(credits.router, prefix="/credits", tags=["Credits"])

# history
root_api_router.include_router(history.router, prefix="/history", tags=["History"])

# templates
root_api_router.include_router(template.router, prefix="/templates", tags=["Templates"])

# teams
root_api_router.include_router(team.router, prefix="/teams", tags=["Teams"])

# monitoring
root_api_router.include_router(health.router)
root_api_router.include_router(performance.router)

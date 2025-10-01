"""
모델 정의 모듈
데이터베이스 모델들을 중앙에서 관리
"""

from app.database.connection import Base

# 데이터베이스 모델 임포트 (순환 참조 방지)
from app.models.user import User
from app.models.subscription import Subscription, Payment
from app.models.video_history import VideoHistory
from app.models.template import Template
from app.models.branding import Branding
from app.models.team import Team, team_member_association

# 외부로 export
__all__ = [
    'Base',
    'User',
    'Subscription',
    'Payment',
    'VideoHistory',
    'Template',
    'Branding',
    'Team',
    'team_member_association',
]
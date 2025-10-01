
# 모든 SQLAlchemy 모델을 중앙에서 관리

from app.database.connection import engine, Base
# 모든 모델 임포트 (테이블 생성을 위해)
from app.models import (
    User,
    Subscription,
    Payment,
    VideoHistory,
    Template,
    Branding,
    Team,
    team_member_association
)

def create_all_tables():
    """데이터베이스에 모든 테이블 생성"""
    # Base를 상속한 모든 모델의 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("[OK] All tables created successfully")


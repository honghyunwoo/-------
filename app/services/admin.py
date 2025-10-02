"""
Service for providing administrative statistics.

This module contains functions to query the database and aggregate data
for the admin dashboard, such as user counts, video counts, and daily activity.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Dict, Any

from app.models.user import User
from app.models.video_history import VideoHistory


def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """
    Retrieve key statistics for the admin dashboard.

    This function queries the database to get total user and video counts,
    daily signups and video creations for the last 30 days, and the
    distribution of users across different subscription plans.

    Args:
        db (Session): The database session.

    Returns:
        Dict[str, Any]: A dictionary containing various statistics for the dashboard.
    """
    total_users = db.query(User).count()
    total_videos = db.query(VideoHistory).count()

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    daily_signups = (
        db.query(func.date(User.created_at), func.count(User.id))
        .filter(User.created_at >= thirty_days_ago)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )

    daily_videos = (
        db.query(func.date(VideoHistory.created_at), func.count(VideoHistory.id))
        .filter(VideoHistory.created_at >= thirty_days_ago)
        .group_by(func.date(VideoHistory.created_at))
        .order_by(func.date(VideoHistory.created_at))
        .all()
    )

    plan_distribution = (
        db.query(User.subscription_plan, func.count(User.id))
        .group_by(User.subscription_plan)
        .all()
    )

    stats = {
        "total_users": total_users,
        "total_videos_generated": total_videos,
        "daily_signups": [{"date": str(date), "count": count} for date, count in daily_signups],
        "daily_videos": [{"date": str(date), "count": count} for date, count in daily_videos],
        "plan_distribution": {plan: count for plan, count in plan_distribution},
    }

    return stats
"""
구독 자동 갱신 스케줄러

APScheduler를 사용하여 주기적으로 자동 갱신 작업을 실행합니다:
- 매일 새벽 2시: 자동 갱신 처리
- 매일 오전 9시: 만료 임박 알림 발송
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from loguru import logger

from app.database.connection import SessionLocal
from app.services import subscription


# 스케줄러 인스턴스
scheduler = BackgroundScheduler()


def process_subscription_renewals():
    """
    구독 자동 갱신 작업 실행
    매일 새벽 2시에 실행됩니다.
    """
    logger.info("⏰ Starting scheduled subscription renewal process")
    db = SessionLocal()

    try:
        results = subscription.process_all_renewals(db)

        logger.info(f"📊 Renewal completed: "
                   f"Total={results['total']}, "
                   f"Success={results['success']}, "
                   f"Failed={results['failed']}")

        # TODO: 관리자에게 결과 이메일 발송
        # send_admin_notification(results)

    except Exception as e:
        logger.error(f"❌ Renewal process failed: {e}", exc_info=True)

    finally:
        db.close()


def send_expiration_reminders():
    """
    만료 임박 알림 발송
    매일 오전 9시에 실행됩니다.
    """
    logger.info("⏰ Starting scheduled expiration reminder process")
    db = SessionLocal()

    try:
        # 3일 이내 만료 예정 구독 조회
        expiring_subscriptions = subscription.get_expiring_subscriptions(db, days_before=3)

        logger.info(f"📧 Found {len(expiring_subscriptions)} expiring subscriptions")

        for sub in expiring_subscriptions:
            try:
                user = sub.user
                days_left = (sub.end_date - datetime.now()).days

                logger.info(f"📧 Sending reminder to {user.email}: {days_left} days left")

                # TODO: 이메일 발송
                # send_expiration_email(
                #     email=user.email,
                #     plan=sub.plan,
                #     end_date=sub.end_date,
                #     days_left=days_left,
                #     auto_renew=sub.auto_renew
                # )

            except Exception as e:
                logger.error(f"❌ Failed to send reminder for subscription {sub.id}: {e}")

    except Exception as e:
        logger.error(f"❌ Reminder process failed: {e}", exc_info=True)

    finally:
        db.close()


def start_scheduler():
    """
    스케줄러 시작

    작업 스케줄:
    - 매일 새벽 2시: 자동 갱신 처리
    - 매일 오전 9시: 만료 임박 알림 발송
    """
    # 자동 갱신 작업 (매일 새벽 2시)
    scheduler.add_job(
        process_subscription_renewals,
        trigger=CronTrigger(hour=2, minute=0),  # 매일 02:00
        id="subscription_renewal",
        name="Subscription Auto-Renewal",
        replace_existing=True
    )

    # 만료 임박 알림 (매일 오전 9시)
    scheduler.add_job(
        send_expiration_reminders,
        trigger=CronTrigger(hour=9, minute=0),  # 매일 09:00
        id="expiration_reminder",
        name="Expiration Reminder",
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ Scheduler started successfully")
    logger.info("📅 Scheduled jobs:")
    logger.info("  - Subscription renewal: Daily at 02:00")
    logger.info("  - Expiration reminder: Daily at 09:00")


def stop_scheduler():
    """스케줄러 중지"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("⏹️ Scheduler stopped")


def get_scheduled_jobs():
    """
    등록된 작업 목록 조회

    Returns:
        list: 작업 정보 목록
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return jobs

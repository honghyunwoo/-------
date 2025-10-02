"""
이메일 서비스: 인증 메일, 비밀번호 재설정 등
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timedelta
import secrets
from jose import jwt
from loguru import logger

from app.config import config
from app.services.auth import SECRET_KEY, ALGORITHM

# 이메일 설정
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "noreply@owl-studio.kr")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@owl-studio.kr")
FROM_NAME = "올빼미 AI 영상 스튜디오"

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """이메일 발송"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to_email

        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)

        # Gmail SMTP 설정
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        if SMTP_PASSWORD:  # 비밀번호가 설정된 경우에만 로그인
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.exception(f"An unexpected error occurred while sending email to {to_email}")
        return False

def generate_verification_token(email: str) -> str:
    """이메일 인증 토큰 생성"""
    expires_delta = timedelta(hours=24)
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": email, "exp": expire, "type": "email_verification"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """토큰 검증 및 이메일 반환"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "email_verification":
            return None
        email = payload.get("sub")
        return email
    except jwt.JWTError:
        return None

def send_verification_email(email: str, token: str) -> bool:
    """회원가입 인증 메일 발송"""
    app_base_url = config.app.get("app_base_url", "http://localhost:8080")
    verification_link = f"{app_base_url}/api/v1/auth/verify-email?token={token}"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Noto Sans KR', sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #2a5298; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🦉 올빼미 AI 영상 스튜디오</h1>
                <p>이메일 인증</p>
            </div>
            <div class="content">
                <h2>안녕하세요!</h2>
                <p>올빼미 AI 영상 스튜디오에 가입해 주셔서 감사합니다.</p>
                <p>아래 버튼을 클릭하여 이메일 인증을 완료해주세요:</p>
                <center>
                    <a href="{verification_link}" class="button">이메일 인증하기</a>
                </center>
                <p>또는 다음 링크를 브라우저에 직접 입력하세요:</p>
                <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 5px;">
                    {verification_link}
                </p>
                <p><small>이 링크는 24시간 동안 유효합니다.</small></p>
            </div>
            <div class="footer">
                <p>© 2024 올빼미 AI 영상 스튜디오. All rights reserved.</p>
                <p>본 메일은 발신 전용입니다.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(email, "🦉 올빼미 AI 영상 스튜디오 - 이메일 인증", html_body)

def send_password_reset_email(email: str, token: str) -> bool:
    """비밀번호 재설정 메일 발송"""
    app_base_url = config.app.get("app_base_url", "http://localhost:8080").replace("8080", "8501") # Assume UI is on 8501
    reset_link = f"{app_base_url}/reset-password?token={token}"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Noto Sans KR', sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #e74c3c; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🦉 올빼미 AI 영상 스튜디오</h1>
                <p>비밀번호 재설정</p>
            </div>
            <div class="content">
                <h2>비밀번호 재설정 요청</h2>
                <p>비밀번호 재설정을 요청하셨습니다.</p>
                <p>아래 버튼을 클릭하여 새로운 비밀번호를 설정해주세요:</p>
                <center>
                    <a href="{reset_link}" class="button">비밀번호 재설정</a>
                </center>
                <p>만약 비밀번호 재설정을 요청하지 않으셨다면 이 메일을 무시하세요.</p>
                <p><small>이 링크는 1시간 동안 유효합니다.</small></p>
            </div>
            <div class="footer">
                <p>© 2024 올빼미 AI 영상 스튜디오. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(email, "🦉 올빼미 AI 영상 스튜디오 - 비밀번호 재설정", html_body)
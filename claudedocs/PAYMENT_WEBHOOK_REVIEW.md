# 결제 웹훅 구현 상세 검수 보고서

**검수일**: 2025-10-03
**검수자**: Claude (Chief Developer)
**대상**: 토스페이먼츠 웹훅 구현 (ERR-010)

---

## 📋 검수 체크리스트

### ✅ 통과한 항목

1. **보안**
   - ✅ HMAC SHA256 서명 검증
   - ✅ Constant-time 비교
   - ✅ 환경 변수로 API 키 관리

2. **멱등성**
   - ✅ payment_gateway_charge_id로 중복 확인
   - ✅ "Already processed" 응답

3. **에러 처리**
   - ✅ try-except 블록
   - ✅ db.rollback()
   - ✅ 상세 로깅

4. **테스트**
   - ✅ 5개 테스트 케이스 통과
   - ✅ 서명 검증 테스트
   - ✅ 멱등성 테스트

---

## ⚠️ 발견된 문제점

### 1. CRITICAL: CANCEL_STATUS_CHANGED 로직 오류

**위치**: `app/services/payment.py:291-325`

**문제**:
```python
# Line 305-307: payment_key로 조회하고 있음
payment = db.query(Payment).filter(
    Payment.payment_gateway_charge_id == payment_key  # ❌ 잘못됨!
).first()
```

**원인**:
- `payment_key`는 토스페이먼츠의 결제 고유 ID
- `payment_gateway_charge_id`는 우리의 `order_id` 저장
- **매칭 불일치!**

**영향**:
- 🔴 결제 취소 시 기존 결제를 찾지 못함
- 🔴 구독이 비활성화되지 않음
- 🔴 사용자가 환불받았는데 서비스는 계속 이용 가능

**해결 방법**:
```python
# 옵션 1: payment_key를 별도 컬럼에 저장
payment = db.query(Payment).filter(
    Payment.payment_key == payment_key
).first()

# 옵션 2: order_id로 조회 (CANCEL_STATUS_CHANGED에 orderId 포함 시)
order_id = data.get("orderId")
payment = db.query(Payment).filter(
    Payment.payment_gateway_charge_id == order_id
).first()
```

---

### 2. HIGH: Payment 모델에 payment_key 컬럼 누락

**위치**: `app/models/subscription.py:19-32`

**문제**:
- `Payment` 모델에 `payment_key` 컬럼이 없음
- `payment_gateway_charge_id`만 있음 (order_id 저장용)
- 취소/환불 추적 불가

**현재 모델**:
```python
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    amount = Column(Float, nullable=False)
    currency = Column(String, default="KRW")
    status = Column(String, nullable=False)
    payment_gateway_charge_id = Column(String, unique=True)  # order_id만 저장
    created_at = Column(DateTime, default=func.now())
```

**필요한 개선**:
```python
class Payment(Base):
    __tablename__ = "payments"

    # ... (기존 컬럼)
    payment_gateway_charge_id = Column(String, unique=True)  # order_id
    payment_key = Column(String, unique=True)  # 토스페이먼츠 결제 고유 ID (추가 필요!)
    created_at = Column(DateTime, default=func.now())
```

---

### 3. MEDIUM: _update_user_subscription 중복 호출 위험

**위치**: `app/services/payment.py:219, 406`

**문제**:
1. **Line 219**: `_handle_payment_status_changed()`에서 호출
2. **Line 406**: `retry_failed_payment()`에서 직접 호출
3. 멱등성 체크가 `_handle_payment_status_changed()`에만 있음
4. `retry_failed_payment()`는 멱등성 체크 없이 직접 `_update_user_subscription()` 호출

**시나리오**:
```
1. 웹훅 수신 → _handle_payment_status_changed() → 구독 생성 ✅
2. 관리자가 retry_failed_payment() 수동 호출
3. 멱등성 체크 없이 → _update_user_subscription() 호출
4. 구독 중복 생성 가능성 ❌
```

**해결 방법**:
```python
def retry_failed_payment(db: Session, payment_id: int, max_retries: int = 3) -> dict:
    # ...
    if payment_data.get("status") == "DONE":
        # 멱등성 체크 추가!
        if payment_record.status == "succeeded":
            logger.info(f"✅ Payment already succeeded: {payment_id}")
            return {"status": "success", "message": "Already succeeded"}

        # 구독 업데이트
        user = db.query(User).filter(User.id == payment_record.user_id).first()
        parts = order_id.split("_")
        plan = parts[3]

        _update_user_subscription(db, user, plan, payment_record.amount, order_id)
```

---

### 4. MEDIUM: 부분 취소 (PARTIAL_CANCELED) 미처리

**위치**: `app/services/payment.py:168-251`

**문제**:
- `PARTIAL_CANCELED` 상태가 docstring에 명시되어 있음 (Line 179)
- 하지만 실제 처리 로직 없음
- Line 224-231에서 `CANCELED`만 처리

**시나리오**:
- 사용자가 99,000원 결제
- 부분 환불 30,000원 요청
- 상태: `PARTIAL_CANCELED`
- 현재 코드: 처리 안 됨 (Line 243-246의 "기타 상태"로 처리)

**해결 방법**:
```python
elif status == "CANCELED" or status == "PARTIAL_CANCELED":
    # 결제 취소/부분취소 처리
    if existing_payment:
        existing_payment.status = "canceled" if status == "CANCELED" else "partial_canceled"

        # 부분 취소인 경우 남은 금액 계산
        if status == "PARTIAL_CANCELED":
            canceled_amount = data.get("canceledAmount", 0)
            existing_payment.amount = existing_payment.amount - canceled_amount

        db.commit()
        logger.info(f"🔄 Payment {status.lower()}: {order_id}")
```

---

### 5. LOW: 서명 검증 실패 시 HTTP 403 반환 필요

**위치**: `app/services/payment.py:141-143`

**문제**:
```python
if signature and not verify_webhook_signature(json.dumps(payload), signature):
    logger.warning("🚨 Webhook signature verification failed")
    return {"status": "error", "message": "Invalid signature"}  # ❌ 200 OK 반환
```

**보안 이슈**:
- 서명 검증 실패해도 200 OK 응답
- 공격자가 유효하지 않은 웹훅으로 테스트 가능
- 실제 토스페이먼츠 웹훅인지 구분 불가

**권장 방법**:
```python
# app/controllers/payment.py에서 처리
if signature and not payment.verify_webhook_signature(json.dumps(payload), signature):
    logger.warning("🚨 Webhook signature verification failed")
    raise HTTPException(status_code=403, detail="Invalid signature")
```

---

### 6. LOW: DEPOSIT_CALLBACK 페이로드 구조 불일치

**위치**: `app/services/payment.py:254-288`

**문제**:
```python
# Line 263-265: DEPOSIT_CALLBACK 페이로드 파싱
order_id = payload.get("orderId")
status = payload.get("status")
transaction_key = payload.get("transactionKey")
```

**토스페이먼츠 실제 구조**:
```json
{
  "eventType": "DEPOSIT_CALLBACK",
  "createdAt": "2025-10-03T14:30:00+09:00",
  "data": {
    "orderId": "...",
    "status": "DONE",
    "transactionKey": "..."
  }
}
```

**수정 필요**:
```python
data = payload.get("data", {})
order_id = data.get("orderId")
status = data.get("status")
transaction_key = data.get("transactionKey")
```

---

## 🛠️ 수정 우선순위

### 🔴 P0 (즉시 수정 필요)
1. **CANCEL_STATUS_CHANGED 로직 수정**
   - payment_key vs order_id 매칭 오류
   - 구독 취소 실패 가능성

2. **Payment 모델에 payment_key 컬럼 추가**
   - DB 마이그레이션 필요
   - 기존 데이터 영향 고려

### 🟠 P1 (24시간 내 수정)
3. **retry_failed_payment 멱등성 추가**
   - 중복 구독 생성 방지

4. **PARTIAL_CANCELED 처리 추가**
   - 부분 환불 시나리오 지원

### 🟡 P2 (1주일 내 수정)
5. **서명 검증 실패 시 403 반환**
   - 보안 강화

6. **DEPOSIT_CALLBACK 페이로드 구조 수정**
   - 토스페이먼츠 명세 준수

---

## 📊 검수 통계

| 항목 | 수량 |
|------|------|
| **총 검수 항목** | 20개 |
| **통과** | 14개 (70%) |
| **문제 발견** | 6개 (30%) |
| - CRITICAL | 1개 |
| - HIGH | 1개 |
| - MEDIUM | 2개 |
| - LOW | 2개 |

---

## 🎯 다음 단계

### 즉시 조치
1. Payment 모델에 payment_key 추가
2. CANCEL_STATUS_CHANGED 로직 수정
3. 테스트 케이스 추가 (취소, 부분취소)

### 구현 순서
```
Day 1 (오늘):
1. Payment 모델 수정 + 마이그레이션
2. CANCEL_STATUS_CHANGED 로직 수정
3. retry_failed_payment 멱등성 추가
4. 테스트 작성 및 검증

Day 2:
5. PARTIAL_CANCELED 처리 추가
6. DEPOSIT_CALLBACK 구조 수정
7. 서명 검증 403 반환
8. 통합 테스트
```

---

## 💡 추가 권장사항

### 1. 웹훅 재전송 대비
토스페이먼츠는 실패 시 최대 7회 재전송합니다.
멱등성 보장이 매우 중요합니다.

### 2. payment_key 저장
취소/환불 추적을 위해 `payment_key`를 반드시 저장하세요.

### 3. 로그 레벨 조정
프로덕션에서는 이모지 로그를 일반 텍스트로 변경하세요.
Windows 서버에서 인코딩 오류 가능성 있습니다.

### 4. 모니터링 추가
- 웹훅 실패율 추적
- 서명 검증 실패 알림
- 결제 상태 이상 알림

---

**검수 완료일**: 2025-10-03 10:00
**다음 검수**: 수정 완료 후

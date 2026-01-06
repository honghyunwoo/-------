"""
Script V2.1 Validator - 대본 검증기
V2 + 완주율 개선 규칙 (브릿지, 마찰제거) 체크
"""

import json
from pathlib import Path
from typing import Tuple, List, Dict


# CTA 타입 (V2.1: 한글 타입 지원)
VALID_CTA_TYPES = [
    "acknowledge", "celebrate", "connect",  # V2 영문
    "인정형", "축하형", "연결형"  # V2.1 한글
]

# 금지 표현
FORBIDDEN_WORDS = [
    # 장면/화면 지칭
    "지금 화면", "보이시죠", "여기 보면", "이 장면", "화면에", "영상에서",
    # 의료 표현
    "치료", "완치", "진단", "병원", "우울증", "불안장애",
    # 재무 조언
    "투자", "종목", "수익보장", "수익률", "100% 확정", "경제적 자유",
    # 과장/클리셰
    "인생이 바뀐다", "무조건", "반드시", "확실히", "기적",
    "노력하면 된다", "포기하지 마", "꿈은 이루어진다",
    "여러분", "안녕하세요", "오늘은"
]

# 명령형 표현 (S5에서 금지)
IMPERATIVE_PATTERNS = ["해라", "하라", "꺼라", "하세요", "해야 해", "하십시오"]

# V2.1: 브릿지 키워드 (S3에 1개 이상 필요)
BRIDGE_KEYWORDS = [
    "여기서 갈린다", "근데 진짜는", "여기가 핵심", "포인트가 있어",
    "갈린다", "진짜는 지금", "핵심이야"
]

# V2.1: 마찰제거 키워드 (S5에 1개 이상 필요)
# 더 유연한 매칭을 위해 부분 키워드 포함
FRICTION_KEYWORDS = [
    # 명시적 허용 표현
    "멈춰도 돼", "멈춰도 괜찮", "해도 충분", "해도 괜찮", "만 해도 돼",
    "해도 돼", "면 끝", "면 충분",
    # 시간 기반 (짧은 시간 강조)
    "1분이면", "10초만", "5분만", "2초만", "초만", "분만",
    # 유연한 표현 변형
    "충분해", "괜찮아", "도 돼", "만 해도",
    # 부담 제거 표현
    "해봐도", "해보기만", "눌러보기만", "열어보기만",
    # 낮은 부담 암시
    "내일 다시", "다시 볼 수 있", "문장만", "하나만",
    # 실패 부담 제거
    "닫아도", "안 해도", "멈춰도", "그만해도"
]


def validate_script(script: Dict, strict_v21: bool = False) -> Tuple[bool, List[str]]:
    """
    V2/V2.1 스크립트 검증

    Args:
        script: 스크립트 딕셔너리
        strict_v21: V2.1 규칙 강제 (브릿지/마찰제거 필수)

    Returns:
        (통과 여부, 에러/경고 목록)
    """
    errors = []
    warnings = []
    version = script.get("version", "v2")

    # V2.1이면 strict 모드 자동 활성화
    if version == "v2.1":
        strict_v21 = True

    # 1. 버전 체크
    if version not in ["v2", "v2.1"]:
        errors.append(f"[ERROR] version: '{version}' (must be 'v2' or 'v2.1')")

    # 2. 필수 필드 체크
    required_fields = ["id", "category", "topic", "mood", "cta_type",
                       "s1_hook", "s2_pain", "s3_reframe", "s4_insight",
                       "s5_action", "s6_loop_cta", "broll_keywords"]
    for field in required_fields:
        if field not in script:
            errors.append(f"[ERROR] missing field: {field}")

    # 3. CTA 타입 체크
    cta_type = script.get("cta_type", "")
    if cta_type not in VALID_CTA_TYPES:
        errors.append(f"[ERROR] cta_type: '{cta_type}' (invalid)")

    # 4. broll_keywords 체크
    keywords = script.get("broll_keywords", [])
    if len(keywords) != 3:
        errors.append(f"[ERROR] broll_keywords: {len(keywords)}개 (must be exactly 3)")
    for kw in keywords:
        if not isinstance(kw, str) or not kw.isascii():
            errors.append(f"[ERROR] broll_keywords: '{kw}' (must be English)")

    # 5. 문장 길이 체크 (유연한 범위: 25-55자)
    sentences = {
        "s1_hook": (25, 45),   # Hook은 짧게
        "s2_pain": (35, 55),   # Pain은 중간
        "s3_reframe": (35, 55),
        "s4_insight": (35, 55),
        "s5_action": (35, 55),
        "s6_loop_cta": (25, 50)  # CTA도 유연하게
    }

    for name, (min_len, max_len) in sentences.items():
        text = script.get(name, "")
        length = len(text)
        if length < min_len:
            errors.append(f"[ERROR] {name}: {length}자 (minimum {min_len})")
        elif length > max_len:
            warnings.append(f"[WARN] {name}: {length}자 (recommended max {max_len})")

    # 6. 총 길이 체크 (225-285자)
    total_length = sum(len(script.get(s, "")) for s in sentences.keys())
    if total_length < 225:
        errors.append(f"[ERROR] total length: {total_length}자 (minimum 225)")
    elif total_length > 300:
        warnings.append(f"[WARN] total length: {total_length}자 (recommended max 285)")

    # 7. 금지 표현 체크
    all_text = " ".join(script.get(s, "") for s in sentences.keys())
    for word in FORBIDDEN_WORDS:
        if word in all_text:
            errors.append(f"[ERROR] forbidden: '{word}'")

    # 8. S5 제안형 체크 (명령형 금지)
    s5 = script.get("s5_action", "")
    for pattern in IMPERATIVE_PATTERNS:
        if pattern in s5:
            errors.append(f"[ERROR] s5_action: '{pattern}' (imperative forbidden)")

    # 9. V2.1: 브릿지 키워드 체크 (S3)
    s3 = script.get("s3_reframe", "")
    has_bridge = any(kw in s3 for kw in BRIDGE_KEYWORDS)
    if strict_v21 and not has_bridge:
        errors.append("[ERROR] s3_reframe: 브릿지 키워드 필요 (예: '여기서 갈린다')")
    elif not has_bridge:
        warnings.append("[WARN] s3_reframe: 브릿지 추가 권장")

    # 10. V2.1: 마찰제거 키워드 체크 (S5)
    has_friction = any(kw in s5 for kw in FRICTION_KEYWORDS)
    if strict_v21 and not has_friction:
        errors.append("[ERROR] s5_action: 마찰제거 키워드 필요 (예: '멈춰도 돼')")
    elif not has_friction:
        warnings.append("[WARN] s5_action: 마찰제거 추가 권장")

    # 결과
    all_issues = errors + warnings
    return len(errors) == 0, all_issues


def validate_file(file_path: str) -> Dict:
    """JSON 파일 내 모든 스크립트 검증"""
    path = Path(file_path)

    if not path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    with open(path, 'r', encoding='utf-8') as f:
        scripts = json.load(f)

    results = {
        "total": len(scripts),
        "passed": 0,
        "failed": 0,
        "details": []
    }

    for script in scripts:
        script_id = script.get("id", "?")
        passed, issues = validate_script(script)

        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1

        results["details"].append({
            "id": script_id,
            "passed": passed,
            "issues": issues
        })

    results["success"] = results["failed"] == 0

    return results


def print_report(results: Dict):
    """검증 결과 출력"""
    print("\n" + "=" * 50)
    print("Script V2.1 Validation Report")
    print("=" * 50)
    print(f"Total: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print("=" * 50)

    for detail in results["details"]:
        status = "PASS" if detail["passed"] else "FAIL"
        print(f"\n[{status}] ID {detail['id']}")
        for issue in detail["issues"]:
            print(f"  {issue}")

    print("\n" + "=" * 50)
    if results["success"]:
        print("All scripts passed validation!")
    else:
        print(f"{results['failed']} script(s) need fixes.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        # V2.1 예시 파일 검증
        default_file = Path(__file__).parent.parent / "data" / "scripts_v2.1_examples.json"
        file_path = str(default_file)
    else:
        file_path = sys.argv[1]

    print(f"Validating: {file_path}")
    results = validate_file(file_path)
    print_report(results)

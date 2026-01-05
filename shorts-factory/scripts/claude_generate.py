"""
Claude가 직접 작성한 스크립트로 영상 생성
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.factory import Script as FactoryScript, ShortsFactory

# Claude가 직접 작성한 고품질 스크립트
# 명언: 시간을 낭비하는 것은 가장 비싼 낭비다 - 세네카

hook = "당신은 지금 세상에서 가장 비싼 걸 태우고 있습니다."

quote = "시간을 낭비하는 것은 가장 비싼 낭비다."
author = "세네카"

explanation = """돈은 잃어도 다시 벌 수 있습니다.
건강은 잃어도 회복할 수 있습니다.
하지만 시간은? 한 번 지나가면 영원히 돌아오지 않습니다.
2천 년 전 로마의 철학자 세네카는 이미 이 진실을 알았습니다."""

example = """지금 손에 든 스마트폰.
무의미하게 스크롤하는 그 30분이
당신의 꿈을 위한 30분이 될 수 있습니다.
오늘 딱 하나만 바꿔보세요."""

cta = "이 영상이 도움이 됐다면, 저장해두고 시간이 아까울 때마다 다시 보세요."

factory_script = FactoryScript(
    hook=hook,
    quote=quote,
    author=author,
    explanation=explanation,
    application=example,
    cta=cta,
    # 실제 폴더 이름과 매칭되는 키워드 사용
    keywords=["time_passing", "dark_cinematic", "stoic"],
    mood="dramatic"
)

print("=== Claude Script ===")
print(f"[Hook] {hook}")
print(f"[Quote] {quote} - {author}")
print(f"[Explanation] {explanation[:50]}...")
print(f"[Example] {example[:50]}...")
print(f"[CTA] {cta}")
print("=====================")
print()

# 영상 생성
factory = ShortsFactory()
video_path = factory.produce(factory_script, "claude_script_v1")
print(f"\n[COMPLETE] {video_path}")

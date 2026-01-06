"""
업로드 패키지 생성 모듈
YouTube 업로드용 메타데이터 (제목/설명/태그) 자동 생성
"""

import json
from pathlib import Path
from typing import Dict, Optional


# 카테고리별 태그 매핑
CATEGORY_TAGS = {
    "집중_미루기": ["미루기", "집중력", "생산성", "시간관리", "뽀모도로"],
    "디지털_디톡스": ["디지털디톡스", "스마트폰중독", "SNS", "알림관리", "디지털웰빙"],
    "번아웃_회복": ["번아웃", "퇴근", "워라밸", "회복", "직장인"],
    "돈_소비마인드": ["소비습관", "절약", "가계부", "충동구매", "돈관리"],
    "직장_인간관계": ["직장생활", "인간관계", "거절", "커뮤니케이션", "사회생활"],
    "습관_루틴": ["습관", "루틴", "아침루틴", "자기관리", "생활패턴"],
    "감정_마인드셋": ["마인드셋", "감정관리", "멘탈", "자존감", "마음공부"],
    "성장_학습": ["자기계발", "성장", "학습", "목표설정", "동기부여"],
}

# 공통 태그
COMMON_TAGS = ["shorts", "자기계발", "동기부여", "마인드셋", "생활팁"]


class UploadPackager:
    """업로드 메타데이터 생성기"""

    def __init__(self):
        pass

    def generate(
        self,
        script_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        업로드 정보 파일 생성

        Args:
            script_path: script.json 경로
            output_path: 출력 파일 경로 (기본: upload_info.txt)

        Returns:
            생성된 파일 경로
        """
        script_path = Path(script_path)

        if output_path is None:
            output_path = script_path.parent / "upload_info.txt"

        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)

        # 메타데이터 생성
        title = self._generate_title(script)
        description = self._generate_description(script)
        tags = self._generate_tags(script)

        # 파일 작성
        content = self._format_output(title, description, tags, script)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def _generate_title(self, script: Dict) -> str:
        """제목 생성"""
        topic = script.get('topic', '')
        category = script.get('category', '').replace('_', ' ')
        hook = script.get('s1_hook', '')

        # 훅 문장에서 키워드 추출 (첫 부분)
        hook_short = hook[:20] + "..." if len(hook) > 20 else hook

        # 제목 형식: "키워드 | 토픽 #shorts"
        title = f"{hook_short} | {topic} #shorts"

        return title

    def _generate_description(self, script: Dict) -> str:
        """설명 생성"""
        s1 = script.get('s1_hook', '')
        s2 = script.get('s2_pain', '')
        s4 = script.get('s4_insight', '')
        category = script.get('category', '')

        # 카테고리별 태그
        cat_tags = CATEGORY_TAGS.get(category, [])
        hashtags = " ".join([f"#{tag}" for tag in cat_tags[:5]])

        description = f"""{s1}

{s2}

핵심 포인트:
{s4}

{hashtags} #shorts #자기계발"""

        return description

    def _generate_tags(self, script: Dict) -> list:
        """태그 생성"""
        category = script.get('category', '')
        topic = script.get('topic', '')

        tags = []

        # 카테고리별 태그
        cat_tags = CATEGORY_TAGS.get(category, [])
        tags.extend(cat_tags)

        # 토픽 추가
        if topic:
            tags.append(topic)

        # 공통 태그
        tags.extend(COMMON_TAGS)

        # 중복 제거
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags

    def _format_output(
        self,
        title: str,
        description: str,
        tags: list,
        script: Dict
    ) -> str:
        """출력 포맷"""
        category = script.get('category', '')
        topic = script.get('topic', '')
        video_id = script.get('id', 0)

        output = f"""{'='*50}
YouTube Shorts 업로드 정보
{'='*50}

[제목] (복사해서 붙여넣기)
{title}

{'='*50}

[설명] (복사해서 붙여넣기)
{description}

{'='*50}

[태그] (쉼표로 구분)
{', '.join(tags)}

{'='*50}

[카테고리]
교육

[공개 설정]
공개

{'='*50}
메타데이터
{'='*50}
- 스크립트 ID: {video_id}
- 카테고리: {category}
- 토픽: {topic}
- 버전: {script.get('version', 'v2')}
- CTA 타입: {script.get('cta_type', '')}
{'='*50}
"""
        return output


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python upload_packager.py <project_folder>")
        print("Example: python upload_packager.py output/20260106_집중_미루기_01")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    script_path = project_dir / "script.json"
    output_path = project_dir / "upload_info.txt"

    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        sys.exit(1)

    packager = UploadPackager()
    result = packager.generate(script_path, output_path)
    print(f"[OK] Upload info generated: {result}")

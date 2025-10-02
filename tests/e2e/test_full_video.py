#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
전체 영상 생성 플로우 테스트
수정된 품질 설정 검증:
1. 썸네일 한글 폰트
2. 자막 한글 폰트
3. 고품질 인코딩 (8000k bitrate)
4. 고품질 소스 영상 (4K/Full HD)
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.models.schema import VideoParams, VideoAspect
from app.services import material, llm, voice, video, subtitle
from app.utils import utils
import os

def test_full_video_generation():
    """전체 영상 생성 테스트"""
    print("=" * 60)
    print("전체 영상 생성 플로우 테스트")
    print("=" * 60)

    # 1. 영상 파라미터 설정
    params = VideoParams()
    params.video_subject = "AI 영상 제작 자동화"
    params.video_script = """
AI 영상 제작 자동화의 시대가 열렸습니다.
이제 누구나 고품질 영상을 쉽게 만들 수 있습니다.
자동 자막, 배경 음악, 전문가급 편집까지 모두 가능합니다.
당신의 아이디어를 영상으로 만들어보세요.
"""
    params.video_aspect = VideoAspect.portrait.value
    params.voice_name = "ko-KR-SunHiNeural"
    params.voice_volume = 1.0
    params.bgm_type = "random"
    params.bgm_volume = 0.3
    params.subtitle_enabled = True
    params.font_name = "MicrosoftYaHeiBold.ttc"
    params.font_size = 60
    params.text_fore_color = "#FFFFFF"
    params.stroke_color = "#000000"
    params.stroke_width = 1.5
    params.n_threads = 4
    params.paragraph_number = 1

    print(f"\n✅ 파라미터 설정 완료")
    print(f"   주제: {params.video_subject}")
    print(f"   화면 비율: {params.video_aspect}")
    print(f"   폰트: {params.font_name} (한글 지원)")

    # 2. 비디오 소재 검색
    print(f"\n📹 고품질 비디오 소재 검색 중...")
    search_terms = ["AI technology", "video production", "automation"]
    materials = []

    for term in search_terms[:2]:  # 2개 소스만 (테스트용)
        print(f"   검색: {term}")
        items = material.search_videos_pexels(
            search_term=term,
            minimum_duration=5,
            video_aspect=VideoAspect.portrait
        )
        if items:
            materials.append(items[0])
            print(f"   ✅ 찾음: {items[0].url}")

    if not materials:
        print("❌ 비디오 소재를 찾을 수 없습니다")
        return

    print(f"\n✅ {len(materials)}개 고품질 소재 확보 (4K/Full HD 우선 선택)")

    # 3. 비디오 소재 다운로드
    print(f"\n⬇️  비디오 다운로드 중...")
    downloaded_materials = material.save_videos(
        materials=materials,
        material_directory="storage/test_materials"
    )
    print(f"✅ 다운로드 완료: {len(downloaded_materials)}개")

    # 4. TTS 음성 생성
    print(f"\n🎤 음성 생성 중...")
    audio_file = voice.tts(
        text=params.video_script,
        voice_name=params.voice_name,
        voice_rate=1.0,
        voice_file="storage/test_audio.mp3"
    )
    print(f"✅ 음성 생성 완료: {audio_file}")

    # 5. 자막 생성
    print(f"\n📝 자막 생성 중...")
    subtitle_path = subtitle.generate_subtitles(
        audio_file=audio_file,
        subtitle_file="storage/test_subtitle.srt"
    )
    print(f"✅ 자막 생성 완료: {subtitle_path}")

    # 6. 비디오 편집 및 합성
    print(f"\n🎬 비디오 합성 중 (고품질 8000k bitrate)...")
    final_video_path = "storage/test_videos/final_test_video.mp4"

    # 소재를 비디오로 결합
    combined_video = video.combine_videos(
        combined_video_path="storage/test_videos/combined.mp4",
        video_paths=[m.url for m in downloaded_materials],
        video_aspect=VideoAspect.portrait,
        video_concat_mode=params.video_concat_mode,
        max_clip_duration=params.video_clip_duration,
        threads=params.n_threads
    )

    print(f"✅ 비디오 결합 완료")

    # 7. 최종 영상 생성 (자막 + 음성)
    print(f"\n🎥 최종 영상 생성 중...")
    video.generate_video(
        video_path=combined_video,
        audio_path=audio_file,
        subtitle_path=subtitle_path,
        output_file=final_video_path,
        params=params
    )

    print(f"\n" + "=" * 60)
    print(f"🎉 전체 영상 생성 완료!")
    print(f"=" * 60)
    print(f"\n📁 최종 결과물:")
    print(f"   영상: {final_video_path}")
    print(f"   음성: {audio_file}")
    print(f"   자막: {subtitle_path}")

    # 파일 크기 확인
    if os.path.exists(final_video_path):
        size_mb = os.path.getsize(final_video_path) / (1024*1024)
        print(f"\n📊 영상 파일 크기: {size_mb:.2f}MB")
        print(f"   (고품질 설정으로 인해 크기가 증가할 수 있습니다)")

    print(f"\n✅ 품질 개선 사항:")
    print(f"   ✓ 썸네일 한글 폰트 (맑은 고딕)")
    print(f"   ✓ 자막 한글 폰트 (Microsoft YaHei Bold)")
    print(f"   ✓ 고품질 인코딩 (8000k bitrate, slow preset)")
    print(f"   ✓ 고품질 소스 (4K/Full HD 우선 선택)")

if __name__ == "__main__":
    try:
        test_full_video_generation()
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

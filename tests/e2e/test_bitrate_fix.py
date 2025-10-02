#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
비트레이트 수정 확인 테스트
- 8000k bitrate가 실제로 적용되는지 검증
- 간단한 테스트 영상 생성
"""

import sys
import io
import os

# Python 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from pathlib import Path
from app.models.schema import VideoParams, VideoAspect
from app.services import material, voice, video
from moviepy.video.io.VideoFileClip import VideoFileClip


def test_bitrate_encoding():
    """비트레이트 인코딩 테스트"""
    print("=" * 70)
    print("🎬 비트레이트 수정 확인 테스트")
    print("=" * 70)
    print()
    
    test_dir = Path("storage/bitrate_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 테스트 영상 소재 검색 (1개만)
    print("📹 1단계: 테스트 영상 소재 검색...")
    materials = material.search_videos_pexels(
        search_term="technology",
        minimum_duration=5,
        video_aspect=VideoAspect.portrait
    )
    
    if not materials:
        print("❌ 영상 소재를 찾을 수 없습니다")
        return
    
    print(f"✅ 소재 발견: {materials[0].url}")
    
    # 2. 영상 다운로드
    print("\n⬇️  2단계: 영상 다운로드...")
    downloaded = material.save_video(
        video_url=materials[0].url,
        save_dir=str(test_dir)
    )
    
    if not downloaded:
        print("❌ 다운로드 실패")
        return
    
    print(f"✅ 다운로드 완료: {downloaded}")
    
    # 3. TTS 생성 (짧은 텍스트)
    print("\n🎤 3단계: 음성 생성...")
    audio_file = str(test_dir / "test_audio.mp3")
    
    try:
        voice.tts(
            text="이것은 비트레이트 테스트입니다.",
            voice_name="ko-KR-SunHiNeural",
            voice_rate=1.0,
            voice_file=audio_file
        )
        print(f"✅ TTS 생성 완료: {audio_file}")
    except Exception as e:
        print(f"❌ TTS 생성 실패: {str(e)}")
        return
    
    # 4. 최종 영상 합성 (8000k bitrate 적용)
    print("\n🎥 4단계: 최종 영상 합성 (8000k bitrate)...")
    output_file = str(test_dir / "final_bitrate_test.mp4")
    
    params = VideoParams(
        video_subject="Bitrate Test",
        video_aspect=VideoAspect.portrait,
        voice_name="ko-KR-SunHiNeural",
        font_name="MicrosoftYaHeiBold.ttc",
        n_threads=4
    )
    
    try:
        # combine_videos 대신 직접 generate_video 호출
        video.generate_video(
            video_path=downloaded,
            audio_path=audio_file,
            subtitle_path=None,  # 자막 없이
            output_file=output_file,
            params=params
        )
        
        print(f"✅ 영상 합성 완료: {output_file}")
        
    except Exception as e:
        print(f"❌ 영상 합성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. 품질 검증
    print("\n🔍 5단계: 품질 검증...")
    
    if not os.path.exists(output_file):
        print("❌ 최종 파일이 생성되지 않았습니다")
        return
    
    try:
        clip = VideoFileClip(output_file)
        width, height = clip.size
        fps = clip.fps
        duration = clip.duration
        clip.close()
        
        # 비트레이트 계산
        file_size_bits = os.path.getsize(output_file) * 8
        bitrate_kbps = file_size_bits / duration / 1000
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        
        print(f"\n📊 결과:")
        print(f"   해상도: {width}x{height}")
        print(f"   FPS: {fps}")
        print(f"   길이: {duration:.1f}초")
        print(f"   파일 크기: {file_size_mb:.2f}MB")
        print(f"   비트레이트: {bitrate_kbps:.0f}k")
        
        # 비트레이트 검증
        if bitrate_kbps >= 7000:
            print(f"\n✅ 비트레이트 테스트 통과! (목표: ≥7000k, 실제: {bitrate_kbps:.0f}k)")
            print("   ✓ 8000k bitrate 설정이 올바르게 적용되었습니다")
            return True
        else:
            print(f"\n❌ 비트레이트 테스트 실패! (목표: ≥7000k, 실제: {bitrate_kbps:.0f}k)")
            print("   ✗ 8000k bitrate 설정이 적용되지 않았습니다")
            print("\n🔍 원인 분석:")
            print("   1. MoviePy의 bitrate 파라미터가 무시되고 있을 가능성")
            print("   2. FFmpeg 버전 문제")
            print("   3. Codec 호환성 문제")
            return False
            
    except Exception as e:
        print(f"❌ 검증 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = test_bitrate_encoding()
        
        print("\n" + "=" * 70)
        if result:
            print("🎉 비트레이트 수정 확인 완료 - 정상 작동")
        else:
            print("⚠️ 비트레이트 수정 확인 완료 - 추가 수정 필요")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

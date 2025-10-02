import unittest
import os
import sys
from pathlib import Path
from uuid import uuid4

# 프로젝트 루트 경로 추가
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.services import task as tm
from app.models.schema import VideoParams, VideoAspect, VideoConcatMode
from app.utils import utils
from tests.e2e.test_quality_verification import get_video_properties

class TestFullPipeline(unittest.TestCase):
    def setUp(self):
        """테스트 실행 전 초기화"""
        self.task_id = str(uuid4())
        self.output_dir = utils.task_dir(self.task_id)
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        """테스트 실행 후 정리"""
        # 생성된 테스트 디렉토리 정리 (필요 시 주석 해제)
        # import shutil
        # if os.path.exists(self.output_dir):
        #     shutil.rmtree(self.output_dir)
        pass

    def test_full_video_generation_pipeline(self):
        """E2E 테스트: 전체 영상 생성 파이프라인 검증"""
        
        # 1. 테스트 파라미터 설정
        params = VideoParams(
            video_subject="AI 기술의 미래와 우리 삶의 변화",
            video_script="AI는 이제 단순한 기술을 넘어, 우리 일상의 모든 면을 바꾸고 있습니다. 이 영상에서는 AI가 어떻게 우리의 미래를 만들어 가는지 살펴보겠습니다.",
            video_aspect=VideoAspect.portrait,
            video_concat_mode=VideoConcatMode.random,
            video_clip_duration=5,
            video_count=1,
            video_source="pexels",
            video_language="ko",
            voice_name="ko-KR-SunHiNeural-Female",
            bgm_type="random",
            subtitle_enabled=True,
            font_name="NanumGothic.ttf", # 한글 지원 폰트
            n_threads=4
        )

        # 2. 태스크 실행
        # 참고: 이 테스트는 실제 API를 호출하므로 시간이 오래 걸릴 수 있습니다. (약 5-10분)
        result = tm.start(task_id=self.task_id, params=params, db=None, user=None)

        # 3. 결과 검증
        self.assertIsNotNone(result, "Task result should not be None")
        self.assertIn("videos", result, "Result should contain 'videos' key")
        
        final_video_paths = result.get("videos", [])
        self.assertEqual(len(final_video_paths), 1, "Should generate 1 video")

        final_video_path = Path(final_video_paths[0])
        self.assertTrue(final_video_path.exists(), f"Final video file not found at {final_video_path}")
        self.assertGreater(final_video_path.stat().st_size, 1024 * 100, "Video file size should be > 100KB") # 최소 100KB 이상

        # 4. 품질 검증
        properties = get_video_properties(final_video_path)
        
        self.assertNotIn("error", properties, f"Failed to get video properties: {properties.get('error')}")
        
        # 비트레이트 검증 (목표: 8000k, 허용오차 감안하여 7000k 이상)
        self.assertGreaterEqual(properties.get("bit_rate_kbps", 0), 7000, "Bitrate should be at least 7000 kbps")
        self.assertEqual(properties.get("width"), 1080, "Video width should be 1080")
        self.assertEqual(properties.get("height"), 1920, "Video height should be 1920")
        self.assertAlmostEqual(properties.get("fps", 0), 30, delta=1, msg="FPS should be around 30")

if __name__ == "__main__":
    unittest.main()
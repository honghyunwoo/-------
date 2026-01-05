"""
영상 리뷰용 스크린샷 캡처 스크립트
- 2초마다 화면 캡처
- ESC 키로 종료
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    import pyautogui
    import keyboard
except ImportError:
    print("필요한 패키지 설치 중...")
    os.system("pip install pyautogui keyboard pillow")
    import pyautogui
    import keyboard


def create_output_dir():
    """출력 디렉토리 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"./review_captures/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def capture_loop(output_dir: Path, interval: float = 2.0):
    """주기적 스크린샷 캡처"""
    print("=" * 50)
    print("🎬 영상 리뷰 캡처 시작!")
    print("=" * 50)
    print(f"📁 저장 위치: {output_dir}")
    print(f"⏱️  캡처 간격: {interval}초")
    print("🛑 종료하려면 ESC 키를 누르세요")
    print("=" * 50)
    print("\n▶️  지금 영상을 재생하세요!\n")

    frame_count = 0
    start_time = time.time()
    running = True

    def stop_capture():
        nonlocal running
        running = False
        print("\n⏹️  캡처 종료 요청...")

    keyboard.on_press_key('esc', lambda _: stop_capture())

    try:
        while running:
            # 스크린샷 캡처
            screenshot = pyautogui.screenshot()

            # 타임스탬프 계산
            elapsed = time.time() - start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)

            # 파일명: frame_001_0m05s.png
            filename = f"frame_{frame_count:03d}_{minutes}m{seconds:02d}s.png"
            filepath = output_dir / filename

            screenshot.save(str(filepath))
            print(f"📸 캡처: {filename}")

            frame_count += 1
            time.sleep(interval)

    except KeyboardInterrupt:
        pass

    print("\n" + "=" * 50)
    print(f"✅ 캡처 완료!")
    print(f"📊 총 {frame_count}장 캡처됨")
    print(f"📁 저장 위치: {output_dir}")
    print("=" * 50)

    return output_dir, frame_count


def main():
    # 캡처 간격 (기본 2초)
    interval = 2.0
    if len(sys.argv) > 1:
        try:
            interval = float(sys.argv[1])
        except ValueError:
            pass

    output_dir = create_output_dir()

    print("\n🎥 3초 후 캡처를 시작합니다...")
    print("   지금 영상 플레이어를 준비하세요!")
    time.sleep(3)

    capture_loop(output_dir, interval)


if __name__ == "__main__":
    main()

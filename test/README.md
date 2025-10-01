# 올빼미 AI 영상 스튜디오 - 테스트 디렉토리

이 디렉토리는 **올빼미 AI 영상 스튜디오** 프로젝트의 단위 테스트를 포함합니다.

## 디렉토리 구조

- `services/`: `app/services` 디렉토리의 컴포넌트 테스트
  - `test_video.py`: 영상 서비스 테스트
  - `test_task.py`: 작업 서비스 테스트
  - `test_voice.py`: 음성 서비스 테스트

## 테스트 실행 방법

Python의 내장 `unittest` 프레임워크를 사용하여 테스트를 실행할 수 있습니다:

```bash
# 모든 테스트 실행
python -m unittest discover -s test

# 특정 테스트 파일 실행
python -m unittest test/services/test_video.py

# 특정 테스트 클래스 실행
python -m unittest test.services.test_video.TestVideoService

# 특정 테스트 메서드 실행
python -m unittest test.services.test_video.TestVideoService.test_preprocess_video
```

## 새로운 테스트 추가하기

다른 컴포넌트에 대한 테스트를 추가하려면 다음 가이드라인을 따르세요:

1. 적절한 하위 디렉토리에 `test_` 접두사가 붙은 테스트 파일 생성
2. 테스트 클래스의 기본 클래스로 `unittest.TestCase` 사용
3. 테스트 메서드 이름에 `test_` 접두사 사용

## 테스트 리소스

테스트에 필요한 리소스 파일은 `test/resources` 디렉토리에 배치하세요.

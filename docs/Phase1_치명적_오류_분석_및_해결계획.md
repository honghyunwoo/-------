# Phase 1: 치명적 오류 분석 및 해결 계획

**프로젝트**: 올빼미 AI 영상 스튜디오  
**수석 개발자**: Claude  
**분석일**: 2025-10-01  
**우선순위**: 🚨 최우선 (생존 필수)

---

## 🚨 치명적 오류 상세 분석

### **1순위: 자막 동기화 완전 실패** 🚨 최우선

#### **현재 문제**:
- 2,3,4번째 자막 타이밍이 모두 `00:00:00,000`으로 표시
- 첫 번째 자막만 1.83초로 정상
- 음성과 자막이 완전히 동기화되지 않음

#### **원인 분석**:
1. **`subtitle.py`의 `correct()` 함수 문제**:
   ```python
   # Line 187-283: correct() 함수에서 타이밍 계산 오류
   # audio_duration이 0일 때 추정값 사용하지만 정확하지 않음
   if audio_duration == 0:
       estimated_duration = len(video_script) / 4.0  # 부정확한 추정
   ```

2. **`voice.py`의 `create_subtitle()` 함수 문제**:
   ```python
   # Line 1393-1488: create_subtitle() 함수에서 타이밍 계산 오류
   # SubMaker 객체의 offset 정보가 정확하지 않음
   ```

3. **Whisper 자막 생성과 TTS 자막 생성 충돌**:
   - Edge TTS 자막 생성 실패 시 Whisper로 fallback
   - 두 시스템 간 타이밍 계산 방식이 다름

#### **해결 방안**:
1. **오디오 파일 길이 정확 측정**:
   ```python
   # MoviePy를 사용한 정확한 오디오 길이 측정
   from moviepy.editor import AudioFileClip
   with AudioFileClip(audio_file_path) as audio_clip:
       audio_duration = audio_clip.duration
   ```

2. **자막 타이밍 계산 로직 수정**:
   ```python
   # 문자 수 기반이 아닌 실제 오디오 길이 기반 계산
   duration_per_character = audio_duration / len(video_script)
   ```

3. **SRT 파일 생성 검증**:
   ```python
   # 생성된 SRT 파일의 타이밍 검증
   def validate_srt_timing(srt_file):
       # 모든 자막이 0초가 아닌지 확인
   ```

---

### **2순위: 한국어 음성 실제 적용 실패** 🇰🇷

#### **현재 문제**:
- `config.toml`에서 `ko-KR-SunHiNeural`로 설정했으나
- `script.json`에서 여전히 `de-AT-IngridNeural-Female` 사용
- 한국어 콘텐츠에 독일어 음성 생성

#### **원인 분석**:
1. **음성 설정 로딩 문제**:
   ```python
   # task.py에서 음성 설정이 제대로 로딩되지 않음
   # config.voice.voice_name이 실제 TTS 호출 시 반영되지 않음
   ```

2. **TTS 서비스 선택 로직 문제**:
   ```python
   # voice.py의 tts() 함수에서 음성 선택 로직 오류
   # Azure TTS v1/v2 선택 시 설정이 제대로 전달되지 않음
   ```

3. **캐싱 문제**:
   ```python
   # Line 1084-1092: TTS 캐싱으로 인해 이전 설정이 유지됨
   cache_key = f"tts:{utils.md5(text + voice_name + str(voice_rate) + str(voice_volume))}"
   ```

#### **해결 방안**:
1. **음성 설정 강제 적용**:
   ```python
   # config.toml 설정을 강제로 적용하는 로직 추가
   def force_korean_voice():
       return "ko-KR-SunHiNeural"
   ```

2. **캐시 무효화**:
   ```python
   # 음성 설정 변경 시 캐시 무효화
   cache.clear_cache("tts:*")
   ```

3. **TTS 호출 검증**:
   ```python
   # 실제 TTS 호출 시 한국어 음성 사용 확인
   logger.info(f"Using voice: {voice_name}")
   ```

---

### **3순위: 영상 길이 너무 짧음** ⏰

#### **현재 문제**:
- `max_clip_duration`이 15초로 설정되어 있음
- 실제 클립들이 3초씩만 사용됨
- 총 영상 길이가 너무 짧음 (경쟁사는 10초+)

#### **원인 분석**:
1. **클립 길이 설정 문제**:
   ```python
   # video.py의 combine_videos() 함수에서
   max_clip_duration: int = 30  # 설정은 30초이지만 실제 적용 안 됨
   ```

2. **클립 수집 로직 문제**:
   ```python
   # material.py에서 클립 수집 시 길이 제한
   # 다운로드된 클립의 실제 길이가 짧음
   ```

3. **클립 반복/루핑 시스템 부족**:
   ```python
   # video.py에서 클립 루핑 로직이 제대로 작동하지 않음
   ```

#### **해결 방안**:
1. **클립 길이 설정 강제 적용**:
   ```python
   # max_clip_duration을 30초로 강제 설정
   max_clip_duration = 30
   ```

2. **클립 수집 로직 개선**:
   ```python
   # 더 긴 클립을 우선적으로 선택하는 로직
   def select_longer_clips(video_files, min_duration=10):
   ```

3. **클립 반복 시스템 개선**:
   ```python
   # 오디오 길이에 맞춘 클립 반복 로직
   def loop_clips_to_match_audio(clips, audio_duration):
   ```

---

### **4순위: 한글 폰트 설정 미적용** 🔤

#### **현재 문제**:
- `Charm-Bold.ttf`로 설정했으나 실제 적용 확인 필요
- `script.json`에서 여전히 `MicrosoftYaHeiBold.ttc` 표시
- 한글 자막에 어울리지 않는 폰트 사용

#### **원인 분석**:
1. **폰트 설정 로딩 문제**:
   ```python
   # config.toml의 font_name 설정이 실제 적용되지 않음
   ```

2. **폰트 파일 경로 문제**:
   ```python
   # 폰트 파일이 존재하지 않거나 경로가 잘못됨
   ```

3. **폰트 로딩 실패 시 폴백 문제**:
   ```python
   # 폰트 로딩 실패 시 기본 폰트로 폴백되지만 한글 지원 안 됨
   ```

#### **해결 방안**:
1. **폰트 설정 강제 적용**:
   ```python
   # 한글 폰트를 강제로 적용하는 로직
   def force_korean_font():
       return "Charm-Bold.ttf"
   ```

2. **폰트 파일 검증**:
   ```python
   # 폰트 파일 존재 여부 및 한글 지원 확인
   def validate_korean_font(font_path):
   ```

3. **폰트 로딩 검증**:
   ```python
   # 폰트 로딩 성공 여부 및 한글 렌더링 확인
   def test_font_rendering(font_path, test_text="안녕하세요"):
   ```

---

## 📋 Phase 1 해결 계획

### **Task 1: 자막 동기화 완전 수정** 🚨 최우선

**예상 소요 시간**: 2일  
**난이도**: 높음  
**영향도**: 매우 높음

**구체적 작업**:
1. **오디오 길이 측정 로직 수정**:
   ```python
   # subtitle.py의 correct() 함수 수정
   def get_accurate_audio_duration(audio_file_path):
       try:
           from moviepy.editor import AudioFileClip
           with AudioFileClip(audio_file_path) as audio_clip:
               return audio_clip.duration
       except Exception as e:
           logger.error(f"Failed to measure audio duration: {e}")
           return 0
   ```

2. **자막 타이밍 계산 로직 수정**:
   ```python
   # 정확한 타이밍 계산
   def calculate_subtitle_timing(script_lines, audio_duration):
       total_chars = sum(len(line) for line in script_lines)
       current_time = 0
       
       for line in script_lines:
           line_duration = (len(line) / total_chars) * audio_duration
           start_time = current_time
           end_time = current_time + line_duration
           current_time = end_time
           
           yield start_time, end_time, line
   ```

3. **SRT 파일 생성 검증**:
   ```python
   # 생성된 SRT 파일 검증
   def validate_srt_file(srt_file):
       with open(srt_file, 'r', encoding='utf-8') as f:
           content = f.read()
       
       # 모든 자막이 0초가 아닌지 확인
       lines = content.split('\n')
       for i, line in enumerate(lines):
           if '-->' in line and '00:00:00,000' in line:
               logger.error(f"Subtitle timing error at line {i}: {line}")
               return False
       return True
   ```

**성공 기준**:
- 모든 자막이 정확한 타이밍을 가짐
- 음성과 자막이 완벽히 동기화
- SRT 파일 포맷이 올바름

---

### **Task 2: 한국어 음성 실제 적용 검증** 🇰🇷

**예상 소요 시간**: 1일  
**난이도**: 중간  
**영향도**: 높음

**구체적 작업**:
1. **음성 설정 강제 적용**:
   ```python
   # task.py에서 음성 설정 강제 적용
   def get_voice_name(params):
       # 한국어 음성 강제 적용
       if params.video_language == "ko":
           return "ko-KR-SunHiNeural"
       return params.voice_name or "ko-KR-SunHiNeural"
   ```

2. **TTS 호출 검증**:
   ```python
   # voice.py에서 TTS 호출 시 로깅 추가
   def tts(text, voice_name, voice_rate, voice_file, voice_volume=1.0):
       logger.info(f"TTS called with voice: {voice_name}")
       # 실제 음성 생성 로직
   ```

3. **캐시 무효화**:
   ```python
   # 음성 설정 변경 시 캐시 무효화
   def clear_tts_cache():
       cache.clear_cache("tts:*")
   ```

**성공 기준**:
- 한국어 음성으로 나레이션 생성 확인
- 음성 품질이 자연스러움
- 발음이 정확함

---

### **Task 3: 영상 길이 30초 연장 시스템 구현** ⏰

**예상 소요 시간**: 1일  
**난이도**: 중간  
**영향도**: 중간

**구체적 작업**:
1. **클립 길이 설정 강제 적용**:
   ```python
   # video.py에서 max_clip_duration 강제 설정
   def combine_videos(..., max_clip_duration: int = 30):
       # 30초로 강제 설정
       max_clip_duration = 30
   ```

2. **클립 수집 로직 개선**:
   ```python
   # material.py에서 더 긴 클립 우선 선택
   def select_longer_clips(video_files, min_duration=10):
       return [v for v in video_files if v.get('duration', 0) >= min_duration]
   ```

3. **클립 반복 시스템 개선**:
   ```python
   # 오디오 길이에 맞춘 클립 반복
   def loop_clips_to_match_audio(clips, audio_duration):
       total_duration = sum(clip.duration for clip in clips)
       if total_duration < audio_duration:
           # 클립 반복하여 오디오 길이에 맞춤
           pass
   ```

**성공 기준**:
- 30초 이상의 영상 생성
- 클립 간 자연스러운 연결
- 오디오와 영상 길이 완벽 매칭

---

### **Task 4: 한글 폰트 완벽 적용 및 검증** 🔤

**예상 소요 시간**: 1일  
**난이도**: 낮음  
**영향도**: 중간

**구체적 작업**:
1. **폰트 설정 강제 적용**:
   ```python
   # config.toml 설정을 강제로 적용
   def get_font_name():
       return "Charm-Bold.ttf"
   ```

2. **폰트 파일 검증**:
   ```python
   # 폰트 파일 존재 여부 확인
   def validate_font_file(font_path):
       if not os.path.exists(font_path):
           logger.error(f"Font file not found: {font_path}")
           return False
       return True
   ```

3. **폰트 로딩 검증**:
   ```python
   # 폰트 로딩 성공 여부 확인
   def test_font_loading(font_path):
       try:
           from PIL import ImageFont
           font = ImageFont.truetype(font_path, 60)
           return True
       except Exception as e:
           logger.error(f"Font loading failed: {e}")
           return False
   ```

**성공 기준**:
- 한글 폰트가 정상적으로 적용됨
- 자막에서 한글이 깨지지 않음
- 폰트 품질이 우수함

---

## 🎯 Phase 1 완료 후 검증

### **검증 항목**:
1. **자막 동기화 성공률**: 95%+
2. **한국어 음성 적용률**: 100%
3. **영상 길이**: 평균 12초+
4. **사용자 불만 제로화**

### **검증 방법**:
1. **테스트 영상 생성**: 3개 테스트 영상 생성
2. **품질 검증**: 각 영상의 자막, 음성, 길이 검증
3. **사용자 테스트**: 실제 사용자에게 테스트 영상 제공
4. **피드백 수집**: 사용자 피드백 수집 및 개선

---

## 📅 실행 일정

**Day 1**: 자막 동기화 수정 (Task 1)  
**Day 2**: 한국어 음성 적용 (Task 2)  
**Day 3**: 영상 길이 연장 (Task 3)  
**Day 4**: 한글 폰트 적용 (Task 4)  
**Day 5**: 통합 테스트 및 검증

**총 소요 시간**: 5일  
**예상 효과**: 기본 기능 완전 작동, 사용자 불만 제로화

---

**Phase 1 계획 작성자**: Claude (수석 개발자)  
**작성일**: 2025-10-01  
**다음 업데이트**: 2025-10-02  
**문서 버전**: 1.0.0

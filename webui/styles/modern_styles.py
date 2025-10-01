# -*- coding: utf-8 -*-
"""
현대적 디자인 스타일 정의
AI 동영상 생성 플랫폼을 위한 모던 UI/UX
"""

MODERN_CSS = """
<style>
    /* 구글 폰트 임포트 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

    /* CSS 변수 정의 */
    :root {
        /* Primary Colors */
        --primary-blue: #2563EB;
        --accent-purple: #7C3AED;
        --success-green: #059669;

        /* Neutral Colors */
        --dark-gray: #1F2937;
        --mid-gray: #6B7280;
        --light-gray: #F9FAFB;
        --white: #FFFFFF;

        /* Gradients */
        --hero-gradient: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
        --card-gradient: linear-gradient(135deg, #FFFFFF 0%, #F0F8FF 100%);
        --action-gradient: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%);

        /* Typography */
        --font-primary: 'Inter', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-korean: 'Noto Sans KR', 'Malgun Gothic', sans-serif;

        /* Spacing */
        --spacing-xs: 0.5rem;
        --spacing-sm: 1rem;
        --spacing-md: 1.5rem;
        --spacing-lg: 2rem;
        --spacing-xl: 3rem;

        /* Border Radius */
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 24px;

        /* Shadows */
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);

        /* Glassmorphism */
        --glass-bg: rgba(255, 255, 255, 0.15);
        --glass-border: rgba(255, 255, 255, 0.2);
        --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        --glass-blur: blur(8px);
    }

    /* 전체 앱 스타일링 */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: var(--font-primary);
    }

    /* 메인 컨테이너 */
    .main .block-container {
        padding: var(--spacing-lg) var(--spacing-md);
        max-width: 1400px;
        margin: 0 auto;
    }

    /* 헤더 스타일링 */
    .stApp > header {
        background: var(--glass-bg);
        backdrop-filter: var(--glass-blur);
        border-bottom: 1px solid var(--glass-border);
    }

    /* 타이틀 스타일링 */
    h1 {
        font-family: var(--font-primary) !important;
        font-weight: 700 !important;
        background: var(--hero-gradient) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin-bottom: var(--spacing-lg) !important;
        padding-top: 0 !important;
        font-size: 2.5rem !important;
        letter-spacing: -0.025em !important;
    }

    /* 서브헤딩 스타일 */
    h2, h3 {
        font-family: var(--font-primary) !important;
        font-weight: 600 !important;
        color: var(--dark-gray) !important;
        margin: var(--spacing-md) 0 var(--spacing-sm) 0 !important;
    }

    /* 카드 스타일 (벤토 그리드) */
    .stContainer,
    .element-container {
        background: var(--glass-bg);
        backdrop-filter: var(--glass-blur);
        border-radius: var(--radius-lg);
        border: 1px solid var(--glass-border);
        box-shadow: var(--glass-shadow);
        padding: var(--spacing-md);
        margin: var(--spacing-sm) 0;
        transition: all 0.3s ease;
    }

    .stContainer:hover,
    .element-container:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-xl);
    }

    /* 입력 필드 스타일링 */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox select {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 2px solid transparent !important;
        border-radius: var(--radius-md) !important;
        font-family: var(--font-primary) !important;
        font-size: 14px !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stSelectbox select:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }

    /* 버튼 스타일링 */
    .stButton button {
        background: var(--action-gradient) !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        color: white !important;
        font-family: var(--font-primary) !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-md) !important;
        cursor: pointer !important;
        min-height: 44px !important;
    }

    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-lg) !important;
        filter: brightness(110%) !important;
    }

    .stButton button:active {
        transform: translateY(0) !important;
    }

    /* 프라이머리 버튼 */
    .stButton[data-testid="baseButton-primaryFormSubmit"] button {
        background: var(--hero-gradient) !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 16px 32px !important;
        border-radius: var(--radius-lg) !important;
        min-height: 56px !important;
    }

    /* 사이드바 스타일링 */
    .css-1d391kg {
        background: var(--glass-bg) !important;
        backdrop-filter: var(--glass-blur) !important;
        border-right: 1px solid var(--glass-border) !important;
    }

    /* 체크박스 스타일링 */
    .stCheckbox {
        font-family: var(--font-primary) !important;
    }

    /* 라디오 버튼 스타일링 */
    .stRadio {
        font-family: var(--font-primary) !important;
    }

    /* 슬라이더 스타일링 */
    .stSlider .st-bz {
        background: var(--primary-blue) !important;
    }

    /* 프로그레스 바 */
    .stProgress .st-bs {
        background: var(--primary-blue) !important;
    }

    /* 성공 메시지 */
    .stSuccess {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%) !important;
        border: 1px solid var(--success-green) !important;
        border-radius: var(--radius-md) !important;
        padding: var(--spacing-md) !important;
        font-family: var(--font-primary) !important;
    }

    /* 에러 메시지 */
    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%) !important;
        border: 1px solid #EF4444 !important;
        border-radius: var(--radius-md) !important;
        padding: var(--spacing-md) !important;
        font-family: var(--font-primary) !important;
    }

    /* 경고 메시지 */
    .stWarning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%) !important;
        border: 1px solid #F59E0B !important;
        border-radius: var(--radius-md) !important;
        padding: var(--spacing-md) !important;
        font-family: var(--font-primary) !important;
    }

    /* 정보 메시지 */
    .stInfo {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%) !important;
        border: 1px solid var(--primary-blue) !important;
        border-radius: var(--radius-md) !important;
        padding: var(--spacing-md) !important;
        font-family: var(--font-primary) !important;
    }

    /* 확장 가능한 섹션 */
    .streamlit-expanderHeader {
        background: var(--glass-bg) !important;
        border-radius: var(--radius-md) !important;
        font-family: var(--font-primary) !important;
        font-weight: 600 !important;
        padding: var(--spacing-md) !important;
        border: 1px solid var(--glass-border) !important;
    }

    /* 데이터프레임 스타일링 */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: var(--radius-md) !important;
        padding: var(--spacing-md) !important;
        box-shadow: var(--shadow-md) !important;
    }

    /* 메트릭 스타일링 */
    .metric-container {
        background: var(--card-gradient) !important;
        border-radius: var(--radius-lg) !important;
        padding: var(--spacing-md) !important;
        box-shadow: var(--shadow-md) !important;
        text-align: center !important;
    }

    /* 로딩 스피너 */
    .stSpinner {
        background: var(--hero-gradient) !important;
        border-radius: 50% !important;
    }

    /* 툴팁 스타일링 */
    .stTooltipIcon {
        color: var(--primary-blue) !important;
    }

    /* 테이블 헤더 */
    .stDataFrame th {
        background: var(--primary-blue) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: var(--spacing-sm) !important;
    }

    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: var(--spacing-md) var(--spacing-sm);
        }

        h1 {
            font-size: 2rem !important;
        }

        .stButton button {
            width: 100% !important;
            padding: 16px !important;
            font-size: 16px !important;
        }
    }

    /* 다크 테마 대응 */
    @media (prefers-color-scheme: dark) {
        :root {
            --dark-gray: #F9FAFB;
            --mid-gray: #D1D5DB;
            --light-gray: #1F2937;
        }

        .stApp {
            background: linear-gradient(135deg, #1e3a8a 0%, #581c87 100%);
        }
    }

    /* 커스텀 애니메이션 */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }

    /* 생성 중 애니메이션 */
    .generating {
        animation: pulse 2s infinite;
    }

    /* 페이드 인 효과 */
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }

    /* 스크롤바 커스텀 */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-sm);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--primary-blue);
        border-radius: var(--radius-sm);
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-purple);
    }
</style>
"""

# 추가 JavaScript 효과
MODERN_JS = """
<script>
// 동적 로딩 텍스트
const loadingTexts = [
    "AI가 영상 대본을 생성 중입니다...",
    "창의적인 키워드를 찾고 있습니다...",
    "완벽한 영상 소재를 수집 중입니다...",
    "최고의 결과를 위해 처리 중입니다...",
    "거의 완료되었습니다..."
];

function updateLoadingText() {
    const loadingElements = document.querySelectorAll('.stSpinner');
    loadingElements.forEach(element => {
        const randomText = loadingTexts[Math.floor(Math.random() * loadingTexts.length)];
        if (element.nextElementSibling) {
            element.nextElementSibling.textContent = randomText;
        }
    });
}

// 페이지 로드 시 애니메이션 효과
document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('.element-container');
    elements.forEach((element, index) => {
        element.style.animationDelay = `${index * 0.1}s`;
        element.classList.add('fade-in');
    });

    // 로딩 텍스트 업데이트
    setInterval(updateLoadingText, 3000);
});

// 버튼 클릭 피드백
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'BUTTON') {
        e.target.style.transform = 'scale(0.95)';
        setTimeout(() => {
            e.target.style.transform = '';
        }, 150);
    }
});
</script>
"""
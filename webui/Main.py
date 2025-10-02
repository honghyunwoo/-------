import os
import platform
import sys
from uuid import uuid4

import streamlit as st
from loguru import logger

# Add the root directory of the project to the system path to allow importing modules from the project
root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)
    logger.debug(f"Root directory added to sys.path: {root_dir}")

from app.config import config
from app.models.schema import (
    MaterialInfo,
    VideoAspect,
    VideoConcatMode,
    VideoParams,
    VideoTransitionMode,
)
from app.models.schema import TemplateCreate, UserCreate, UserLogin
from app.services import llm, voice
from app.services import task as tm
from app.utils import utils
from app.services import auth as auth_service
from app.config.logging import setup_logging

st.set_page_config(
    page_title="올빼미 AI 영상 스튜디오",
    page_icon="🦉",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get help": "https://owl-studio.kr/help",
        "About": "# 🦉 올빼미 AI 영상 스튜디오\n밤새우며 만드는 완벽한 영상\n\n"
        "AI가 24시간 함께 영상을 만들어주는 스튜디오입니다. "
        "키워드만 입력하면 전문가급 품질의 영상을 몇 분 만에 완성할 수 있습니다.\n\n"
        "🌙 24시간 창작 가능\n🎬 전문가급 퀄리티\n🚀 빠른 제작 (3분 완성)\n💡 창의적 AI 파트너",
    },
)

# --- Authentication State ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None

# 현대적인 스타일 정의
modern_css = """
<style>
    /* 구글 폰트 임포트 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

    /* CSS 변수 정의 */
    :root {
        --primary-blue: #2563EB;
        --accent-purple: #7C3AED;
        --success-green: #059669;
        --dark-gray: #1F2937;
        --mid-gray: #6B7280;
        --light-gray: #F9FAFB;
        --white: #FFFFFF;
        --hero-gradient: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%);
        --glass-bg: rgba(255, 255, 255, 0.15);
        --glass-border: rgba(255, 255, 255, 0.2);
        --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        --glass-blur: blur(8px);
        --font-primary: 'Inter', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* 전체 앱 스타일링 */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: var(--font-primary);
    }

    /* 메인 컨테이너 */
    .main .block-container {
        padding: 2rem 1.5rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    /* 타이틀 스타일링 */
    h1 {
        font-family: var(--font-primary) !important;
        font-weight: 700 !important;
        background: var(--hero-gradient) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin-bottom: 2rem !important;
        padding-top: 0 !important;
        font-size: 2.5rem !important;
        letter-spacing: -0.025em !important;
    }

    /* 서브헤딩 스타일 */
    h2, h3 {
        font-family: var(--font-primary) !important;
        font-weight: 600 !important;
        color: var(--dark-gray) !important;
        margin: 1.5rem 0 1rem 0 !important;
    }

    /* 카드 스타일 (벤토 그리드) */
    .element-container {
        background: var(--glass-bg);
        backdrop-filter: var(--glass-blur);
        border-radius: 16px;
        border: 1px solid var(--glass-border);
        box-shadow: var(--glass-shadow);
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }

    .element-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
    }

    /* 입력 필드 스타일링 */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox select {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 2px solid transparent !important;
        border-radius: 12px !important;
        font-family: var(--font-primary) !important;
        font-size: 14px !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05) !important;
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
        background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        font-family: var(--font-primary) !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1) !important;
        cursor: pointer !important;
        min-height: 44px !important;
    }

    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1) !important;
        filter: brightness(110%) !important;
    }

    /* 프라이머리 버튼 */
    .stButton[data-testid="baseButton-primaryFormSubmit"] button {
        background: var(--hero-gradient) !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 16px 32px !important;
        border-radius: 16px !important;
        min-height: 56px !important;
    }

    /* 확장 가능한 섹션 */
    .streamlit-expanderHeader {
        background: var(--glass-bg) !important;
        border-radius: 12px !important;
        font-family: var(--font-primary) !important;
        font-weight: 600 !important;
        padding: 1.5rem !important;
        border: 1px solid var(--glass-border) !important;
    }

    /* 성공/에러 메시지 */
    .stSuccess {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%) !important;
        border: 1px solid var(--success-green) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        font-family: var(--font-primary) !important;
    }

    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%) !important;
        border: 1px solid #EF4444 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        font-family: var(--font-primary) !important;
    }

    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1.5rem 1rem;
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
        border-radius: 8px;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--primary-blue);
        border-radius: 8px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-purple);
    }
</style>
"""

def setup_language_selector(locales):
    display_languages = []
    selected_index = 0
    for i, code in enumerate(locales.keys()):
        display_languages.append(f"{code} - {locales[code].get('Language')}")
        if code == st.session_state.get("ui_language", ""):
            selected_index = i

    selected_language = st.selectbox(
        "Language / Language",
        options=display_languages,
        index=selected_index,
        key="top_language_selector",
        label_visibility="collapsed",
    )
    if selected_language:
        code = selected_language.split(" - ")[0].strip()
        st.session_state["ui_language"] = code
        config.ui["language"] = code

# --- App Setup ---
setup_logging()
st.markdown(modern_css, unsafe_allow_html=True)

font_dir = os.path.join(root_dir, "resource", "fonts")
song_dir = os.path.join(root_dir, "resource", "songs")
i18n_dir = os.path.join(root_dir, "webui", "i18n")
config_file = os.path.join(root_dir, "webui", ".streamlit", "webui.toml")
system_locale = utils.get_system_locale()

if "video_subject" not in st.session_state:
    st.session_state["video_subject"] = ""
if "video_script" not in st.session_state:
    st.session_state["video_script"] = ""
if "video_terms" not in st.session_state:
    st.session_state["video_terms"] = ""
if "ui_language" not in st.session_state:
    st.session_state["ui_language"] = config.ui.get("language", system_locale)

locales = utils.load_locales(i18n_dir)

title_col, lang_col = st.columns([3, 1])

with title_col:
    st.title("🦉 올빼미 AI 영상 스튜디오")
with lang_col:
    setup_language_selector(locales)

support_locales = [
    "zh-CN",
    "zh-HK",
    "zh-TW",
    "de-DE",
    "en-US",
    "fr-FR",
    "vi-VN",
    "th-TH",
]


def get_all_fonts():
    fonts = []
    for root, dirs, files in os.walk(font_dir):
        for file in files:
            if file.endswith(".ttf") or file.endswith(".ttc"):
                fonts.append(file)
    fonts.sort()
    return fonts


def get_all_songs():
    songs = []
    for root, dirs, files in os.walk(song_dir):
        for file in files:
            if file.endswith(".mp3"):
                songs.append(file)
    return songs


def open_task_folder(task_id):
    try:
        sys = platform.system()
        path = os.path.join(root_dir, "storage", "tasks", task_id)
        if os.path.exists(path):
            if sys == "Windows":
                os.system(f"start {path}")
            if sys == "Darwin":
                os.system(f"open {path}")
    except Exception as e:
        logger.error(e)


def scroll_to_bottom():
    js = """
    <script>
        console.log("scroll_to_bottom");
        function scroll(dummy_var_to_force_repeat_execution){
            var sections = parent.document.querySelectorAll('section.main');
            console.log(sections);
            for(let index = 0; index<sections.length; index++) {
                sections[index].scrollTop = sections[index].scrollHeight;
            }
        }
        scroll(1);
    </script>
    """
    st.components.v1.html(js, height=0, width=0)

def show_login_page():
    st.title("🦉 올빼미 AI 영상 스튜디오 로그인")

    with st.form("login_form"):
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인")

        if submitted:
            try:
                # This is a placeholder for a real API call
                # In a real app, you would call your FastAPI backend
                # e.g., response = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
                # For this example, we'll simulate a successful login
                
                # Placeholder for user object
                st.session_state["authenticated"] = True
                st.session_state["user"] = {"email": email, "id": 1} # Mock user
                st.experimental_rerun()
            except Exception as e:
                st.error(f"로그인 실패: {e}")

def show_register_page():
    st.title("🦉 올빼미 AI 영상 스튜디오 회원가입")

    with st.form("register_form"):
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        confirm_password = st.text_input("비밀번호 확인", type="password")
        submitted = st.form_submit_button("회원가입")

        if submitted:
            if password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                try:
                    # Placeholder for API call to registration endpoint
                    st.success("회원가입 성공! 이메일을 확인하여 계정을 활성화해주세요.")
                except Exception as e:
                    st.error(f"회원가입 실패: {e}")

def show_auth_page():
    st.markdown(modern_css, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("") # Spacer
        st.write("") # Spacer
        
        auth_tab1, auth_tab2 = st.tabs(["로그인", "회원가입"])

        with auth_tab1:
            show_login_page()

        with auth_tab2:
            show_register_page()

# --- Main App Logic ---
if not st.session_state["authenticated"]:
    show_auth_page()
    st.stop()

# If authenticated, show the main app
def show_history_page():
    st.subheader("🎞️ 영상 생성 히스토리")
    
    # Placeholder for API call to fetch history
    # In a real app: history_items = requests.get(f"{API_URL}/history", headers={"Authorization": f"Bearer {token}"}).json()
    history_items = [
        {"video_subject": "AI의 미래", "created_at": "2024-10-04T10:00:00", "video_path": "path/to/video1.mp4", "task_id": "task1"},
        {"video_subject": "성공하는 사람들의 5가지 습관", "created_at": "2024-10-03T15:30:00", "video_path": "path/to/video2.mp4", "task_id": "task2"},
    ] # Mock data

    if not history_items:
        st.info("아직 생성된 영상이 없습니다.")
        return

    for item in history_items:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{item['video_subject']}**")
        with col2:
            st.write(f"_{item['created_at']}_")
        with col3:
            # In a real app, this would trigger a download from the backend API
            st.download_button("다시 다운로드", data=b"", file_name=os.path.basename(item['video_path']), mime="video/mp4", key=f"download_{item['task_id']}")


def main_app():
    st.markdown(modern_css, unsafe_allow_html=True)

    font_dir = os.path.join(root_dir, "resource", "fonts")
    song_dir = os.path.join(root_dir, "resource", "songs")
    i18n_dir = os.path.join(root_dir, "webui", "i18n")
    config_file = os.path.join(root_dir, "webui", ".streamlit", "webui.toml")
    system_locale = utils.get_system_locale()


    if "video_subject" not in st.session_state:
        st.session_state["video_subject"] = ""
    if "video_script" not in st.session_state:
        st.session_state["video_script"] = ""
    if "video_terms" not in st.session_state:
        st.session_state["video_terms"] = ""
    if "ui_language" not in st.session_state:
        st.session_state["ui_language"] = config.ui.get("language", system_locale)

    locales = utils.load_locales(i18n_dir)

    title_col, lang_col, logout_col = st.columns([3, 1, 0.5])

    with title_col:
        st.title("🦉 올빼미 AI 영상 스튜디오")
    
    with logout_col:
        st.write("") # Spacer
        if st.button("로그아웃"):
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.experimental_rerun()

    # Display user's current plan and credits
    user_info = st.session_state.get("user")
    if user_info:
        plan = user_info.get('subscription_plan', 'free').capitalize()
        credits = user_info.get('credits', 0)
        credits_display = "무제한" if credits == -1 else f"{credits}개"
        st.sidebar.info(f"**{user_info.get('email')}**\n\n**플랜**: {plan}\n\n**남은 크레딧**: {credits_display}")
        st.sidebar.page_link("public/payment.html", label="플랜 업그레이드", icon="🚀")

    main_tab, history_tab = st.tabs(["🎬 영상 제작", "🗂️ 히스토리"])

    with main_tab:
        show_main_generator_ui()

    with history_tab:
        show_history_page()

locales = utils.load_locales(i18n_dir)


def tr(key):
    loc = locales.get(st.session_state["ui_language"], {})
    return loc.get("Translation", {}).get(key, key)


def show_main_generator_ui():
if not config.app.get("hide_config", False):
    with st.expander(tr("Basic Settings"), expanded=False):
        config_panels = st.columns(3)
        left_config_panel = config_panels[0]
        middle_config_panel = config_panels[1]
        right_config_panel = config_panels[2]

        with left_config_panel:
            hide_config = st.checkbox(
                tr("Hide Basic Settings"), value=config.app.get("hide_config", False)
            )
            config.app["hide_config"] = hide_config

            hide_log = st.checkbox(
                tr("Hide Log"), value=config.ui.get("hide_log", False)
            )
            config.ui["hide_log"] = hide_log


        with middle_config_panel:
            st.write(tr("LLM Settings"))
            llm_providers = [
                "OpenAI",
                "Moonshot",
                "Azure",
                "Qwen",
                "DeepSeek",
                "Gemini",
                "Ollama",
                "G4f",
                "OneAPI",
                "Cloudflare",
                "ERNIE",
                "Pollinations",
            ]
            saved_llm_provider = config.app.get("llm_provider", "OpenAI").lower()
            saved_llm_provider_index = 0
            for i, provider in enumerate(llm_providers):
                if provider.lower() == saved_llm_provider:
                    saved_llm_provider_index = i
                    break

            llm_provider = st.selectbox(
                tr("LLM Provider"),
                options=llm_providers,
                index=saved_llm_provider_index,
            )
            llm_helper = st.container()
            llm_provider = llm_provider.lower()
            config.app["llm_provider"] = llm_provider

            llm_api_key = config.app.get(f"{llm_provider}_api_key", "")
            llm_secret_key = config.app.get(
                f"{llm_provider}_secret_key", ""
            )  # only for baidu ernie
            llm_base_url = config.app.get(f"{llm_provider}_base_url", "")
            llm_model_name = config.app.get(f"{llm_provider}_model_name", "")
            llm_account_id = config.app.get(f"{llm_provider}_account_id", "")

            tips = ""
            if llm_provider == "ollama":
                if not llm_model_name:
                    llm_model_name = "qwen:7b"
                if not llm_base_url:
                    llm_base_url = "http://localhost:11434/v1"

                with llm_helper:
                    tips = """
                            - **API Key**: 아무 값이나 입력하세요 (예: 123).
                            - **Base Url**: 보통 `http://localhost:11434/v1` 입니다.
                                - 다른 컴퓨터에 있다면, `Ollama`가 설치된 기기의 IP 주소를 입력하세요.
                                - Docker로 배포했다면, `http://host.docker.internal:11434/v1`를 권장합니다.
                            - **Model Name**: `ollama list` 명령어로 확인 가능합니다 (예: `qwen:7b`).
                            """

            if llm_provider == "openai":
                if not llm_model_name:
                    llm_model_name = "gpt-3.5-turbo"
                with llm_helper:
                    tips = """
                            > Requires VPN with global traffic mode
                            - **API Key**: [Click to apply](https://platform.openai.com/api-keys)
                            - **Base Url**: Can be left empty
                            - **Model Name**: Fill in authorized model，[Click to view model list](https://platform.openai.com/settings/organization/limits)
                            """

            if llm_provider == "moonshot":
                if not llm_model_name:
                    llm_model_name = "moonshot-v1-8k"
                with llm_helper:
                    tips = """
                            - **API Key**: 여기서 발급
                            - **Base Url**: `https://api.moonshot.cn/v1`로 고정됩니다.
                            - **Model Name**: 예: `moonshot-v1-8k`. 모델 목록 보기
                            """
            if llm_provider == "oneapi":
                if not llm_model_name:
                    llm_model_name = (
                        "claude-3-5-sonnet-20240620"
                    )
                with llm_helper:
                    tips = f"""
                        - **API Key**: OneAPI에서 발급받은 키를 입력하세요.
                        - **Base Url**: OneAPI의 Base URL을 입력하세요.
                        - **Model Name**: 사용하려는 모델명을 입력하세요 (예: `claude-3-5-sonnet-20240620`).
                        """

            if llm_provider == "qwen":
                if not llm_model_name:
                    llm_model_name = "qwen-max"
                with llm_helper:
                    tips = """
                            - **API Key**: 여기서 발급
                            - **Base Url**: 비워두세요.
                            - **Model Name**: 예: `qwen-max`. 모델 목록 보기
                            """

            if llm_provider == "g4f":
                if not llm_model_name:
                    llm_model_name = "gpt-3.5-turbo"
                with llm_helper:
                    tips = """
                            > [GitHubOpen source project](https://github.com/xtekky/gpt4free)，Free GPT models but less stable
                            - **API Key**: Fill in anything, e.g. 123
                            - **Base Url**: Leave empty
                            - **Model Name**: e.g. gpt-3.5-turbo，[Click to view model list](https://github.com/xtekky/gpt4free/blob/main/g4f/models.py
                            """
            if llm_provider == "azure":
                with llm_helper:
                    tips = """
                            > [Click to see how to deploy](https://learn.microsoft.com/zh-cn/azure/ai-services/openai/how-to/create-resource)
                            - **API Key**: [Create in Azure portal](https://portal.azure.com/
                            - **Base Url**: Leave empty
                            - **Model Name**: Fill in your deployment name
                            """

            if llm_provider == "gemini":
                if not llm_model_name:
                    llm_model_name = "gemini-1.0-pro"

                with llm_helper:
                    tips = """
                            - **API Key**: 여기서 발급
                            - **Base Url**: 비워두세요.
                            - **Model Name**: 예: `gemini-1.0-pro`
                            """

            if llm_provider == "deepseek":
                if not llm_model_name:
                    llm_model_name = "deepseek-chat"
                if not llm_base_url:
                    llm_base_url = "https://api.deepseek.com"
                with llm_helper:
                    tips = """
                            - **API Key**: [Click to apply](https://platform.deepseek.com/api_keys)
                            - **Base Url**: Fixed as https://api.deepseek.com
                            - **Model Name**: Fixed as deepseek-chat
                            """

            if llm_provider == "ernie":
                with llm_helper:
                    tips = """
                            - **API Key**: [Click to apply](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
                            - **Secret Key**: [Click to apply](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application)
                            - **Base Url**: 填写 **请求地址** [点击查看文档](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/jlil56u11
                            """

            if llm_provider == "pollinations":
                if not llm_model_name:
                    llm_model_name = "default"
                with llm_helper:
                    tips = """
                            ##### Pollinations AI Configuration
                            - **API Key**: Optional - Leave empty for public access
                            - **Base Url**: Default is https://text.pollinations.ai/openai
                            - **Model Name**: Use 'openai-fast' or specify a model name
                            """

            if tips and config.ui["language"] == "zh":
                st.warning(
                    "Chinese users recommend **DeepSeek** 或 **Moonshot** 作为大模型提供商\n- Accessible in China without VPN \n- Free credits on registration"
                )
                st.info(tips)

            st_llm_api_key = st.text_input(
                tr("API Key"), value=llm_api_key, type="password"
            )
            st_llm_base_url = st.text_input(tr("Base Url"), value=llm_base_url)
            st_llm_model_name = ""
            if llm_provider != "ernie":
                st_llm_model_name = st.text_input(
                    tr("Model Name"),
                    value=llm_model_name,
                    key=f"{llm_provider}_model_name_input",
                )
                if st_llm_model_name:
                    config.app[f"{llm_provider}_model_name"] = st_llm_model_name
            else:
                st_llm_model_name = None

            if st_llm_api_key:
                config.app[f"{llm_provider}_api_key"] = st_llm_api_key
            if st_llm_base_url:
                config.app[f"{llm_provider}_base_url"] = st_llm_base_url
            if st_llm_model_name:
                config.app[f"{llm_provider}_model_name"] = st_llm_model_name
            if llm_provider == "ernie":
                st_llm_secret_key = st.text_input(
                    tr("Secret Key"), value=llm_secret_key, type="password"
                )
                config.app[f"{llm_provider}_secret_key"] = st_llm_secret_key

            if llm_provider == "cloudflare":
                st_llm_account_id = st.text_input(
                    tr("Account ID"), value=llm_account_id
                )
                if st_llm_account_id:
                    config.app[f"{llm_provider}_account_id"] = st_llm_account_id

        with right_config_panel:

            def get_keys_from_config(cfg_key):
                api_keys = config.app.get(cfg_key, [])
                if isinstance(api_keys, str):
                    api_keys = [api_keys]
                api_key = ", ".join(api_keys)
                return api_key

            def save_keys_to_config(cfg_key, value):
                value = value.replace(" ", "")
                if value:
                    config.app[cfg_key] = value.split(",")

            st.write(tr("Video Source Settings"))

            pexels_api_key = get_keys_from_config("pexels_api_keys")
            pexels_api_key = st.text_input(
                tr("Pexels API Key"), value=pexels_api_key, type="password"
            )
            save_keys_to_config("pexels_api_keys", pexels_api_key)

            pixabay_api_key = get_keys_from_config("pixabay_api_keys")
            pixabay_api_key = st.text_input(
                tr("Pixabay API Key"), value=pixabay_api_key, type="password"
            )
            save_keys_to_config("pixabay_api_keys", pixabay_api_key)

llm_provider = config.app.get("llm_provider", "").lower()
panel = st.columns(3)
left_panel = panel[0]
middle_panel = panel[1]
right_panel = panel[2]

# config.toml에서 기본값들을 가져와서 VideoParams 초기화
params = VideoParams(
    video_subject="",
    voice_name=config.ui.get("voice_name", ""),
    font_name=config.ui.get("font_name", "STHeitiMedium.ttc"),
    text_fore_color=config.ui.get("text_fore_color", "#FFFFFF"),
    font_size=config.ui.get("font_size", 60)
)
uploaded_files = []

with left_panel:
    with st.container(border=True):
        st.write(tr("Video Script Settings"))
        params.video_subject = st.text_input(
            tr("Video Subject"),
            value=st.session_state["video_subject"],
            key="video_subject_input",
        ).strip()

        video_languages = [
            (tr("Auto Detect"), ""),
        ]
        for code in support_locales:
            video_languages.append((code, code))

        selected_index = st.selectbox(
            tr("Script Language"),
            index=0,
            options=range(
                len(video_languages)
            ),  # Use the index as the internal option value
            format_func=lambda x: video_languages[x][
                0
            ],  # The label is displayed to the user
        )
        params.video_language = video_languages[selected_index][1]

        if st.button(
            tr("Generate Video Script and Keywords"), key="auto_generate_script"
        ):
            with st.spinner(tr("Generating Video Script and Keywords")):
                script = llm.generate_script(
                    video_subject=params.video_subject, language=params.video_language
                )
                terms = llm.generate_terms(params.video_subject, script)
                if "Error: " in script:
                    st.error(tr(script))
                elif "Error: " in terms:
                    st.error(tr(terms))
                else:
                    st.session_state["video_script"] = script
                    st.session_state["video_terms"] = ", ".join(terms)
        params.video_script = st.text_area(
            tr("Video Script"), value=st.session_state["video_script"], height=280
        )
        if st.button(tr("Generate Video Keywords"), key="auto_generate_terms"):
            if not params.video_script:
                st.error(tr("Please Enter the Video Subject"))
                st.stop()

            with st.spinner(tr("Generating Video Keywords")):
                terms = llm.generate_terms(params.video_subject, params.video_script)
                if "Error: " in terms:
                    st.error(tr(terms))
                else:
                    st.session_state["video_terms"] = ", ".join(terms)

        params.video_terms = st.text_area(
            tr("Video Keywords"), value=st.session_state["video_terms"]
        )

with middle_panel:
    with st.container(border=True):
        st.write(tr("Video Settings"))
        video_concat_modes = [
            (tr("Sequential"), "sequential"),
            (tr("Random"), "random"),
        ]
        video_sources = [
            (tr("Pexels"), "pexels"),
            (tr("Pixabay"), "pixabay"),
            (tr("Local file"), "local"),
            (tr("TikTok"), "douyin"),
            (tr("Bilibili"), "bilibili"),
            (tr("Xiaohongshu"), "xiaohongshu"),
        ]

        saved_video_source_name = config.app.get("video_source", "pexels")
        saved_video_source_index = [v[1] for v in video_sources].index(
            saved_video_source_name
        )

        selected_index = st.selectbox(
            tr("Video Source"),
            options=range(len(video_sources)),
            format_func=lambda x: video_sources[x][0],
            index=saved_video_source_index,
        )
        params.video_source = video_sources[selected_index][1]
        config.app["video_source"] = params.video_source

        if params.video_source == "local":
            uploaded_files = st.file_uploader(
                "Upload Local Files",
                type=["mp4", "mov", "avi", "flv", "mkv", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
            )

        selected_index = st.selectbox(
            tr("Video Concat Mode"),
            index=1,
            options=range(
                len(video_concat_modes)
            ),  # Use the index as the internal option value
            format_func=lambda x: video_concat_modes[x][
                0
            ],  # The label is displayed to the user
        )
        params.video_concat_mode = VideoConcatMode(
            video_concat_modes[selected_index][1]
        )

        video_transition_modes = [
            (tr("None"), VideoTransitionMode.none.value),
            (tr("Shuffle"), VideoTransitionMode.shuffle.value),
            (tr("FadeIn"), VideoTransitionMode.fade_in.value),
            (tr("FadeOut"), VideoTransitionMode.fade_out.value),
            (tr("SlideIn"), VideoTransitionMode.slide_in.value),
            (tr("SlideOut"), VideoTransitionMode.slide_out.value),
        ]
        selected_index = st.selectbox(
            tr("Video Transition Mode"),
            options=range(len(video_transition_modes)),
            format_func=lambda x: video_transition_modes[x][0],
            index=0,
        )
        params.video_transition_mode = VideoTransitionMode(
            video_transition_modes[selected_index][1]
        )

        video_aspect_ratios = [
            (tr("Portrait"), VideoAspect.portrait.value),
            (tr("Landscape"), VideoAspect.landscape.value),
        ]
        selected_index = st.selectbox(
            tr("Video Ratio"),
            options=range(
                len(video_aspect_ratios)
            ),  # Use the index as the internal option value
            format_func=lambda x: video_aspect_ratios[x][
                0
            ],  # The label is displayed to the user
        )
        params.video_aspect = VideoAspect(video_aspect_ratios[selected_index][1])

        params.video_clip_duration = st.selectbox(
            tr("Clip Duration"), options=[2, 3, 4, 5, 6, 7, 8, 9, 10], index=1
        )
        params.video_count = st.selectbox(
            tr("Number of Videos Generated Simultaneously"),
            options=[1, 2, 3, 4, 5],
            index=0,
        )
    with st.container(border=True):
        st.write(tr("Audio Settings"))

        tts_servers = [
            ("azure-tts-v1", "Azure TTS V1"),
            ("azure-tts-v2", "Azure TTS V2"),
            ("siliconflow", "SiliconFlow TTS"),
        ]

        saved_tts_server = config.ui.get("tts_server", "azure-tts-v1")
        saved_tts_server_index = 0
        for i, (server_value, _) in enumerate(tts_servers):
            if server_value == saved_tts_server:
                saved_tts_server_index = i
                break

        selected_tts_server_index = st.selectbox(
            tr("TTS Servers"),
            options=range(len(tts_servers)),
            format_func=lambda x: tts_servers[x][1],
            index=saved_tts_server_index,
        )

        selected_tts_server = tts_servers[selected_tts_server_index][0]
        config.ui["tts_server"] = selected_tts_server

        filtered_voices = []

        if selected_tts_server == "siliconflow":
            filtered_voices = voice.get_siliconflow_voices()
        else:
            all_voices = voice.get_all_azure_voices(filter_locals=None)

            for v in all_voices:
                if selected_tts_server == "azure-tts-v2":
                    if "V2" in v:
                        filtered_voices.append(v)
                else:
                    if "V2" not in v:
                        filtered_voices.append(v)

        friendly_names = {
            v: v.replace("Female", tr("Female"))
            .replace("Male", tr("Male"))
            .replace("Neural", "")
            for v in filtered_voices
        }

        if friendly_names:
            # Determine the default selection index
            saved_voice_name = config.ui.get("voice_name", "")
            try:
                # Try to find the index of the saved voice name
                saved_voice_name_index = list(friendly_names.keys()).index(saved_voice_name)
            except ValueError:
                # If not found, try to find a voice matching the UI language
                saved_voice_name_index = 0 # Default to the first voice
                ui_lang_code = st.session_state.get("ui_language", "en").lower().split('-')[0]
                for i, voice_key in enumerate(friendly_names.keys()):
                    if voice_key.lower().startswith(ui_lang_code):
                        saved_voice_name_index = i
                        break

            selected_friendly_name = st.selectbox(
                tr("Speech Synthesis"),
                options=list(friendly_names.values()),
                index=saved_voice_name_index,
            )

            # Get the actual voice name from the selected friendly name
            selected_voice_name = list(friendly_names.keys())[list(friendly_names.values()).index(selected_friendly_name)]
            params.voice_name = selected_voice_name
            config.ui["voice_name"] = selected_voice_name
        else:
            st.warning(
                tr(
                    "No voices available for the selected TTS server. Please select another server."
                )
            )
            params.voice_name = ""
            config.ui["voice_name"] = ""

        if params.voice_name and st.button(tr("Play Voice")):
            play_content = params.video_subject
            if not play_content:
                play_content = params.video_script
            if not play_content:
                play_content = tr("Voice Example")
            with st.spinner(tr("Synthesizing Voice")):
                temp_dir = utils.storage_dir("temp", create=True)
                audio_file = os.path.join(temp_dir, f"tmp-voice-{str(uuid4())}.mp3")
                sub_maker = voice.tts(
                    text=play_content,
                    voice_name=params.voice_name,
                    voice_rate=params.voice_rate,
                    voice_file=audio_file,
                    voice_volume=params.voice_volume,
                )
                # if the voice file generation failed, try again with a default content.
                if not sub_maker:
                    play_content = "This is a example voice. if you hear this, the voice synthesis failed with the original content."
                    sub_maker = voice.tts(
                        text=play_content,
                        voice_name=params.voice_name,
                        voice_rate=params.voice_rate,
                        voice_file=audio_file,
                        voice_volume=params.voice_volume,
                    )

                if sub_maker and os.path.exists(audio_file):
                    st.audio(audio_file, format="audio/mp3")
                    if os.path.exists(audio_file):
                        os.remove(audio_file)

        if selected_tts_server == "azure-tts-v2" or ( 
            params.voice_name and voice.is_azure_v2_voice(params.voice_name)
        ):
            saved_azure_speech_region = config.azure.get("speech_region", "")
            saved_azure_speech_key = config.azure.get("speech_key", "")
            azure_speech_region = st.text_input(
                tr("Speech Region"),
                value=saved_azure_speech_region,
                key="azure_speech_region_input",
            )
            azure_speech_key = st.text_input(
                tr("Speech Key"),
                value=saved_azure_speech_key,
                type="password",
                key="azure_speech_key_input",
            )
            config.azure["speech_region"] = azure_speech_region
            config.azure["speech_key"] = azure_speech_key

        if selected_tts_server == "siliconflow" or ( 
            params.voice_name and voice.is_siliconflow_voice(params.voice_name)
        ):
            saved_siliconflow_api_key = config.siliconflow.get("api_key", "")

            siliconflow_api_key = st.text_input(
                tr("SiliconFlow API Key"),
                value=saved_siliconflow_api_key,
                type="password",
                key="siliconflow_api_key_input",
            )

            st.info(
                tr("SiliconFlow TTS Settings")
                + ":\n"
                + "- "
                + tr("Speed: Range [0.25, 4.0], default is 1.0")
                + "\n"
                + "- "
                + tr("Volume: Uses Speech Volume setting, default 1.0 maps to gain 0")
            )

            config.siliconflow["api_key"] = siliconflow_api_key

        params.voice_volume = st.selectbox(
            tr("Speech Volume"),
            options=[0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0],
            index=2,
        )

        params.voice_rate = st.selectbox(
            tr("Speech Rate"),
            options=[0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.0],
            index=2,
        )

        bgm_options = [
            (tr("No Background Music"), ""),
            (tr("Random Background Music"), "random"),
            (tr("Custom Background Music"), "custom"),
        ]
        selected_index = st.selectbox(
            tr("Background Music"),
            index=1,
            options=range(
                len(bgm_options)
            ),  # Use the index as the internal option value
            format_func=lambda x: bgm_options[x][
                0
            ],  # The label is displayed to the user
        )
        # Get the selected background music type
        params.bgm_type = bgm_options[selected_index][1]

        # Show or hide components based on the selection
        if params.bgm_type == "custom":
            custom_bgm_file = st.text_input(
                tr("Custom Background Music File"), key="custom_bgm_file_input"
            )
            if custom_bgm_file and os.path.exists(custom_bgm_file):
                params.bgm_file = custom_bgm_file
        params.bgm_volume = st.selectbox(
            tr("Background Music Volume"),
            options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            index=2,
        )

with right_panel:
    with st.container(border=True):
        st.write(tr("Subtitle Settings"))
        params.subtitle_enabled = st.checkbox(tr("Enable Subtitles"), value=True)
        font_names = get_all_fonts()
        saved_font_name = config.ui.get("font_name", "MicrosoftYaHeiBold.ttc")
        saved_font_name_index = 0
        if saved_font_name in font_names:
            saved_font_name_index = font_names.index(saved_font_name)
        params.font_name = st.selectbox(
            tr("Font"), font_names, index=saved_font_name_index
        )
        config.ui["font_name"] = params.font_name

        subtitle_positions = [
            (tr("Top"), "top"),
            (tr("Center"), "center"),
            (tr("Bottom"), "bottom"),
            (tr("Custom"), "custom"),
        ]
        selected_index = st.selectbox(
            tr("Position"),
            index=2,
            options=range(len(subtitle_positions)),
            format_func=lambda x: subtitle_positions[x][0],
        )
        params.subtitle_position = subtitle_positions[selected_index][1]

        if params.subtitle_position == "custom":
            custom_position = st.text_input(
                tr("Custom Position (% from top)"),
                value="70.0",
                key="custom_position_input",
            )
            try:
                params.custom_position = float(custom_position)
                if params.custom_position < 0 or params.custom_position > 100:
                    st.error(tr("Please enter a value between 0 and 100"))
            except ValueError:
                st.error(tr("Please enter a valid number"))

        font_cols = st.columns([0.3, 0.7])
        with font_cols[0]:
            saved_text_fore_color = config.ui.get("text_fore_color", "#FFFFFF")
            params.text_fore_color = st.color_picker(
                tr("Font Color"), saved_text_fore_color
            )
            config.ui["text_fore_color"] = params.text_fore_color

        with font_cols[1]:
            saved_font_size = config.ui.get("font_size", 60)
            params.font_size = st.slider(tr("Font Size"), 30, 100, saved_font_size)
            config.ui["font_size"] = params.font_size

        stroke_cols = st.columns([0.3, 0.7])
        with stroke_cols[0]:
            params.stroke_color = st.color_picker(tr("Stroke Color"), "#000000")
        with stroke_cols[1]:
            params.stroke_width = st.slider(tr("Stroke Width"), 0.0, 10.0, 1.5)

    with st.container(border=True):
        st.write("### 템플릿 관리")
        
        # Load templates
        # In a real multi-user app, you'd pass the current user's ID
        user_templates = tm.get_templates(db=st.session_state.db, user_id=1) 
        template_options = {t.id: t.name for t in user_templates}
        
        selected_template_id = st.selectbox(
            "템플릿 불러오기",
            options=[None] + list(template_options.keys()),
            format_func=lambda x: "선택 안함" if x is None else template_options[x]
        )

        if selected_template_id and st.button("템플릿 적용"):
            with st.spinner("템플릿을 불러오는 중..."):
                loaded_template = tm.get_template(db=st.session_state.db, template_id=selected_template_id)
                if loaded_template:
                    # Update params and session_state with loaded template data
                    # This is a simplified example. A full implementation would iterate
                    # over all fields and update them.
                    st.session_state["video_subject"] = loaded_template.video_subject
                    st.session_state["video_script"] = loaded_template.video_script
                    params.font_name = loaded_template.font_name
                    # ... and so on for all other parameters
                    st.success(f"'{loaded_template.name}' 템플릿을 적용했습니다.")
                    st.experimental_rerun()
                else:
                    st.error("템플릿을 불러오는데 실패했습니다.")

        template_name = st.text_input("새 템플릿 이름")
        if st.button("현재 설정을 템플릿으로 저장"):
            if template_name:
                with st.spinner("템플릿 저장 중..."):
                    # Collect current params into a TemplateCreate schema
                    template_data = TemplateCreate(
                        name=template_name,
                        video_subject=params.video_subject,
                        video_script=params.video_script,
                        # ... and so on for all other parameters
                        font_name=params.font_name,
                        font_size=params.font_size,
                        voice_name=params.voice_name,
                    )
                    # In a real app, you'd get the current user
                    tm.create_template(db=st.session_state.db, template=template_data, user=st.session_state.user)
                    st.success(f"'{template_name}' 템플릿을 저장했습니다.")
            else:
                st.warning("템플릿 이름을 입력해주세요.")

start_button = st.button(tr("Generate Video"), use_container_width=True, type="primary")
if start_button:
    config.save_config()
    task_id = str(uuid4())
    if not params.video_subject and not params.video_script:
        st.error(tr("Video Script and Subject Cannot Both Be Empty"))
        scroll_to_bottom()
        st.stop()

    if params.video_source not in ["pexels", "pixabay", "local"]:
        st.error(tr("Please Select a Valid Video Source"))
        scroll_to_bottom()
        st.stop()

    if params.video_source == "pexels" and not config.app.get("pexels_api_keys", ""):
        st.error(tr("Please Enter the Pexels API Key"))
        scroll_to_bottom()
        st.stop()

    if params.video_source == "pixabay" and not config.app.get("pixabay_api_keys", ""):
        st.error(tr("Please Enter the Pixabay API Key"))
        scroll_to_bottom()
        st.stop()

    if uploaded_files:
        local_videos_dir = utils.storage_dir("local_videos", create=True)
        for file in uploaded_files:
            file_path = os.path.join(local_videos_dir, f"{file.file_id}_{file.name}")
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
                m = MaterialInfo()
                m.provider = "local"
                m.url = file_path
                if not params.video_materials:
                    params.video_materials = []
                params.video_materials.append(m)

    log_container = st.empty()
    log_records = []

    def log_received(msg):
        if config.ui.get("hide_log", False):
            return
        with log_container:
            log_records.append(msg)
            st.code("\n".join(log_records))

    logger.add(log_received)

    st.toast(tr("Generating Video"))
    logger.info(tr("Start Generating Video"))
    logger.info(utils.to_json(params))
    scroll_to_bottom()

    result = tm.start(task_id=task_id, params=params)
    if not result or "videos" not in result:
        st.error(tr("Video Generation Failed"))
        logger.error(tr("Video Generation Failed"))
        scroll_to_bottom()
        st.stop()

    video_files = result.get("videos", [])
    st.success(tr("Video Generation Completed"))
    try:
        if video_files:
            player_cols = st.columns(len(video_files) * 2 + 1)
            for i, url in enumerate(video_files):
                player_cols[i * 2 + 1].video(url)
    except Exception:
        pass

    # YouTube Upload Section
    if video_files:
        st.write("---")
        st.write("### 🎬 YouTube에 업로드")
        
        # In a real app, you'd get the current user's ID
        user_id_for_upload = "user_1" 

        yt_title = st.text_input("YouTube 제목", value=params.video_subject)
        yt_description = st.text_area("YouTube 설명", value=params.video_script, height=150)
        yt_tags = st.text_input("YouTube 태그 (쉼표로 구분)", value=",".join(params.video_terms.split(',')[:15]))

        if st.button("YouTube에 업로드 시작"):
            with st.spinner("YouTube에 영상을 업로드하는 중... 이 작업은 시간이 걸릴 수 있습니다."):
                video_id = tm.upload_to_youtube(user_id_for_upload, video_files[0], yt_title, yt_description, yt_tags.split(','))
                if video_id:
                    st.success(f"업로드 성공! 영상 링크: https://www.youtube.com/watch?v={video_id}")
                else:
                    st.error("YouTube 업로드에 실패했습니다. 로그를 확인해주세요.")

    open_task_folder(task_id)
    logger.info(tr("Video Generation Completed"))
    scroll_to_bottom()

    config.save_config()

if __name__ == "__main__":
    main_app()

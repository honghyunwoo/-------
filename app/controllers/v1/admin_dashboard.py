import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="관리자 대시보드",
    page_icon="👑",
    layout="wide",
)

st.title("👑 관리자 대시보드")

# --- Authentication Check ---
if not st.session_state.get("authenticated") or not st.session_state.get(
    "user", {}
).get("is_superuser"):
    st.error("이 페이지에 접근할 권한이 없습니다. 관리자로 로그인해주세요.")
    st.stop()

# Placeholder for API call to fetch stats
# In a real app: stats = requests.get(f"{API_URL}/admin/stats", headers=auth_headers).json()
stats = {
    "total_users": 1250,
    "total_videos_generated": 8743,
    "daily_signups": [
        {"date": "2024-09-20", "count": 15},
        {"date": "2024-09-21", "count": 25},
        {"date": "2024-09-22", "count": 30},
    ],
    "daily_videos": [
        {"date": "2024-09-20", "count": 150},
        {"date": "2024-09-21", "count": 200},
        {"date": "2024-09-22", "count": 250},
    ],
    "plan_distribution": {
        "free": 800,
        "basic": 300,
        "pro": 100,
        "business": 50,
    }
}  # Mock data


st.header("핵심 지표")
col1, col2, col3 = st.columns(3)
col1.metric("총 사용자 수", f"{stats['total_users']:,}")
col2.metric("총 영상 생성 수", f"{stats['total_videos_generated']:,}")
col3.metric(
    "유료 전환율 (추정)",
    f"{( (stats['total_users'] - stats['plan_distribution']['free']) / stats['total_users'] ) * 100:.2f}%",
)

st.header("사용자 및 영상 생성 추이 (최근 30일)")

signup_df = pd.DataFrame(stats["daily_signups"]).set_index("date")
video_df = pd.DataFrame(stats["daily_videos"]).set_index("date")

st.line_chart(signup_df, use_container_width=True)
st.line_chart(video_df, use_container_width=True)


st.header("구독 플랜 분포")
plan_df = pd.DataFrame(
    list(stats["plan_distribution"].items()), columns=["Plan", "User Count"]
).set_index("Plan")
st.bar_chart(plan_df, use_container_width=True)

st.header("최근 사용자 및 활동 (샘플)")
# Placeholder for paginated user/video tables
st.dataframe(
    pd.DataFrame(
        {
            "Email": ["user1@example.com", "user2@example.com"],
            "Plan": ["pro", "free"],
            "Last Active": ["2024-10-04", "2024-10-03"],
        }
    ),
    use_container_width=True,
)
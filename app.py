import streamlit as st
import requests
import os
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="SkillScapes Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    h1 {
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
print (API_BASE_URL)


# Check API connection
def check_api_connection():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


# Sidebar connection status
with st.sidebar:
    st.markdown("### 🔌 API Status")
    if check_api_connection():
        st.success(f"✅ Connected")
        st.caption(f"URL: {API_BASE_URL}")
    else:
        st.error(f"❌ Disconnected")
        st.caption(f"URL: {API_BASE_URL}")
        st.warning("""
        **Start API:**
        ```bash
        uvicorn api:app --port 8000
        ```
        """)

# Home page
st.title("📊 SkillScapes Analytics Dashboard")
st.markdown("### Greek Job Market Intelligence Platform")

st.markdown("""
Welcome to **SkillScapes Analytics** - your comprehensive platform for analyzing the Greek job market.

#### 🎯 Available Features:
- **📈 Jobs**: Job volume and time series analysis
- **💼 Occupations**: Occupation demand tracking and trends
- **🏢 Regions**: Regional job market insights (NUTS2 & Regional Units)
- **🎓 Skills**: Skill demand and categorization
- **🔥 Heatmaps**: Visual comparison across dimensions
- **📊 Job Types**: Employment type distribution and categories

#### 🚀 Getting Started:
Use the sidebar to navigate between different analysis pages. Each page offers interactive visualizations
and filtering options to explore the data.

---
*Data powered by SkillScapes Analytics API v3.0*
""")

# Quick stats
if check_api_connection():
    col1, col2, col3, col4 = st.columns(4)

    try:
        # Total jobs
        response = requests.get(f"{API_BASE_URL}/api/jobs/count")
        if response.status_code == 200:
            data = response.json()
            with col1:
                st.metric("Total Jobs", f"{data.get('total_jobs', 0):,}")

        # Top occupations count
        response = requests.get(f"{API_BASE_URL}/api/occupations/demand", params={"top_n": 100})
        if response.status_code == 200:
            data = response.json()
            with col2:
                st.metric("Occupations Tracked", f"{data.get('count', 0):,}")

        # Regions count
        response = requests.get(f"{API_BASE_URL}/api/regions/jobs", params={"region_level": "nuts2", "top_n": 100})
        if response.status_code == 200:
            data = response.json()
            with col3:
                st.metric("Regions (NUTS2)", f"{data.get('count', 0):,}")

        # Skills count
        response = requests.get(f"{API_BASE_URL}/api/skills/top", params={"top_n": 100})
        if response.status_code == 200:
            data = response.json()
            with col4:
                st.metric("Skills Tracked", f"{data.get('count', 0):,}+")
    except:
        pass

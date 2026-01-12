import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="Skills", page_icon="🎓", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("🎓 Skills Analysis")

# Sidebar
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime(2025, 5, 1, 0, 0, 0, 0), datetime.now()),
    max_value=datetime.now()
)

if len(date_range) == 2:
    start_date = date_range[0].strftime("%Y-%m-%d")
    end_date = date_range[1].strftime("%Y-%m-%d")
else:
    start_date = end_date = None

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Top Skills", "🔍 Skills by Occupation", "🗺️ Skills by Region"])

# TAB 1: Top Skills
with tab1:
    st.header("Most In-Demand Skills")

    top_n = st.slider("Number of skills to show", 10, 100, 30, key="top_skills_overall")

    try:
        params = {"top_n": top_n}
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(f"{API_BASE_URL}/api/skills/top", params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                col1, col2 = st.columns([2, 1])

                with col1:
                    fig = px.bar(
                        df,
                        x='total_frequency',
                        y='skill',
                        orientation='h',
                        title="Top Skills by Frequency",
                        labels={'total_frequency': 'Frequency', 'skill': 'Skill'},
                        color='total_frequency',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(
                        height=max(600, top_n * 15),
                        showlegend=False
                    )
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    st.subheader("Rankings")
                    st.dataframe(
                        df[['rank', 'skill', 'total_frequency']],
                        height=max(600, top_n * 15),
                        width='stretch'
                    )

                # Top 20 as treemap
                st.subheader("Top 20 Skills - Treemap")
                fig2 = px.treemap(
                    df.head(20),
                    path=['skill'],
                    values='total_frequency',
                    title="Visual Representation",
                    color='total_frequency',
                    color_continuous_scale='Blues'
                )
                fig2.update_layout(height=500)
                st.plotly_chart(fig2, width='stretch')
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 2: Skills by Occupation
with tab2:
    st.header("Skills by Occupation")


    # Get occupations
    @st.cache_data(ttl=3600)
    def get_occupations():
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/occupations/demand",
                params={"top_n": 200}
            )
            if response.status_code == 200:
                data = response.json()
                return [item['esco_label'] for item in data['data']]
        except:
            return []


    occupations = get_occupations()

    if occupations:
        occupation = st.selectbox("Select Occupation", options=occupations, index=0)
    else:
        occupation = st.text_input("Enter Occupation", value="Software Developer")

    top_n_occ_skills = st.slider(
        "Number of skills to show",
        10, 50, 20,
        key="skills_by_occ"
    )

    try:
        params = {
            "esco_label": occupation,
            "top_n": top_n_occ_skills
        }
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        # Try detailed endpoint first
        response = requests.get(
            f"{API_BASE_URL}/api/skills/by-occupation/detailed",
            params=params
        )

        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                # Metadata
                if 'metadata' in data:
                    meta = data['metadata']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Jobs", f"{meta.get('total_jobs', 0):,}")
                    with col2:
                        st.metric("Jobs with Skills", f"{meta.get('jobs_with_skills', 0):,}")
                    with col3:
                        st.metric("Coverage", f"{meta.get('skill_coverage_percentage', 0):.1f}%")

                st.markdown("---")

                # Main chart
                fig = px.bar(
                    df,
                    x='percentage',
                    y='skill',
                    orientation='h',
                    title=f"Skills for {occupation}",
                    labels={'percentage': '% of Jobs', 'skill': 'Skill'},
                    color='percentage',
                    color_continuous_scale='Greens',
                    text='percentage'
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(
                    height=max(500, len(df) * 20),
                    showlegend=False
                )
                st.plotly_chart(fig, width='stretch')

                # Skill categorization
                st.subheader("Skill Categories")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if 'is_essential' in df.columns:
                        essential = int(df['is_essential'].sum())
                        st.metric("⭐ Essential", essential)

                with col2:
                    if 'is_digital' in df.columns:
                        digital = int(df['is_digital'].sum())
                        st.metric("💻 Digital", digital)

                with col3:
                    if 'is_transversal' in df.columns:
                        transversal = int(df['is_transversal'].sum())
                        st.metric("🔄 Transversal", transversal)

                with col4:
                    if 'is_green' in df.columns:
                        green = int(df['is_green'].sum())
                        st.metric("🌱 Green", green)

                # Detailed table
                st.markdown("---")
                st.subheader("Detailed Data")

                display_cols = ['rank', 'skill', 'total_frequency', 'percentage']
                if 'skill_name_el' in df.columns:
                    display_cols.append('skill_name_el')
                if 'is_essential' in df.columns:
                    display_cols.extend(['is_essential', 'is_digital', 'is_transversal', 'is_green'])

                st.dataframe(
                    df[[col for col in display_cols if col in df.columns]],
                    width='stretch',
                    height=400
                )
            else:
                st.info("No skill data available for this occupation")
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 3: Skills by Region
with tab3:
    st.header("Skills by Region")

    col1, col2 = st.columns(2)

    with col1:
        region_level_skills = st.radio(
            "Region Level",
            ["NUTS2", "Regional Unit"],
            horizontal=True
        )
        level_param_skills = "nuts2" if region_level_skills == "NUTS2" else "regional_unit"

    with col2:
        # Get regions
        @st.cache_data(ttl=3600)
        def get_regions(level):
            try:
                response = requests.get(
                    f"{API_BASE_URL}/api/regions/jobs",
                    params={"region_level": level, "top_n": 100}
                )
                if response.status_code == 200:
                    data = response.json()
                    return [item['region'] for item in data['data']]
            except:
                return []


        regions = get_regions(level_param_skills)

        if regions:
            region_skills = st.selectbox("Select Region", options=regions, index=0)
        else:
            region_skills = st.text_input("Enter Region", value="Attiki")

    top_n_region_skills = st.slider(
        "Number of skills",
        10, 50, 20,
        key="skills_by_region"
    )

    try:
        params = {
            "region": region_skills,
            "region_level": level_param_skills,
            "top_n": top_n_region_skills
        }
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(
            f"{API_BASE_URL}/api/skills/by-region",
            params=params
        )
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                col1, col2 = st.columns([2, 1])

                with col1:
                    fig = px.bar(
                        df,
                        x='total_frequency',
                        y='skill',
                        orientation='h',
                        title=f"Top Skills in {region_skills}",
                        labels={'total_frequency': 'Frequency', 'skill': 'Skill'},
                        color='total_frequency',
                        color_continuous_scale='Purples'
                    )
                    fig.update_layout(
                        height=max(500, top_n_region_skills * 20),
                        showlegend=False
                    )
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    st.subheader("Data")
                    st.dataframe(
                        df[['rank', 'skill', 'total_frequency']],
                        height=max(500, top_n_region_skills * 20),
                        width='stretch'
                    )
    except Exception as e:
        st.error(f"Error: {e}")

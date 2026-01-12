import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="Occupations", page_icon="💼", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("💼 Occupation Analysis")

# Sidebar
st.sidebar.header("Filters")


# Get list of occupations
@st.cache_data(ttl=3600)
def get_occupations():
    try:
        response = requests.get(f"{API_BASE_URL}/api/occupations/demand", params={"top_n": 200})
        if response.status_code == 200:
            data = response.json()
            return [item['esco_label'] for item in data['data']]
    except:
        return []


occupations = get_occupations()

if occupations:
    selected_occupation = st.sidebar.selectbox("Select Occupation", options=occupations, index=0)
else:
    selected_occupation = st.sidebar.text_input("Enter Occupation", value="Software Developer")

date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.now() - timedelta(days=90), datetime.now()),
    max_value=datetime.now()
)

if len(date_range) == 2:
    start_date = date_range[0].strftime("%Y-%m-%d")
    end_date = date_range[1].strftime("%Y-%m-%d")
else:
    start_date = end_date = None

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Time Series", "🗺️ Regional", "🎓 Skills"])

# TAB 1: Overview
with tab1:
    st.header(f"Overview: {selected_occupation}")

    # Regional distribution
    st.subheader("Regional Distribution")

    region_level = st.radio("Region Level", ["NUTS2", "Regional Unit"], horizontal=True, key="overview_level")
    level_param = "nuts2" if region_level == "NUTS2" else "regional_unit"

    try:
        params = {
            "esco_label": selected_occupation,
            "region_level": level_param,
            "top_n": 15
        }
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(f"{API_BASE_URL}/api/occupations/regions", params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                col1, col2 = st.columns(2)

                with col1:
                    fig = px.pie(
                        df,
                        values='total_jobs',
                        names='region',
                        title=f"Distribution by {region_level}",
                        hole=0.4
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    fig = px.bar(
                        df,
                        x='total_jobs',
                        y='region',
                        orientation='h',
                        title="Jobs by Region",
                        color='percentage',
                        color_continuous_scale='Blues',
                        text='percentage'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, width='stretch')

                # Data table
                st.dataframe(
                    df[['rank', 'region', 'total_jobs', 'percentage']],
                    width='stretch'
                )
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 2: Time Series
with tab2:
    st.header("Occupation Trend")

    try:
        params = {"esco_label": selected_occupation}
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(f"{API_BASE_URL}/api/occupations/timeseries", params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['job_count'],
                    mode='lines+markers',
                    name='Daily Jobs',
                    line=dict(color='#2ecc71', width=2),
                    marker=dict(size=6)
                ))

                fig.update_layout(
                    title=f"Daily Trend: {selected_occupation}",
                    xaxis_title="Date",
                    yaxis_title="Job Count",
                    hovermode='x unified',
                    height=500
                )
                st.plotly_chart(fig, width='stretch')

                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", f"{df['job_count'].sum():,}")
                with col2:
                    st.metric("Daily Avg", f"{df['job_count'].mean():.1f}")
                with col3:
                    st.metric("Peak", f"{df['job_count'].max():,}")
                with col4:
                    peak_date = df.loc[df['job_count'].idxmax(), 'date']
                    st.metric("Peak Date", str(peak_date)[:10])

                # Monthly aggregation
                st.subheader("Monthly Trend")
                try:
                    response_monthly = requests.get(
                        f"{API_BASE_URL}/api/trends/monthly/occupations/{selected_occupation}",
                        params=params
                    )
                    if response_monthly.status_code == 200:
                        monthly_data = response_monthly.json()
                        monthly_df = pd.DataFrame(monthly_data['data'])

                        if not monthly_df.empty:
                            fig2 = px.bar(
                                monthly_df,
                                x='month',
                                y='total_jobs',
                                title="Monthly Aggregated",
                                color='total_jobs',
                                color_continuous_scale='Greens'
                            )
                            fig2.update_layout(height=400, showlegend=False)
                            st.plotly_chart(fig2, width='stretch')
                except:
                    pass
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 3: Regional Analysis
with tab3:
    st.header("Regional Analysis")

    region_level_detail = st.radio(
        "Region Level",
        ["NUTS2", "Regional Unit"],
        horizontal=True,
        key="detail_level"
    )
    level_param_detail = "nuts2" if region_level_detail == "NUTS2" else "regional_unit"

    top_n = st.slider("Top N Regions", 5, 30, 15, key="top_regions")

    try:
        params = {
            "esco_label": selected_occupation,
            "region_level": level_param_detail,
            "top_n": top_n
        }
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(f"{API_BASE_URL}/api/occupations/regions", params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                fig = px.bar(
                    df,
                    x='total_jobs',
                    y='region',
                    orientation='h',
                    title=f"Top {top_n} Regions for {selected_occupation}",
                    labels={'total_jobs': 'Job Count', 'region': 'Region'},
                    color='percentage',
                    color_continuous_scale='Viridis',
                    text='percentage'
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(height=max(400, top_n * 25), showlegend=False)
                st.plotly_chart(fig, width='stretch')

                st.dataframe(df, width='stretch')
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 4: Skills
with tab4:
    st.header("Required Skills")

    top_n_skills = st.slider("Number of skills to show", 10, 50, 20, key="top_skills")

    try:
        params = {
            "esco_label": selected_occupation,
            "top_n": top_n_skills
        }
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(
            f"{API_BASE_URL}/api/skills/by-occupation/detailed",
            params=params
        )
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty and 'metadata' in data:
                meta = data['metadata']

                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Jobs", f"{meta.get('total_jobs', 0):,}")
                with col2:
                    st.metric("Jobs with Skills", f"{meta.get('jobs_with_skills', 0):,}")
                with col3:
                    st.metric("Coverage", f"{meta.get('skill_coverage_percentage', 0):.1f}%")
                with col4:
                    st.metric("Top Skills", len(df))

                st.markdown("---")

                col1, col2 = st.columns([3, 1])

                with col1:
                    fig = px.bar(
                        df,
                        x='percentage',
                        y='skill',
                        orientation='h',
                        title=f"Required Skills: {selected_occupation}",
                        labels={'percentage': '% of Jobs', 'skill': 'Skill'},
                        color='percentage',
                        color_continuous_scale='Greens',
                        text='percentage'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig.update_layout(height=max(500, len(df) * 20), showlegend=False)
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    st.subheader("Skill Flags")

                    if 'is_essential' in df.columns:
                        essential = int(df['is_essential'].sum())
                        st.metric("⭐ Essential", essential)

                    if 'is_digital' in df.columns:
                        digital = int(df['is_digital'].sum())
                        st.metric("💻 Digital", digital)

                    if 'is_transversal' in df.columns:
                        transversal = int(df['is_transversal'].sum())
                        st.metric("🔄 Transversal", transversal)

                    if 'is_green' in df.columns:
                        green = int(df['is_green'].sum())
                        st.metric("🌱 Green", green)

                # Detailed table
                st.markdown("---")
                st.subheader("Detailed Breakdown")

                display_cols = ['rank', 'skill', 'total_frequency', 'percentage']
                if 'skill_name_el' in df.columns:
                    display_cols.append('skill_name_el')
                if 'is_essential' in df.columns:
                    display_cols.extend(['is_essential', 'is_digital', 'is_transversal'])

                st.dataframe(
                    df[[col for col in display_cols if col in df.columns]],
                    width='stretch',
                    height=400
                )
            else:
                st.info("No skill data available for this occupation")
    except Exception as e:
        st.error(f"Error: {e}")

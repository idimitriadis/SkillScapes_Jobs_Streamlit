import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="Regions", page_icon="🏢", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("🏢 Regional Analysis")

# Sidebar
st.sidebar.header("Filters")

region_level = st.sidebar.radio("Region Level", ["NUTS2", "Regional Unit"], index=0)
level_param = "nuts2" if region_level == "NUTS2" else "regional_unit"


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


regions = get_regions(level_param)

if regions:
    selected_region = st.sidebar.selectbox("Select Region", options=regions, index=0)
else:
    selected_region = st.sidebar.text_input("Enter Region", value="Attiki")

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
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💼 Occupations", "📈 Time Series", "🎓 Skills"])

# TAB 1: Overview
with tab1:
    st.header(f"Overview: {selected_region}")

    # Regional comparison
    st.subheader("Regional Comparison")

    top_n_regions = st.slider("Number of regions to compare", 5, 30, 15, key="compare_regions")

    try:
        params = {"region_level": level_param, "top_n": top_n_regions}
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(f"{API_BASE_URL}/api/regions/jobs", params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                # Highlight selected region
                df['highlight'] = df['region'] == selected_region
                df['color'] = df['highlight'].map({True: 'Selected', False: 'Others'})

                col1, col2 = st.columns(2)

                with col1:
                    fig = px.bar(
                        df,
                        x='region',
                        y='total_jobs',
                        color='color',
                        title=f"Job Distribution Across {region_level}",
                        labels={'total_jobs': 'Job Count', 'region': 'Region'},
                        color_discrete_map={'Selected': '#e74c3c', 'Others': '#3498db'}
                    )
                    fig.update_layout(
                        height=400,
                        xaxis_tickangle=-45,
                        showlegend=False
                    )
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    # Pie chart of top 10
                    fig2 = px.pie(
                        df.head(10),
                        values='total_jobs',
                        names='region',
                        title="Top 10 Regions Share",
                        hole=0.4
                    )
                    fig2.update_traces(textposition='inside', textinfo='percent')
                    st.plotly_chart(fig2, width='stretch')

                # Data table
                st.dataframe(
                    df[['rank', 'region', 'total_jobs', 'percentage']],
                    width='stretch'
                )
    except Exception as e:
        st.error(f"Error: {e}")

    st.markdown("---")

    # Job types in region
    st.subheader(f"Job Type Categories in {selected_region}")

    try:
        params = {"region_level": level_param}
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(
            f"{API_BASE_URL}/api/regions/{selected_region}/jobtypes/categories",
            params=params
        )
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                col1, col2 = st.columns(2)

                with col1:
                    fig = px.pie(
                        df,
                        values='total_jobs',
                        names='category',
                        title="Job Type Categories",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    fig = px.bar(
                        df,
                        x='category',
                        y='total_jobs',
                        title="Category Counts",
                        color='percentage',
                        color_continuous_scale='Blues',
                        text='percentage'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 2: Occupations
with tab2:
    st.header(f"Top Occupations in {selected_region}")

    top_n_occ = st.slider("Number of occupations", 10, 50, 20, key="top_occ_region")

    try:
        params = {
            "region_level": level_param,
            "top_n": top_n_occ
        }
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(
            f"{API_BASE_URL}/api/regions/{selected_region}/occupations",
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
                        x='total_jobs',
                        y='esco_label',
                        orientation='h',
                        title=f"Top {top_n_occ} Occupations",
                        labels={'total_jobs': 'Job Count', 'esco_label': 'Occupation'},
                        color='percentage',
                        color_continuous_scale='Viridis',
                        text='percentage'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig.update_layout(height=max(500, top_n_occ * 20), showlegend=False)
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    st.subheader("Data")
                    st.dataframe(
                        df[['rank', 'esco_label', 'total_jobs', 'percentage']],
                        height=max(500, top_n_occ * 20),
                        width='stretch'
                    )
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 3: Time Series
with tab3:
    st.header(f"Time Series: {selected_region}")

    try:
        params = {"region_level": level_param}
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(
            f"{API_BASE_URL}/api/regions/{selected_region}/timeseries",
            params=params
        )
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
                    line=dict(color='#9b59b6', width=2),
                    marker=dict(size=6)
                ))

                fig.update_layout(
                    title=f"Daily Jobs in {selected_region}",
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
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 4: Skills
with tab4:
    st.header(f"In-Demand Skills in {selected_region}")

    top_n_skills = st.slider("Number of skills", 10, 50, 20, key="top_skills_region")

    try:
        params = {
            "region": selected_region,
            "region_level": level_param,
            "top_n": top_n_skills
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
                        title=f"Top {top_n_skills} Skills",
                        labels={'total_frequency': 'Frequency', 'skill': 'Skill'},
                        color='total_frequency',
                        color_continuous_scale='Oranges'
                    )
                    fig.update_layout(
                        height=max(500, top_n_skills * 20),
                        showlegend=False
                    )
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    st.subheader("Rankings")
                    st.dataframe(
                        df[['rank', 'skill', 'total_frequency']],
                        height=max(500, top_n_skills * 20),
                        width='stretch'
                    )
    except Exception as e:
        st.error(f"Error: {e}")

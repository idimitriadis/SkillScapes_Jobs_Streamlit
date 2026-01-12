import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
st.set_page_config(page_title="Jobs", page_icon="📈", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("📈 Job Market Analysis")

# Sidebar filters
st.sidebar.header("Filters")
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
tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Time Series", "📅 Monthly Trends"])

# TAB 1: Overview
with tab1:
    st.header("Job Market Overview")

    # Total job count
    col1, col2 = st.columns([1, 3])

    with col1:
        try:
            params = {}
            if start_date and end_date:
                params = {"start_date": start_date, "end_date": end_date}

            response = requests.get(f"{API_BASE_URL}/api/jobs/count", params=params)
            if response.status_code == 200:
                data = response.json()
                st.metric(
                    "Total Job Postings",
                    f"{data.get('total_jobs', 0):,}",
                    help=f"Period: {data.get('start_date', 'all')} to {data.get('end_date', 'all')}"
                )
        except Exception as e:
            st.error(f"Error: {e}")

    with col2:
        st.markdown("### Data Sources")
        st.markdown("""
        - **JobFind**: Leading Greek job portal
        - **Kariera**: Career opportunities platform
        - **Randstad**: International staffing agency
        - **Skywalker**: Tech-focused job board
        """)

    st.markdown("---")

    # Top occupations
    st.subheader("Top Occupations by Demand")

    top_n = st.slider("Number of occupations to show", 10, 50, 20, key="top_occ")

    try:
        params = {"top_n": top_n}
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(f"{API_BASE_URL}/api/occupations/demand", params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            col1, col2 = st.columns([2, 1])

            with col1:
                fig = px.bar(
                    df,
                    x='total_jobs',
                    y='esco_label',
                    orientation='h',
                    title="Top Occupations",
                    labels={'total_jobs': 'Job Count', 'esco_label': 'Occupation'},
                    color='percentage',
                    color_continuous_scale='Viridis',
                    text='percentage'
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(height=600, showlegend=False)
                st.plotly_chart(fig, width='stretch')

            with col2:
                st.dataframe(
                    df[['rank', 'esco_label', 'total_jobs', 'percentage']],
                    height=600,
                    width='stretch'
                )
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 2: Time Series
with tab2:
    st.header("Daily Job Postings Time Series")

    try:
        params = {}
        if start_date and end_date:
            params = {"start_date": start_date, "end_date": end_date}

        response = requests.get(f"{API_BASE_URL}/api/jobs/timeseries", params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                # Overall trend
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['total_jobs'],
                    mode='lines+markers',
                    name='Total Jobs',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=4)
                ))

                fig.update_layout(
                    title="Daily Job Postings",
                    xaxis_title="Date",
                    yaxis_title="Job Count",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig, width='stretch')

                # By source
                st.subheader("Job Postings by Source")

                fig2 = go.Figure()

                if 'jobfind_count' in df.columns:
                    fig2.add_trace(go.Scatter(
                        x=df['date'], y=df['jobfind_count'],
                        mode='lines', name='JobFind',
                        stackgroup='one', fillcolor='#3498db'
                    ))
                if 'kariera_count' in df.columns:
                    fig2.add_trace(go.Scatter(
                        x=df['date'], y=df['kariera_count'],
                        mode='lines', name='Kariera',
                        stackgroup='one', fillcolor='#e74c3c'
                    ))
                if 'randstad_count' in df.columns:
                    fig2.add_trace(go.Scatter(
                        x=df['date'], y=df['randstad_count'],
                        mode='lines', name='Randstad',
                        stackgroup='one', fillcolor='#2ecc71'
                    ))
                if 'skywalker_count' in df.columns:
                    fig2.add_trace(go.Scatter(
                        x=df['date'], y=df['skywalker_count'],
                        mode='lines', name='Skywalker',
                        stackgroup='one', fillcolor='#f39c12'
                    ))

                fig2.update_layout(
                    title="Job Postings by Source (Stacked)",
                    xaxis_title="Date",
                    yaxis_title="Job Count",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig2, width='stretch')

                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", f"{df['total_jobs'].sum():,}")
                with col2:
                    st.metric("Daily Average", f"{df['total_jobs'].mean():.1f}")
                with col3:
                    st.metric("Peak", f"{df['total_jobs'].max():,}")
                with col4:
                    peak_date = df.loc[df['total_jobs'].idxmax(), 'date']
                    st.metric("Peak Date", str(peak_date)[:10])
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 3: Monthly Trends
with tab3:
    st.header("Monthly Aggregated Trends")

    try:
        params = {}
        if start_date and end_date:
            params = {"start_date": start_date, "end_date": end_date}

        response = requests.get(f"{API_BASE_URL}/api/trends/monthly", params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                fig = px.bar(
                    df,
                    x='month',
                    y='total_jobs',
                    title="Monthly Job Postings",
                    labels={'month': 'Month', 'total_jobs': 'Total Jobs'},
                    color='total_jobs',
                    color_continuous_scale='Blues',
                    text='total_jobs'
                )
                fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                fig.update_layout(height=500, showlegend=False)
                st.plotly_chart(fig, width='stretch')

                # Month-over-month growth
                if len(df) > 1:
                    df['mom_change'] = df['total_jobs'].pct_change() * 100

                    fig2 = px.line(
                        df[1:],  # Skip first row with NaN
                        x='month',
                        y='mom_change',
                        title="Month-over-Month Growth Rate (%)",
                        labels={'month': 'Month', 'mom_change': 'Growth %'},
                        markers=True
                    )
                    fig2.add_hline(y=0, line_dash="dash", line_color="gray")
                    fig2.update_layout(height=400)
                    st.plotly_chart(fig2, width='stretch')
    except Exception as e:
        st.error(f"Error: {e}")

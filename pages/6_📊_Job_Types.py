import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="Job Types", page_icon="📊", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("📊 Job Types Analysis")

# Sidebar
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    value=datetime(2025, 5, 1, 0, 0, 0, 0),
    max_value=datetime.now()
)

if len(date_range) == 2:
    start_date = date_range[0].strftime("%Y-%m-%d")
    end_date = date_range[1].strftime("%Y-%m-%d")
else:
    start_date = end_date = None

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Distribution", "🏷️ Categories", "💼 By Occupation"])

# TAB 1: Distribution
with tab1:
    st.header("Job Type Distribution")

    col1, col2 = st.columns(2)

    with col1:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All Types", "Full-time/Part-time", "Temporary/Permanent"],
            key="dist_category"
        )

    category_param = None
    if category_filter == "Full-time/Part-time":
        category_param = "fulltime"
    elif category_filter == "Temporary/Permanent":
        category_param = "temporary"

    try:
        params = {}
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})
        if category_param:
            params['category'] = category_param

        response = requests.get(f"{API_BASE_URL}/api/jobtypes/distribution", params=params)

        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Distribution (Top 15)")
                    fig = px.pie(
                        df.head(15),
                        values='total_jobs',
                        names='job_type',
                        title="Job Type Distribution",
                        hole=0.4
                    )
                    fig.update_traces(textposition='inside', textinfo='percent')
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    st.subheader("By Count")
                    fig = px.bar(
                        df.head(15),
                        x='total_jobs',
                        y='job_type',
                        orientation='h',
                        title="Job Type Counts",
                        color='percentage',
                        color_continuous_scale='Blues',
                        text='percentage'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig.update_layout(showlegend=False, height=500)
                    st.plotly_chart(fig, width='stretch')

                # Data table
                st.markdown("---")
                st.subheader("Detailed Breakdown")

                display_cols = ['job_type', 'total_jobs', 'percentage']
                if 'category' in df.columns:
                    display_cols.append('category')

                st.dataframe(
                    df[display_cols],
                    width='stretch',
                    height=400
                )
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 2: Categories
with tab2:
    st.header("Job Type Categories")

    try:
        params = {}
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(f"{API_BASE_URL}/api/jobtypes/categories", params=params)

        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])

            if not df.empty:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Category Distribution")
                    fig = px.pie(
                        df,
                        values='total_jobs',
                        names='category',
                        title="Job Categories",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        textfont_size=14
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch')

                with col2:
                    st.subheader("Category Metrics")
                    for _, row in df.iterrows():
                        st.metric(
                            row['category'],
                            f"{int(row['total_jobs']):,} jobs",
                            f"{row['percentage']:.1f}%"
                        )

                # Bar chart
                st.markdown("---")
                fig = px.bar(
                    df,
                    x='category',
                    y='total_jobs',
                    title="Category Comparison",
                    color='percentage',
                    color_continuous_scale='Viridis',
                    text='percentage'
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, width='stretch')

                # Category definitions
                st.markdown("---")
                st.subheader("Category Definitions")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Full-time / Part-time")
                    st.markdown("""
                    - Πλήρης απασχόληση (Full-time)
                    - FULL_TIME
                    - Μερική απασχόληση (Part-time)
                    - PART_TIME
                    - Combinations and variations
                    """)

                with col2:
                    st.markdown("### Temporary / Permanent")
                    st.markdown("""
                    - Εποχιακή εργασία (Seasonal)
                    - μόνιμη (Permanent)
                    - Πρακτική άσκηση (Internship)
                    - Σύμβαση έργου (Contract)
                    - Freelance positions
                    """)
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 3: By Occupation
with tab3:
    st.header("Job Types by Occupation")


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
        occupation_jt = st.selectbox(
            "Select Occupation",
            options=occupations,
            index=0,
            key="jt_occupation"
        )
    else:
        occupation_jt = st.text_input("Enter Occupation", value="Software Developer")

    try:
        params = {"esco_label": occupation_jt}
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        # Try categories endpoint
        response = requests.get(
            f"{API_BASE_URL}/api/occupations/jobtypes/categories",
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
                        title=f"Job Type Categories: {occupation_jt}",
                        hole=0.4
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
                        color_continuous_scale='Greens',
                        text='percentage'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    st.plotly_chart(fig, width='stretch')

                st.dataframe(df, width='stretch')
    except Exception as e:
        st.error(f"Error: {e}")

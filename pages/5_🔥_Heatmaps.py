import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="Heatmaps", page_icon="🔥", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.title("🔥 Heatmap Visualizations")

# Sidebar
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
tab1, tab2 = st.tabs(["💼 Occupations × Regions", "🎓 Skills × Regions"])

# TAB 1: Occupations × Regions
with tab1:
    st.header("Occupations × Regions Heatmap")

    col1, col2, col3 = st.columns(3)

    with col1:
        region_level = st.radio(
            "Region Level",
            ["NUTS2", "Regional Unit"],
            horizontal=True,
            key="occ_region_level"
        )
        level_param = "nuts2" if region_level == "NUTS2" else "regional_unit"

    with col2:
        top_n_occ = st.slider("Top N Occupations", 5, 30, 15, key="top_occ_heatmap")

    with col3:
        top_n_reg = st.slider("Top N Regions", 5, 20, 10, key="top_reg_heatmap")

    try:
        params = {
            "region_level": level_param,
            "top_n_occupations": top_n_occ,
            "top_n_regions": top_n_reg
        }
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(
            f"{API_BASE_URL}/api/heatmap/occupations-regions",
            params=params
        )
        if response.status_code == 200:
            data = response.json()

            if 'matrix' in data and 'occupations' in data and 'regions' in data:
                # Create pivot table from matrix
                occupations = data['occupations']
                regions = data['regions']
                matrix = data['matrix']

                pivot_df = pd.DataFrame(
                    matrix,
                    index=occupations,
                    columns=regions
                )

                # Create heatmap
                fig = px.imshow(
                    pivot_df,
                    labels=dict(x="Region", y="Occupation", color="Job Count"),
                    x=pivot_df.columns,
                    y=pivot_df.index,
                    color_continuous_scale='YlOrRd',
                    aspect="auto"
                )

                fig.update_layout(
                    title="Occupations vs Regions Heatmap",
                    height=max(500, len(occupations) * 25),
                    xaxis_tickangle=-45
                )

                fig.update_xaxes(side="bottom")

                st.plotly_chart(fig, width='stretch')

                # Show dimensions
                if 'dimensions' in data:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Occupations", data['dimensions']['occupations'])
                    with col2:
                        st.metric("Regions", data['dimensions']['regions'])
                    with col3:
                        st.metric("Data Points", data.get('count', 0))

                # Data table
                with st.expander("📊 View Raw Data"):
                    if 'data' in data:
                        raw_df = pd.DataFrame(data['data'])
                        st.dataframe(raw_df, width='stretch')
    except Exception as e:
        st.error(f"Error: {e}")

# TAB 2: Skills × Regions for Occupation
with tab2:
    st.header("Skills × Regions Heatmap for Occupation")


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

    col1, col2 = st.columns(2)

    with col1:
        if occupations:
            occupation = st.selectbox(
                "Select Occupation",
                options=occupations,
                index=0,
                key="heatmap_occupation"
            )
        else:
            occupation = st.text_input("Enter Occupation", value="Software Developer")

    with col2:
        region_level_skills = st.radio(
            "Region Level",
            ["NUTS2", "Regional Unit"],
            horizontal=True,
            key="skills_region_level"
        )
        level_param_skills = "nuts2" if region_level_skills == "NUTS2" else "regional_unit"

    col1, col2, col3 = st.columns(3)

    with col1:
        top_n_skills = st.slider("Top N Skills", 10, 50, 20, key="top_skills_heatmap")

    with col2:
        top_n_regions = st.slider("Top N Regions", 5, 20, 10, key="top_regions_heatmap")

    with col3:
        normalize = st.checkbox("Normalize (% per region)", value=False)

    st.info(f"📊 Analyzing skills for **{occupation}** across top regions")

    try:
        params = {
            "esco_label": occupation,
            "region_level": level_param_skills,
            "top_n_skills": top_n_skills,
            "top_n_regions": top_n_regions,
            "normalize": normalize
        }
        if start_date and end_date:
            params.update({"start_date": start_date, "end_date": end_date})

        response = requests.get(
            f"{API_BASE_URL}/api/heatmap/skills-regions-occupation",
            params=params
        )

        if response.status_code == 200:
            data = response.json()

            if 'skills' in data and 'regions' in data:
                # Use appropriate matrix based on normalization
                matrix_data = data.get('normalized_matrix', data.get('matrix', []))

                skills = data['skills']
                regions = data['regions']

                if matrix_data and skills and regions:
                    # Create pivot table
                    pivot_df = pd.DataFrame(
                        matrix_data,
                        index=skills,
                        columns=regions
                    )

                    # Create heatmap
                    fig = px.imshow(
                        pivot_df,
                        labels=dict(
                            x="Region",
                            y="Skill",
                            color="Percentage" if normalize else "Frequency"
                        ),
                        x=pivot_df.columns,
                        y=pivot_df.index,
                        color_continuous_scale='Viridis',
                        aspect="auto",
                        text_auto='.1f' if normalize else True
                    )

                    title = f"Skills × Regions: {occupation}"
                    if normalize:
                        title += " (Normalized %)"

                    fig.update_layout(
                        title=title,
                        height=max(500, len(skills) * 25),
                        xaxis_tickangle=-45
                    )

                    fig.update_xaxes(side="bottom")

                    st.plotly_chart(fig, width='stretch')

                    # Metrics
                    if 'dimensions' in data:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Skills", data['dimensions'].get('skills', 0))
                        with col2:
                            st.metric("Regions", data['dimensions'].get('regions', 0))
                        with col3:
                            if 'region_job_counts' in data:
                                total_jobs = sum(data['region_job_counts'].values())
                                st.metric("Total Jobs", f"{total_jobs:,}")

                    # Regional job counts
                    if 'region_job_counts' in data:
                        with st.expander("📊 Jobs per Region"):
                            jobs_df = pd.DataFrame([
                                {"Region": k, "Total Jobs": v}
                                for k, v in data['region_job_counts'].items()
                            ])
                            st.dataframe(jobs_df, width='stretch')
                else:
                    st.warning("No data available for selected parameters")
            else:
                st.warning("No data available for selected occupation and regions")
    except Exception as e:
        st.error(f"Error: {e}")

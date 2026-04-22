import os
import pandas as pd
import streamlit as st
import plotly.express as px
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# --- Page config ---
st.set_page_config(
    page_title="Job Market Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
    <style>
        .main { background-color: #0f1117; }
        .metric-card {
            background: linear-gradient(135deg, #1e2130, #2a2f45);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid #2e3250;
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: #4f8ef7;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #9099b0;
            margin-top: 4px;
        }
        .section-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: #e0e4f0;
            margin-bottom: 8px;
        }
        div[data-testid="stSidebar"] {
            background-color: #1a1d2e;
        }
        /* Sidebar label color */
        div[data-testid="stSidebar"] label {
            color: #ffffff !important;
        }
        /* Multiselect container */
        div[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 1.5px solid #000000 !important;
            border-radius: 6px !important;
            color: #000000 !important;
        }
        /* Multiselect selected tags — white with black text and outline */
        div[data-testid="stSidebar"] span[data-baseweb="tag"] {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #000000 !important;
        }
        /* Multiselect tag close button */
        div[data-testid="stSidebar"] span[data-baseweb="tag"] span[role="presentation"] {
            color: #000000 !important;
        }
        /* Multiselect input text */
        div[data-testid="stSidebar"] input {
            color: #000000 !important;
        }
        /* Checkbox label */
        div[data-testid="stSidebar"] .stCheckbox label {
            color: #ffffff !important;
        }
        /* Checkbox box — white with black border */
        div[data-baseweb="checkbox"] div {
            background-color: #ffffff !important;
            border-color: #000000 !important;
        }
        /* Checkbox checked state — white with black border */
        div[data-baseweb="checkbox"] input:checked ~ div {
            background-color: #ffffff !important;
            border-color: #000000 !important;
        }
        /* Checkbox checkmark color */
        div[data-baseweb="checkbox"] input:checked ~ div svg path {
            fill: #000000 !important;
        }
    </style>
""", unsafe_allow_html=True)

COLORS = px.colors.sequential.Blues_r
ACCENT = "#4f8ef7"

# --- Supabase client ---
@st.cache_resource
def get_client():
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# --- Load data with pagination ---
@st.cache_data(ttl=3600)
def load_data():
    client = get_client()
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        response = client.table("jobs_clean").select("*").range(offset, offset + page_size - 1).execute()
        batch = response.data
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    df = pd.DataFrame(all_rows)
    if df.empty:
        st.error("No data found in jobs_clean table.")
        st.stop()
    if "posted_date" in df.columns:
        df["posted_date"] = pd.to_datetime(df["posted_date"])
    return df

# --- Load data ---
df = load_data()

# --- Sidebar Filters ---
st.sidebar.title("🔍 Filters")
st.sidebar.markdown("---")

cat_options = sorted(df["job_category"].dropna().unique())
level_options = sorted(df["job_level"].dropna().unique())
source_options = sorted(df["source"].dropna().unique())

selected_cats = st.sidebar.multiselect("Job Category", cat_options, default=cat_options)
selected_levels = st.sidebar.multiselect("Seniority Level", level_options, default=level_options)
selected_sources = st.sidebar.multiselect("Source", source_options, default=source_options)
remote_only = st.sidebar.checkbox("Remote Only")

filtered = df[
    df["job_category"].isin(selected_cats) &
    df["job_level"].isin(selected_levels) &
    df["source"].isin(selected_sources)
]
if remote_only:
    filtered = filtered[filtered["is_remote"] == True]

# --- Header ---
st.title("📊 Job Market Trend Dashboard")
st.caption(f"Showing **{len(filtered):,}** of **{len(df):,}** jobs • Auto-updated daily via ETL pipeline")
st.markdown("---")

# --- KPI Cards ---
col1, col2, col3, col4, col5 = st.columns(5)
metrics = [
    (col1, "💼", "Total Jobs", f"{len(filtered):,}"),
    (col2, "🏢", "Companies", f"{filtered['company'].nunique():,}"),
    (col3, "🌐", "Remote Jobs", f"{filtered['is_remote'].sum():,}"),
    (col4, "📍", "Cities", f"{filtered['city'].nunique():,}"),
    (col5, "📡", "Sources", f"{filtered['source'].nunique():,}"),
]
for col, icon, label, value in metrics:
    col.markdown(f"""
        <div class="metric-card">
            <div style="font-size:1.5rem">{icon}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Row 1: Category + Level ---
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-header">📂 Jobs by Category</div>', unsafe_allow_html=True)
    cat_counts = filtered["job_category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.bar(cat_counts, x="count", y="category", orientation="h",
                 color="count", color_continuous_scale="Blues")
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      height=320, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#9099b0")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown('<div class="section-header">🎯 Jobs by Seniority Level</div>', unsafe_allow_html=True)
    level_counts = filtered["job_level"].value_counts().reset_index()
    level_counts.columns = ["level", "count"]
    fig = px.pie(level_counts, values="count", names="level", hole=0.45,
                 color_discrete_sequence=COLORS)
    fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#9099b0", legend_font_color="#9099b0")
    st.plotly_chart(fig, use_container_width=True)

# --- Row 2: Source + Remote ---
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-header">📡 Jobs by Source</div>', unsafe_allow_html=True)
    source_counts = filtered["source"].value_counts().reset_index()
    source_counts.columns = ["source", "count"]
    fig = px.pie(source_counts, values="count", names="source", hole=0.45,
                 color_discrete_sequence=["#0077B5", "#4f8ef7", "#00A4E0"])
    fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#9099b0", legend_font_color="#9099b0")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown('<div class="section-header">🌐 Remote vs On-site by Category</div>', unsafe_allow_html=True)
    remote_cat = filtered.groupby(["job_category", "is_remote"]).size().reset_index(name="count")
    remote_cat["type"] = remote_cat["is_remote"].map({True: "Remote", False: "On-site"})
    fig = px.bar(remote_cat, x="job_category", y="count", color="type",
                 barmode="group", color_discrete_map={"Remote": ACCENT, "On-site": "#2a3f6f"})
    fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#9099b0",
                      legend_font_color="#9099b0", xaxis_tickangle=-20)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

# --- Row 3: Top cities + Top companies ---
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="section-header">📍 Top Hiring Cities</div>', unsafe_allow_html=True)
    city_counts = filtered[filtered["city"].notna()]["city"].value_counts().head(10).reset_index()
    city_counts.columns = ["city", "count"]
    fig = px.bar(city_counts, x="count", y="city", orientation="h",
                 color="count", color_continuous_scale="Blues")
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      height=350, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#9099b0")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown('<div class="section-header">🏢 Top Hiring Companies</div>', unsafe_allow_html=True)
    company_counts = filtered["company"].value_counts().head(10).reset_index()
    company_counts.columns = ["company", "count"]
    fig = px.bar(company_counts, x="count", y="company", orientation="h",
                 color="count", color_continuous_scale="Blues")
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      height=350, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#9099b0")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

# --- Row 4: Top job titles ---
st.markdown('<div class="section-header">🔥 Top 10 Trending Job Titles</div>', unsafe_allow_html=True)
title_counts = filtered["title_normalized"].value_counts().head(10).reset_index()
title_counts.columns = ["title", "count"]
fig = px.bar(title_counts, x="title", y="count",
             color="count", color_continuous_scale="Blues")
fig.update_layout(showlegend=False, coloraxis_showscale=False,
                  height=320, paper_bgcolor="rgba(0,0,0,0)",
                  plot_bgcolor="rgba(0,0,0,0)", font_color="#9099b0",
                  xaxis_tickangle=-20)
fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=False)
st.plotly_chart(fig, use_container_width=True)

# --- Row 5: Postings over time ---
st.markdown('<div class="section-header">📅 Job Postings Over Time</div>', unsafe_allow_html=True)
if "posted_date" in filtered.columns:
    time_counts = filtered.groupby("posted_date").size().reset_index(name="count")
    fig = px.line(time_counts, x="posted_date", y="count", markers=True,
                  line_shape="spline", color_discrete_sequence=[ACCENT])
    fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font_color="#9099b0")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Filterable Job Table ---
st.markdown('<div class="section-header">📋 Browse Jobs</div>', unsafe_allow_html=True)
table_cols = ["title", "company", "city", "state", "is_remote",
              "job_level", "job_category", "source", "posted_date"]
available_cols = [c for c in table_cols if c in filtered.columns]
st.dataframe(
    filtered[available_cols].sort_values("posted_date", ascending=False) if "posted_date" in filtered.columns else filtered[available_cols],
    use_container_width=True,
    hide_index=True
)
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

# --- Supabase client ---
@st.cache_resource
def get_client():
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# --- Load data ---
@st.cache_data(ttl=3600)
def load_data():
    client = get_client()
    response = client.table("jobs_clean").select("*").execute()
    df = pd.DataFrame(response.data)
    df["posted_date"] = pd.to_datetime(df["posted_date"])
    return df

# --- App ---
st.title("📊 Job Market Trend Dashboard")
st.caption("Powered by live job data from LinkedIn & Indeed • Auto-updated daily")

df = load_data()

# --- KPI Row ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs", len(df))
col2.metric("Companies", df["company"].nunique())
col3.metric("Remote Jobs", df["is_remote"].sum())
col4.metric("Sources", df["source"].nunique())

st.divider()

# --- Row 1: Category + Level ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Jobs by Category")
    cat_counts = df["job_category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.bar(cat_counts, x="count", y="category", orientation="h",
                 color="count", color_continuous_scale="Blues")
    fig.update_layout(showlegend=False, coloraxis_showscale=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Jobs by Seniority Level")
    level_counts = df["job_level"].value_counts().reset_index()
    level_counts.columns = ["level", "count"]
    fig = px.pie(level_counts, values="count", names="level", hole=0.4,
                 color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Row 2: Source + Remote ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Jobs by Source")
    source_counts = df["source"].value_counts().reset_index()
    source_counts.columns = ["source", "count"]
    fig = px.pie(source_counts, values="count", names="source", hole=0.4,
                 color_discrete_sequence=["#0077B5", "#FF0000"])
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Remote vs On-site")
    remote_counts = df["is_remote"].map({True: "Remote", False: "On-site"}).value_counts().reset_index()
    remote_counts.columns = ["type", "count"]
    fig = px.bar(remote_counts, x="type", y="count",
                 color="type", color_discrete_sequence=["#1f77b4", "#aec7e8"])
    fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Row 3: Top cities + Top companies ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Hiring Cities")
    city_counts = df[df["city"].notna()]["city"].value_counts().head(10).reset_index()
    city_counts.columns = ["city", "count"]
    fig = px.bar(city_counts, x="count", y="city", orientation="h",
                 color="count", color_continuous_scale="Blues")
    fig.update_layout(showlegend=False, coloraxis_showscale=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Top Hiring Companies")
    company_counts = df["company"].value_counts().head(10).reset_index()
    company_counts.columns = ["company", "count"]
    fig = px.bar(company_counts, x="count", y="company", orientation="h",
                 color="count", color_continuous_scale="Blues")
    fig.update_layout(showlegend=False, coloraxis_showscale=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Row 4: Postings over time ---
st.subheader("Job Postings Over Time")
time_counts = df.groupby("posted_date").size().reset_index(name="count")
fig = px.line(time_counts, x="posted_date", y="count", markers=True)
fig.update_layout(height=350)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Raw data table ---
st.subheader("📋 Browse Jobs")
filters = st.columns(3)
with filters[0]:
    cat_filter = st.multiselect("Category", options=df["job_category"].unique())
with filters[1]:
    level_filter = st.multiselect("Level", options=df["job_level"].unique())
with filters[2]:
    source_filter = st.multiselect("Source", options=df["source"].unique())

filtered = df.copy()
if cat_filter:
    filtered = filtered[filtered["job_category"].isin(cat_filter)]
if level_filter:
    filtered = filtered[filtered["job_level"].isin(level_filter)]
if source_filter:
    filtered = filtered[filtered["source"].isin(source_filter)]

st.dataframe(
    filtered[["title", "company", "city", "state", "is_remote", "job_level", "job_category", "source", "posted_date"]],
    use_container_width=True,
    hide_index=True
)
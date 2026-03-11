import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="EchoInv | Terminal", layout="wide", page_icon="⚡")

# --- MODERN STYLING (EchoFi Aesthetic) ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E11; color: #FFFFFF; }
    
    /* KPI Cards */
    div[data-testid="stMetricValue"] { 
        background-color: #151921; padding: 20px; border-radius: 12px; 
        border: 1px solid #2D333B; color: #00FFA3 !important; 
        font-family: 'Courier New', monospace; font-size: 1.8rem !important;
    }
    
    /* Table Styling */
    .stDataFrame { background-color: #151921; border-radius: 10px; border: 1px solid #2D333B; }
    
    /* Buttons */
    .stButton>button { 
        background-color: #00FFA3; color: black; border-radius: 8px; 
        border: none; font-weight: bold; width: 100%;
    }
    
    /* Forms */
    .stExpander { background-color: #151921; border: 1px solid #2D333B; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- UNIFORM DATA ENGINE ---
@st.cache_data(ttl=60)
def load_live_data():
    # Your specific published CSV link
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTRBP7-Jh2bfZF7BbU13MSw_5p0oESN3xvAQd9R-0SxHSqNjPiGYI5LqfwokRXBcMMTUcLEgzfWaiUm/pub?output=csv"
    
    try:
        df = pd.read_csv(url)
        # Remove any leading/trailing spaces from headers
        df.columns = [str(c).strip() for c in df.columns]
        
        # Numeric cleanup for columns matching your Sheet names
        numeric_cols = ['Annual Demand (D)', 'EOQ', 'Annual Value', 'Reorder Point (ROP)', 'Unit Cost (C)']
        for c in numeric_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace('[$,]', '', regex=True), errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame()

# Initialize Session
if 'inventory_data' not in st.session_state:
    st.session_state.inventory_data = load_live_data()

# --- HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("⚡ EchoInv Terminal")
    st.write("Supply Chain Intelligence Engine • Mode: **Uniform Sync**")
with c2:
    if st.button("🔄 Sync with Spreadsheet"):
        st.session_state.inventory_data = load_live_data()
        st.rerun()

df = st.session_state.inventory_data

# --- SIDEBAR FILTERS ---
st.sidebar.header("Terminal Filters")
# Using exact name: Class ABC
abc_options = sorted(list(df['Class ABC'].unique())) if 'Class ABC' in df.columns else ['A', 'B', 'C']
abc_filter = st.sidebar.multiselect("Filter Class ABC", options=abc_options, default=abc_options)

# Filter Data
filtered_df = df[df['Class ABC'].isin(abc_filter)] if 'Class ABC' in df.columns else df

# --- KPI ROW ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Annual Value", f"${filtered_df['Annual Value'].sum():,.0f}" if 'Annual Value' in filtered_df.columns else "$0")
k2.metric("Avg EOQ", f"{filtered_df['EOQ'].mean():.0f}" if 'EOQ' in filtered_df.columns else "0")
k3.metric("SKU Count", len(filtered_df))
k4.metric("Active Classes", ", ".join(abc_filter))

st.markdown("---")

# --- CHARTS (Using Uniform Names) ---
if not filtered_df.empty:
    chart_col1, chart_col2 = st.columns([2, 1])
    
    with chart_col1:
        st.subheader("Inventory Distribution (Demand vs. Value)")
        # Plotly using exact column names from your sheet
        fig = px.scatter(
            filtered_df, 
            x="Annual Demand (D)", 
            y="Annual Value", 
            size="EOQ", 
            color="Class ABC",
            hover_name="Article",
            color_discrete_sequence=['#00FFA3', '#BB86FC', '#848E9C'],
            # Ensure EOQ size is always at least 1 for visibility
            size_max=40
        )
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
    with chart_col2:
        st.subheader("Value Split %")
        fig_pie = px.pie(
            filtered_df, 
            values='Annual Value', 
            names='Class ABC', 
            hole=0.7,
            color_discrete_sequence=['#00FFA3', '#BB86FC', '#2D333B']
        )
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

# --- ADD DATA FORM ---
with st.expander("➕ Add New SKU to Terminal"):
    with st.form("entry_form"):
        f1, f2, f3, f4, f5 = st.columns(5)
        new_art = f1.text_input("Article")
        new_abc = f2.selectbox("Class ABC", ['A', 'B', 'C'])
        new_dem = f3.number_input("Annual Demand (D)", min_value=0.0)
        new_val = f4.number_input("Annual Value", min_value=0.0)
        new_eoq = f5.number_input("EOQ", min_value=0.0)
        
        if st.form_submit_button("Add Record"):
            new_row = pd.DataFrame([{
                'Article': new_art, 
                'Class ABC': new_abc, 
                'Annual Demand (D)': new_dem, 
                'Annual Value': new_val,
                'EOQ': new_eoq
            }])
            st.session_state.inventory_data = pd.concat([st.session_state.inventory_data, new_row], ignore_index=True)
            st.rerun()

# --- LIVE EDITOR ---
st.subheader("📝 Live Inventory Terminal Editor")
# This shows the full table exactly as it is in Google Sheets
edited_df = st.data_editor(st.session_state.inventory_data, num_rows="dynamic", use_container_width=True)

if st.button("💾 Save Changes Locally"):
    st.session_state.inventory_data = edited_df
    st.success("Changes saved to session memory!")

# Sidebar Export
csv = edited_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Download Revised CSV", data=csv, file_name="inventory_update.csv", mime="text/csv")

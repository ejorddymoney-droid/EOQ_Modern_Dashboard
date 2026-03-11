import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="EchoInv | Terminal", layout="wide", page_icon="⚡")

# --- MODERN STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E11; color: #FFFFFF; }
    div[data-testid="stMetricValue"] { 
        background-color: #151921; padding: 20px; border-radius: 12px; 
        border: 1px solid #2D333B; color: #00FFA3 !important; 
    }
    .stDataFrame { background-color: #151921; border-radius: 10px; border: 1px solid #2D333B; }
    .stButton>button { background-color: #00FFA3; color: black; border-radius: 8px; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- DEFENSIVE DATA ENGINE ---
def load_live_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTRBP7-Jh2bfZF7BbU13MSw_5p0oESN3xvAQd9R-0SxHSqNjPiGYI5LqfwokRXBcMMTUcLEgzfWaiUm/pub?output=csv"
    try:
        df = pd.read_csv(url)
        # Clean headers: remove spaces, handle special characters
        df.columns = [str(c).strip() for c in df.columns]
        
        # Clean numeric data: Remove $, commas, and handle empty cells
        cols_to_fix = ['Annual Demand (D)', 'Annual Value', 'EOQ', 'Unit Cost (C)', 'Reorder Point (ROP)']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('[$,]', '', regex=True), errors='coerce').fillna(0)
                # Plotly 'size' parameter crashes on negative or zero. Force a tiny positive value for the chart.
                if col == 'EOQ':
                    df['EOQ_Size'] = df[col].apply(lambda x: x if x > 0 else 0.1)
        
        return df, "Success"
    except Exception as e:
        return pd.DataFrame(), f"Error: {str(e)}"

# Initialize Session
if 'inventory_data' not in st.session_state:
    data, msg = load_live_data()
    st.session_state.inventory_data = data

# --- HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("⚡ EchoInv Terminal")
with c2:
    if st.button("🔄 Sync with Spreadsheet"):
        data, msg = load_live_data()
        st.session_state.inventory_data = data
        st.rerun()

df = st.session_state.inventory_data

# --- DEBUGGING TOOL (Hidden by default) ---
with st.expander("🛠️ Debug: View Spreadsheet Columns"):
    st.write("Columns found in your Google Sheet:")
    st.write(list(df.columns))

if df.empty:
    st.error("No data found. Please check your Google Sheet link.")
    st.stop()

# --- SIDEBAR ---
abc_col = 'Class ABC' if 'Class ABC' in df.columns else df.columns[1] # fallback to 2nd col
abc_options = sorted(list(df[abc_col].unique()))
abc_filter = st.sidebar.multiselect(f"Filter {abc_col}", options=abc_options, default=abc_options)

filtered_df = df[df[abc_col].isin(abc_filter)]

# --- KPI ROW ---
k1, k2, k3, k4 = st.columns(4)
# Checking column existence before math to prevent crashes
val_col = 'Annual Value' if 'Annual Value' in df.columns else None
eoq_col = 'EOQ' if 'EOQ' in df.columns else None

k1.metric("Total Value", f"${filtered_df[val_col].sum():,.0f}" if val_col else "$0")
k2.metric("Avg EOQ", f"{filtered_df[eoq_col].mean():.0f}" if eoq_col else "0")
k3.metric("SKU Count", len(filtered_df))
k4.metric("Active Classes", ", ".join(abc_filter))

st.markdown("---")

# --- CHARTS ---
if not filtered_df.empty:
    chart_1, chart_2 = st.columns([2, 1])
    
    with chart_1:
        st.subheader("Inventory Distribution")
        # Checking for required chart columns
        needed = ['Annual Demand (D)', 'Annual Value', 'EOQ_Size', 'Article', 'Class ABC']
        if all(c in filtered_df.columns for c in needed):
            try:
                fig = px.scatter(
                    filtered_df, 
                    x="Annual Demand (D)", 
                    y="Annual Value", 
                    size="EOQ_Size", 
                    color="Class ABC",
                    hover_name="Article",
                    color_discrete_sequence=['#00FFA3', '#BB86FC', '#848E9C'],
                    size_max=40
                )
                fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Chart Error: {e}")
        else:
            st.warning("Missing columns for scatter chart. Ensure 'Annual Demand (D)', 'Annual Value', and 'EOQ' are in your sheet.")
            
    with chart_2:
        st.subheader("Value Split")
        if val_col and abc_col:
            fig_pie = px.pie(filtered_df, values=val_col, names=abc_col, hole=0.7,
                             color_discrete_sequence=['#00FFA3', '#BB86FC', '#2D333B'])
            fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

# --- TABLE ---
st.subheader("📝 Live Inventory Terminal Editor")
st.data_editor(st.session_state.inventory_data, num_rows="dynamic", use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="EchoInv Terminal", layout="wide", initial_sidebar_state="collapsed")

# --- CSS FOR MODERN UI ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E11; color: #FFFFFF; }
    div[data-testid="stMetricValue"] {
        background-color: #151921; padding: 20px; border-radius: 15px; border: 1px solid #2D333B;
    }
    [data-testid="stMetricLabel"] { color: #848E9C !important; }
    .stDataFrame { background-color: #151921; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ROBUST DATA LOADING ---
@st.cache_data
def load_data():
    # TIP: If your data is NOT on the first tab, change 'gid=0' to your tab ID
    sheet_id = "1QCCB2lUQm0pGZP-lGyrAi5MmBLK8v1gBoK6yGJWxDD0"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns] # Clean whitespace
    return df

def find_column(df, keywords):
    """Helper to find a column name even if it's slightly different"""
    for col in df.columns:
        if any(key.lower() in col.lower() for key in keywords):
            return col
    return None

# --- MAIN APP ---
df = load_data()

# Identify columns dynamically
col_val = find_column(df, ['Annual Value', 'Total Value', 'Value'])
col_demand = find_column(df, ['Demand', 'Annual Demand'])
col_eoq = find_column(df, ['EOQ', 'Order Quantity'])
col_abc = find_column(df, ['Class', 'ABC'])
col_article = find_column(df, ['Article', 'Item', 'Name'])

# --- ERROR CHECKING UI ---
if not col_val or not col_abc:
    st.error("⚠️ Column Mismatch Error")
    st.write("I found these columns in your sheet:", list(df.columns))
    st.info("Check if your Google Sheet has headers in the first row.")
    st.stop()

# --- CALCULATIONS ---
total_value = pd.to_numeric(df[col_val], errors='coerce').sum()
avg_eoq = pd.to_numeric(df[col_eoq], errors='coerce').mean()
class_a_count = len(df[df[col_abc].astype(str).str.contains('A', na=False)])

# --- DASHBOARD LAYOUT ---
st.title("⚡ EchoInv Terminal")
st.markdown("---")

# Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Inventory Value", f"${total_value:,.0f}")
m2.metric("Avg. Optimal EOQ", f"{avg_eoq:.0f}")
m3.metric("Total SKU Count", len(df))
m4.metric("High Priority (A)", class_a_count)

row1, row2 = st.columns([2, 1])

with row1:
    st.subheader("Cost Optimization Curve")
    # Simulation for the first item
    D = pd.to_numeric(df[col_demand], errors='coerce').iloc[0]
    Q_range = np.linspace(10, D if D > 10 else 1000, 100)
    # Using dummy costs if not in sheet to ensure chart renders
    S, H = 50, 2 
    costs = (D / Q_range) * S + (Q_range / 2) * H
    
    fig = px.line(x=Q_range, y=costs, labels={'x':'Quantity', 'y':'Total Cost'})
    fig.update_traces(line_color='#00FFA3', line_width=4)
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with row2:
    st.subheader("Value Distribution")
    fig_pie = px.pie(df, values=col_val, names=col_abc, hole=0.7,
                     color_discrete_sequence=['#00FFA3', '#BB86FC', '#343840'])
    fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("Inventory Intelligence Log")
st.dataframe(df[[col_article, col_abc, col_demand, col_eoq, col_val]].style.highlight_max(axis=0, color='#1d2a24'), use_container_width=True)

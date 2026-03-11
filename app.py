import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="Inventory Intel Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS FOR "ECHOFI" LOOK ---
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #0B0E11;
        color: #FFFFFF;
    }
    
    /* Card styling */
    div[data-testid="stMetricValue"] {
        background-color: #151921;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #2D333B;
    }
    
    /* Sidebar and headers */
    .css-1d391kg {
        background-color: #0B0E11;
    }
    
    /* Custom Metric Labels */
    [data-testid="stMetricLabel"] {
        color: #848E9C !important;
        font-size: 14px !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #00FFA3;
        color: black;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    # Linking your specific Google Sheet data
    sheet_id = "1QCCB2lUQm0pGZP-lGyrAi5MmBLK8v1gBoK6yGJWxDD0"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    df = pd.read_csv(url)
    
    # Cleaning column names (handling spaces from the sheet)
    df.columns = [c.strip() for c in df.columns]
    return df

try:
    df = load_data()
except:
    st.error("Please ensure the Google Sheet is public or the link is correct.")
    st.stop()

# --- HEADER SECTION ---
col_logo, col_search, col_nav = st.columns([1, 2, 2])
with col_logo:
    st.title("⚡ EchoInv")
with col_nav:
    st.write("### Inventory Optimization Terminal")

st.markdown("---")

# --- TOP KPI METRICS ---
# Calculated based on your sheet data
total_value = df['Annual Value'].sum()
avg_eoq = df['EOQ'].mean()
total_items = len(df)
class_a_count = len(df[df['Class ABC'] == 'A'])

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Inventory Value", f"${total_value/1000:,.1f}K", "+2.4%")
m2.metric("Optimal Avg EOQ", f"{avg_eoq:.0f} units", "-1.2%")
m3.metric("SKUs Monitored", total_items)
m4.metric("Class A Items", class_a_count, "High Priority")

# --- MAIN DASHBOARD AREA ---
row2_col1, row2_col2 = st.columns([2, 1])

with row2_col1:
    st.subheader("EOQ Cost Optimization Curve")
    # Generating a sample curve for the first item to show the "Modern Chart" look
    # Total Cost = (D/Q)*S + (Q/2)*H
    D = df['Annual Demand (D)'].iloc[0]
    S = df['Order Cost (S)'].iloc[0]
    H = df['Carrying Cost (h)'].iloc[0]
    Q_range = np.linspace(10, D/2, 100)
    
    order_costs = (D / Q_range) * S
    holding_costs = (Q_range / 2) * H
    total_costs = order_costs + holding_costs

    fig_eoq = go.Figure()
    fig_eoq.add_trace(go.Scatter(x=Q_range, y=order_costs, name="Ordering Cost", line=dict(color='#BB86FC', dash='dot')))
    fig_eoq.add_trace(go.Scatter(x=Q_range, y=holding_costs, name="Holding Cost", line=dict(color='#03DAC6', dash='dot')))
    fig_eoq.add_trace(go.Scatter(x=Q_range, y=total_costs, name="Total Cost", line=dict(color='#00FFA3', width=4)))
    
    fig_eoq.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_eoq, use_container_width=True)

with row2_col2:
    st.subheader("ABC Classification")
    # Donut Chart for ABC breakdown
    abc_counts = df.groupby('Class ABC')['Annual Value'].sum().reset_index()
    fig_pie = px.pie(
        abc_counts, 
        values='Annual Value', 
        names='Class ABC', 
        hole=0.7,
        color_discrete_sequence=['#00FFA3', '#BB86FC', '#2D333B']
    )
    fig_pie.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    # Add center text
    fig_pie.add_annotation(text="Value<br>Split", showarrow=False, font_size=20)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- DATA TABLE SECTION ---
st.subheader("Inventory Intelligence Terminal")
# Styling the dataframe
styled_df = df[['Article', 'Class ABC', 'Annual Demand (D)', 'EOQ', 'Reorder Point (ROP)', 'Annual Value']]

def color_abc(val):
    if val == 'A': return 'color: #00FFA3; font-weight: bold'
    if val == 'B': return 'color: #BB86FC'
    return 'color: #848E9C'

st.dataframe(
    styled_df.style.applymap(color_abc, subset=['Class ABC']),
    use_container_width=True
)

# --- FOOTER ---
st.markdown("<br><p style='text-align: center; color: #444;'>Connected to Real-time Excel Engine • Powered by EchoInv Intelligence</p>", unsafe_allow_html=True)

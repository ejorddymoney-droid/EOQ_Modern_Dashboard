import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EchoInv | Inventory Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- MODERN "ECHOFI" STYLING ---
st.markdown("""
    <style>
    /* Background and global text */
    .stApp {
        background-color: #0B0E11;
        color: #FFFFFF;
    }
    
    /* Metric Card Styling */
    div[data-testid="stMetricValue"] {
        background-color: #151921;
        padding: 15px 25px;
        border-radius: 12px;
        border: 1px solid #2D333B;
        color: #00FFA3 !important;
        font-family: 'Courier New', monospace;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #848E9C !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Hide Streamlit elements for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Dataframe Styling */
    .stDataFrame {
        border: 1px solid #2D333B;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SMART DATA LOADING FUNCTION ---
@st.cache_data
def load_and_clean_data():
    sheet_id = "1QCCB2lUQm0pGZP-lGyrAi5MmBLK8v1gBoK6yGJWxDD0"
    # We use gid=0 (the first tab). If your data is on a different tab, 
    # check the URL in your browser for the gid= number.
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    raw_df = pd.read_csv(url)
    
    # --- AUTOMATIC CLEANING ---
    # 1. If the first few rows are empty (common in Excel), find the first row with data
    if raw_df.columns[0].startswith('Unnamed'):
        # Try to find the actual header row
        for i in range(len(raw_df)):
            if not raw_df.iloc[i].isnull().all():
                new_header = raw_df.iloc[i]
                raw_df = raw_df[i+1:]
                raw_df.columns = new_header
                break

    # 2. Clean column names (remove spaces and special characters)
    raw_df.columns = [str(c).strip() for c in raw_df.columns]
    
    # 3. Remove any completely empty rows or columns
    raw_df = raw_df.dropna(how='all').dropna(axis=1, how='all')
    
    return raw_df

# --- FUZZY COLUMN MATCHER ---
def get_col(df, keywords):
    """Finds a column name in the dataframe that matches any of the keywords."""
    for col in df.columns:
        if any(key.lower() in col.lower() for key in keywords):
            return col
    return None

# --- EXECUTION ---
try:
    df = load_and_clean_data()
    
    # Identify key columns automatically
    col_article = get_col(df, ['Article', 'Item', 'Name', 'Produit'])
    col_val = get_col(df, ['Annual Value', 'Value', 'Total Value', 'Valeur'])
    col_demand = get_col(df, ['Demand', 'D', 'Consommation'])
    col_eoq = get_col(df, ['EOQ', 'Optimal', 'Q*'])
    col_abc = get_col(df, ['Class', 'ABC', 'Catégorie'])
    col_rop = get_col(df, ['ROP', 'Reorder', 'Point de commande'])

    # Ensure critical columns are numbers
    for c in [col_val, col_demand, col_eoq, col_rop]:
        if c: df[c] = pd.to_numeric(df[c].astype(str).str.replace('[$,]', '', regex=True), errors='coerce')

    # --- TOP HEADER ---
    st.markdown("<h1 style='text-align: left; color: white;'>⚡ EchoInv Terminal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #848E9C;'>Supply Chain & Inventory Intelligence Engine</p>", unsafe_allow_html=True)
    st.write("---")

    # --- KPI ROW ---
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        val = df[col_val].sum() if col_val else 0
        st.metric("Total Value", f"${val:,.0f}")
    with k2:
        eoq = df[col_eoq].mean() if col_eoq else 0
        st.metric("Avg Optimal EOQ", f"{eoq:,.0f}")
    with k3:
        st.metric("SKUs Tracked", len(df))
    with k4:
        a_count = len(df[df[col_abc].astype(str).str.contains('A', na=False)]) if col_abc else 0
        st.metric("Class A Items", a_count)

    st.write("##")

    # --- MAIN VISUALS ---
    row1_left, row1_right = st.columns([2, 1])

    with row1_left:
        st.markdown("### Cost Optimization Curve (Top SKU)")
        # We simulate a curve based on the first item's demand
        if col_demand:
            D = df[col_demand].iloc[0]
            Q_range = np.linspace(max(1, D*0.05), D*1.5, 100)
            # Default cost assumptions if not in sheet
            S, h = 50, 2 
            holding_cost = (Q_range / 2) * h
            ordering_cost = (D / Q_range) * S
            total_cost = holding_cost + ordering_cost
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=Q_range, y=total_cost, name='Total Cost', line=dict(color='#00FFA3', width=4)))
            fig.add_trace(go.Scatter(x=Q_range, y=holding_cost, name='Holding', line=dict(color='#BB86FC', dash='dot')))
            fig.add_trace(go.Scatter(x=Q_range, y=ordering_cost, name='Ordering', line=dict(color='#848E9C', dash='dot')))
            
            fig.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=20, b=0), height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

    with row1_right:
        st.markdown("### ABC Distribution")
        if col_abc and col_val:
            fig_abc = px.pie(df, values=col_val, names=col_abc, hole=0.7,
                             color_discrete_sequence=['#00FFA3', '#BB86FC', '#2D333B'])
            fig_abc.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=20, b=0), height=350, showlegend=False
            )
            fig_abc.add_annotation(text="VALUE %", showarrow=False, font_size=14)
            st.plotly_chart(fig_abc, use_container_width=True)

    # --- TABLE SECTION ---
    st.markdown("### Detailed Inventory Intelligence")
    # Display the cleaned dataframe
    cols_to_show = [c for c in [col_article, col_abc, col_demand, col_eoq, col_rop, col_val] if c]
    st.dataframe(df[cols_to_show].style.format(precision=0), use_container_width=True)

except Exception as e:
    st.error("### ⚠️ Application Error")
    st.write("The engine couldn't process the Google Sheet correctly.")
    st.info("Check if your Google Sheet is shared as 'Anyone with the link can view'.")
    with st.expander("Technical details for debugging"):
        st.write(e)
        if 'df' in locals():
            st.write("Columns found:", df.columns.tolist())

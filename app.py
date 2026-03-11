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

# --- ADVANCED DATA ENGINE (Finds headers automatically) ---
def load_live_data():
    # YOUR UPDATED LINK
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTRBP7-Jh2bfZF7BbU13MSw_5p0oESN3xvAQd9R-0SxHSqNjPiGYI5LqfwokRXBcMMTUcLEgzfWaiUm/pub?gid=438856952&single=true&output=csv"
    
    try:
        # Read the whole sheet first
        raw_df = pd.read_csv(url, header=None)
        
        # FIND THE HEADER ROW: Look for the row containing "Article" or "Annual Value"
        header_row_index = 0
        for i, row in raw_df.iterrows():
            row_str = " ".join([str(val).lower() for val in row.values])
            if "article" in row_str or "annual" in row_str:
                header_row_index = i
                break
        
        # Re-read or slice the dataframe from the correct header
        df = raw_df.iloc[header_row_index:].copy()
        df.columns = df.iloc[0] # Set the found row as header
        df = df[1:].reset_index(drop=True) # Remove the header row from the data
        
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        
        # --- ROBUST COLUMN MAPPING ---
        mapping = {
            'Article': ['article', 'item'],
            'Class ABC': ['class', 'abc', 'cat'],
            'Demand': ['demand', 'consommation', 'd'],
            'EOQ': ['eoq', 'optimal', 'q*'],
            'Value': ['value', 'valeur', 'annual value']
        }
        
        final_mapping = {}
        for std, keys in mapping.items():
            for col in df.columns:
                if any(k in col.lower() for k in keys):
                    final_mapping[col] = std
                    break
        df = df.rename(columns=final_mapping)

        # Force Numeric and Cleanup
        numeric_cols = ['Demand', 'EOQ', 'Value']
        for c in numeric_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace('[$,]', '', regex=True), errors='coerce').fillna(0)
                if c == 'EOQ':
                    df['EOQ_Size'] = df[c].apply(lambda x: x if x > 0 else 0.5)

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

if df.empty:
    st.error("Data could not be loaded. Please ensure your Google Sheet is published to web as CSV.")
    st.stop()

# --- SIDEBAR FILTERS ---
# Safely find ABC Column
abc_col = 'Class ABC' if 'Class ABC' in df.columns else None
if abc_col:
    abc_options = sorted(list(df[abc_col].unique()))
    abc_filter = st.sidebar.multiselect(f"Filter {abc_col}", options=abc_options, default=abc_options)
    filtered_df = df[df[abc_col].isin(abc_filter)]
else:
    filtered_df = df

# --- KPI ROW ---
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Value", f"${filtered_df['Value'].sum():,.0f}" if 'Value' in filtered_df.columns else "$0")
k2.metric("Avg EOQ", f"{filtered_df['EOQ'].mean():.0f}" if 'EOQ' in filtered_df.columns else "0")
k3.metric("SKU Count", len(filtered_df))
k4.metric("Status", "Connected ✅")

st.markdown("---")

# --- CHARTS ---
if not filtered_df.empty:
    chart_1, chart_2 = st.columns([2, 1])
    
    with chart_1:
        st.subheader("Inventory Distribution")
        try:
            fig = px.scatter(
                filtered_df, 
                x="Demand", 
                y="Value", 
                size="EOQ_Size" if 'EOQ_Size' in filtered_df.columns else None, 
                color="Class ABC" if 'Class ABC' in filtered_df.columns else None,
                hover_name="Article" if 'Article' in filtered_df.columns else None,
                color_discrete_sequence=['#00FFA3', '#BB86FC', '#848E9C'],
                size_max=40
            )
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Add more data to generate the scatter chart.")
            
    with chart_2:
        st.subheader("Value Split")
        if 'Value' in filtered_df.columns and 'Class ABC' in filtered_df.columns:
            fig_pie = px.pie(filtered_df, values='Value', names='Class ABC', hole=0.7,
                             color_discrete_sequence=['#00FFA3', '#BB86FC', '#2D333B'])
            fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

# --- TABLE ---
st.subheader("📝 Live Inventory Terminal Editor")
st.data_editor(st.session_state.inventory_data, num_rows="dynamic", use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="EchoInv | Terminal", layout="wide", page_icon="⚡")

# --- MODERN STYLING (EchoFi Aesthetic) ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E11; color: #FFFFFF; }
    
    /* Metric Cards */
    div[data-testid="stMetricValue"] { 
        background-color: #151921; padding: 20px; border-radius: 12px; 
        border: 1px solid #2D333B; color: #00FFA3 !important; 
        font-family: 'Courier New', monospace; font-size: 2rem !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0B0E11; border-right: 1px solid #2D333B; }
    
    /* Table Styling */
    .stDataFrame { background-color: #151921; border-radius: 10px; border: 1px solid #2D333B; }
    
    /* Button Styling */
    .stButton>button { 
        background-color: #00FFA3; color: black; border-radius: 8px; 
        border: none; font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #00cc82; transform: scale(1.02); }
    
    /* Form Background */
    .stExpander { background-color: #151921; border: 1px solid #2D333B; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ROBUST DATA ENGINE ---
@st.cache_data(ttl=60) # Refresh data every minute
def load_live_data():
    # YOUR NEW PUBLISHED LINK
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTRBP7-Jh2bfZF7BbU13MSw_5p0oESN3xvAQd9R-0SxHSqNjPiGYI5LqfwokRXBcMMTUcLEgzfWaiUm/pub?output=csv"
    
    try:
        df = pd.read_csv(url)
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        
        # Standardizing column names for the logic
        mapping = {
            'Article': ['article', 'item', 'name'],
            'Class': ['class', 'abc', 'cat'],
            'Demand': ['demand', 'consommation', 'd'],
            'EOQ': ['eoq', 'optimal', 'q*'],
            'Value': ['value', 'valeur', 'annual value']
        }
        
        new_cols = {}
        for std, keys in mapping.items():
            for col in df.columns:
                if any(k in col.lower() for k in keys):
                    new_cols[col] = std
                    break
        df = df.rename(columns=new_cols)
        
        # Numeric cleanup (removing $ and ,)
        for c in ['Demand', 'EOQ', 'Value']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace('[$,]', '', regex=True), errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame(columns=['Article', 'Class', 'Demand', 'EOQ', 'Value'])

# Initialize Session State
if 'inventory_data' not in st.session_state:
    st.session_state.inventory_data = load_live_data()

# --- HEADER SECTION ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("⚡ EchoInv Interactive Terminal")
    st.write("Live Supply Chain Intelligence • Connected to Google Sheets")
with col_h2:
    if st.button("🔄 Sync with Google Sheets"):
        st.session_state.inventory_data = load_live_data()
        st.rerun()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🎛️ Terminal Controls")
abc_options = list(st.session_state.inventory_data['Class'].unique()) if 'Class' in st.session_state.inventory_data.columns else ['A', 'B', 'C']
abc_filter = st.sidebar.multiselect("Filter Class", options=abc_options, default=abc_options)

# Processing Data
df = st.session_state.inventory_data
filtered_df = df[df['Class'].isin(abc_filter)] if 'Class' in df.columns else df

# --- KPI ROW ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Value", f"${filtered_df['Value'].sum():,.0f}" if 'Value' in filtered_df.columns else "$0")
m2.metric("Avg EOQ", f"{filtered_df['EOQ'].mean():.0f}" if 'EOQ' in filtered_df.columns else "0")
m3.metric("Total SKUs", len(filtered_df))
m4.metric("Active Classes", ", ".join(abc_filter))

st.markdown("---")

# --- CHARTS SECTION ---
if not filtered_df.empty:
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Inventory Distribution (Demand vs Value)")
        fig = px.scatter(filtered_df, x="Demand", y="Value", size="EOQ", color="Class",
                         hover_name="Article", color_discrete_sequence=['#00FFA3', '#BB86FC', '#848E9C'])
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("Value Split by ABC")
        fig_pie = px.pie(filtered_df, values='Value' if 'Value' in filtered_df.columns else None, 
                         names='Class' if 'Class' in filtered_df.columns else None, 
                         hole=0.7, color_discrete_sequence=['#00FFA3', '#BB86FC', '#2D333B'])
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

# --- INTERACTIVE DATA ENTRY ---
with st.expander("➕ Add New Inventory Item"):
    with st.form("entry_form", clear_on_submit=True):
        f1, f2, f3, f4 = st.columns(4)
        name = f1.text_input("Article Name")
        abc = f2.selectbox("Class", ['A', 'B', 'C'])
        dem = f3.number_input("Annual Demand", min_value=0)
        val = f4.number_input("Annual Value ($)", min_value=0)
        
        if st.form_submit_button("Update Local Terminal"):
            # Math: EOQ = Sqrt( (2*D*S)/H ) -> simplified calc for UI
            new_eoq = np.sqrt((2 * dem * 50) / 2) 
            new_row = pd.DataFrame([{'Article': name, 'Class': abc, 'Demand': dem, 'EOQ': new_eoq, 'Value': val}])
            st.session_state.inventory_data = pd.concat([st.session_state.inventory_data, new_row], ignore_index=True)
            st.rerun()

# --- LIVE EDITOR ---
st.subheader("📝 Live Inventory Editor")
st.caption("Double-click any cell to edit. Changes reflect in charts instantly but stay in this session until exported.")
edited_df = st.data_editor(st.session_state.inventory_data, num_rows="dynamic", use_container_width=True)

if st.button("💾 Save Table Changes"):
    st.session_state.inventory_data = edited_df
    st.toast("Terminal Data Updated!", icon="✅")

# --- EXPORT ---
st.sidebar.markdown("---")
csv = edited_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Export CSV", data=csv, file_name="inventory_update.csv", mime="text/csv")

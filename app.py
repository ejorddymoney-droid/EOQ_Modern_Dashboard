import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="EchoInv | Terminal", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E11; color: #FFFFFF; }
    [data-testid="stMetricValue"] { background-color: #151921; padding: 15px; border-radius: 12px; border: 1px solid #2D333B; color: #00FFA3 !important; }
    .stDataFrame { background-color: #151921; border-radius: 10px; }
    .stButton>button { background-color: #00FFA3; color: black; border-radius: 8px; width: 100%; border: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SMART COLUMN DETECTOR ---
def find_and_rename_cols(df):
    """Detects columns by keywords and renames them for the app logic."""
    mapping = {
        'Article': ['article', 'item', 'name', 'produit'],
        'ABC': ['class', 'abc', 'cat'],
        'Demand': ['demand', 'consommation', 'qty', 'd'],
        'EOQ': ['eoq', 'optimal', 'q*'],
        'Value': ['value', 'valeur', 'total', 'annual value']
    }
    new_cols = {}
    for standard_name, keywords in mapping.items():
        for col in df.columns:
            if any(key in str(col).lower() for key in keywords):
                new_cols[col] = standard_name
                break
    return df.rename(columns=new_cols)

# --- DATA INITIALIZATION ---
if 'inventory_data' not in st.session_state:
    sheet_id = "1QCCB2lUQm0pGZP-lGyrAi5MmBLK8v1gBoK6yGJWxDD0"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    try:
        raw_df = pd.read_csv(url)
        # 1. Clean whitespace
        raw_df.columns = [str(c).strip() for c in raw_df.columns]
        # 2. Rename to standard names
        df = find_and_rename_cols(raw_df)
        # 3. Force Numeric
        for c in ['Demand', 'EOQ', 'Value']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace('[$,]', '', regex=True), errors='coerce').fillna(0)
        
        st.session_state.inventory_data = df
    except Exception as e:
        st.error(f"Could not connect to Google Sheet. Using empty template. Error: {e}")
        st.session_state.inventory_data = pd.DataFrame(columns=['Article', 'ABC', 'Demand', 'EOQ', 'Value'])

# --- APP LAYOUT ---
df = st.session_state.inventory_data

st.title("⚡ EchoInv Interactive Terminal")

# Sidebar
abc_filter = st.sidebar.multiselect("Filter by Class", options=['A', 'B', 'C'], default=['A', 'B', 'C'])
filtered_df = df[df['ABC'].astype(str).str.contains('|'.join(abc_filter), na=False)]

# --- METRICS ---
m1, m2, m3, m4 = st.columns(4)
total_val = filtered_df['Value'].sum() if 'Value' in filtered_df.columns else 0
avg_eoq = filtered_df['EOQ'].mean() if 'EOQ' in filtered_df.columns else 0

m1.metric("Total Value", f"${total_val:,.0f}")
m2.metric("Avg EOQ", f"{avg_eoq:.0f}")
m3.metric("SKU Count", len(filtered_df))
m4.metric("Active Filters", ", ".join(abc_filter))

# --- FORM & CHARTS ---
with st.expander("➕ Add New Inventory Item"):
    with st.form("new_item"):
        c1, c2, c3, c4 = st.columns(4)
        n_name = c1.text_input("Name")
        n_abc = c2.selectbox("Class", ['A', 'B', 'C'])
        n_dem = c3.number_input("Demand", min_value=0)
        n_val = c4.number_input("Value ($)", min_value=0)
        if st.form_submit_button("Add Item"):
            n_eoq = np.sqrt((2 * n_dem * 50) / 2) # Sample calc
            new_row = pd.DataFrame([{'Article': n_name, 'ABC': n_abc, 'Demand': n_dem, 'EOQ': n_eoq, 'Value': n_val}])
            st.session_state.inventory_data = pd.concat([st.session_state.inventory_data, new_row], ignore_index=True)
            st.rerun()

# Check if we have data before plotting
if not filtered_df.empty and 'Value' in filtered_df.columns:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Top Items by Value")
        top_10 = filtered_df.sort_values('Value', ascending=False).head(10)
        fig = px.bar(top_10, x='Article', y='Value', color='ABC', color_discrete_sequence=['#00FFA3', '#BB86FC', '#848E9C'])
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Value Split")
        fig_pie = px.pie(filtered_df, values='Value', names='ABC', hole=0.7, color_discrete_sequence=['#00FFA3', '#BB86FC', '#2D333B'])
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.warning("No data found matching your filters. Add items or check your Google Sheet.")

# --- DATA EDITOR ---
st.subheader("📝 Live Inventory Editor")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
if st.button("Save Changes"):
    st.session_state.inventory_data = edited_df
    st.success("Data updated!")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="EchoInv | Interactive Terminal", layout="wide")

# --- CUSTOM CSS (MODERN DARK MODE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E11; color: #FFFFFF; }
    [data-testid="stMetricValue"] { background-color: #151921; padding: 15px; border-radius: 12px; border: 1px solid #2D333B; color: #00FFA3 !important; }
    .stDataFrame { background-color: #151921; border-radius: 10px; }
    .stButton>button { background-color: #00FFA3; color: black; border-radius: 8px; width: 100%; border: none; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #151921; color: white; border: 1px solid #2D333B; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA INITIALIZATION ---
if 'inventory_data' not in st.session_state:
    # Initial load from your Google Sheet
    sheet_id = "1QCCB2lUQm0pGZP-lGyrAi5MmBLK8v1gBoK6yGJWxDD0"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        # Cleanup numeric columns
        for col in ['Annual Demand (D)', 'EOQ', 'Annual Value']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('[$,]', '', regex=True), errors='coerce')
        st.session_state.inventory_data = df
    except:
        # Fallback if URL fails
        st.session_state.inventory_data = pd.DataFrame(columns=['Article', 'Class ABC', 'Annual Demand (D)', 'EOQ', 'Annual Value'])

# --- SIDEBAR FILTERS ---
st.sidebar.title("🎛️ Controls")
abc_filter = st.sidebar.multiselect("Filter by Class", options=['A', 'B', 'C'], default=['A', 'B', 'C'])

# --- HEADER ---
st.title("⚡ EchoInv Interactive Terminal")
st.markdown("Edit cells below or use the form to add new inventory items.")

# --- DATA ENTRY FORM ---
with st.expander("➕ Add New Inventory Item"):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        new_name = col1.text_input("Article Name")
        new_abc = col2.selectbox("Class", ['A', 'B', 'C'])
        new_demand = col3.number_input("Annual Demand", min_value=0)
        new_value = col4.number_input("Annual Value ($)", min_value=0)
        
        submit = st.form_submit_button("Add to Dashboard")
        
        if submit:
            # Logic to calculate EOQ (Simplified for the demo)
            new_eoq = np.sqrt((2 * new_demand * 50) / 2) # Assume S=50, H=2
            new_row = pd.DataFrame([{
                'Article': new_name, 'Class ABC': new_abc, 
                'Annual Demand (D)': new_demand, 'EOQ': new_eoq, 
                'Annual Value': new_value
            }])
            st.session_state.inventory_data = pd.concat([st.session_state.inventory_data, new_row], ignore_index=True)
            st.toast("Item added successfully!", icon="✅")

# --- PROCESSING DATA ---
working_df = st.session_state.inventory_data
filtered_df = working_df[working_df['Class ABC'].isin(abc_filter)]

# --- KPI ROW ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Value", f"${filtered_df['Annual Value'].sum():,.0f}")
m2.metric("Avg EOQ", f"{filtered_df['EOQ'].mean():.0f}")
m3.metric("SKU Count", len(filtered_df))
m4.metric("Class A Value", f"${filtered_df[filtered_df['Class ABC'] == 'A']['Annual Value'].sum():,.0f}")

# --- INTERACTIVE CHARTS ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("EOQ Strategy Analysis")
    # Show trend of top 10 items
    top_10 = filtered_df.nlargest(10, 'Annual Value')
    fig = px.bar(top_10, x='Article', y=['Annual Demand (D)', 'EOQ'], 
                 barmode='group', color_discrete_sequence=['#BB86FC', '#00FFA3'])
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Value Split")
    fig_pie = px.pie(filtered_df, values='Annual Value', names='Class ABC', hole=0.7,
                     color_discrete_sequence=['#00FFA3', '#BB86FC', '#2D333B'])
    fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- EDITABLE DATA TABLE ---
st.subheader("📝 Live Inventory Editor")
st.info("You can edit any cell below. The charts above will update automatically.")
edited_df = st.data_editor(
    filtered_df, 
    num_rows="dynamic", 
    use_container_width=True,
    key="editor"
)

# Update session state if editor changes
if st.button("Save Changes"):
    st.session_state.inventory_data.update(edited_df)
    st.success("Changes saved to session!")

# --- DOWNLOAD ---
csv = edited_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Export Data to CSV", data=csv, file_name="inventory_update.csv", mime="text/csv")

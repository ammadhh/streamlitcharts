#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="FPDS Contract Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

#######################
# Load data
df = pd.read_csv('fpds_data.csv')

# Convert date to datetime and extract the year for filtering
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['year'] = df['date'].dt.year

#######################
# Sidebar
with st.sidebar:
    st.title('📊 FPDS Contract Dashboard')
    
    # Create a list of available years from the dataset
    year_list = sorted(df['year'].dropna().unique(), reverse=True)
    selected_year = st.selectbox('Select a Year', year_list)
    
    # Filter the data based on selected year
    df_year = df[df['year'] == selected_year].copy()
    
    # Select a color theme for visualizations
    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a Color Theme', color_theme_list)
    
    # Checkbox to display an extra graph for contract value distribution
    show_distribution = st.checkbox("Show Contract Value Distribution Graph")

#######################
# Data Aggregation & Visualizations

# Choropleth Map: Aggregate total contract value per state
df_state = df_year.groupby('entity_state', as_index=False)['value'].sum()

def make_choropleth(input_df, state_col, value_col, color_theme):
    choropleth = px.choropleth(
        input_df,
        locations=state_col,
        color=value_col,
        locationmode="USA-states",
        color_continuous_scale=color_theme,
        range_color=(0, input_df[value_col].max()),
        scope="usa",
        labels={value_col: 'Total Contract Value'}
    )
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return choropleth

choropleth_map = make_choropleth(df_state, 'entity_state', 'value', selected_color_theme)

# Key Metrics: Highest and Lowest Contract by value
if not df_year.empty:
    top_contract = df_year.sort_values('value', ascending=False).iloc[0]
    bottom_contract = df_year.sort_values('value').iloc[0]
    
    metric_top = f"${top_contract['value']:,.2f}"
    metric_bottom = f"${bottom_contract['value']:,.2f}"
else:
    metric_top = metric_bottom = "N/A"

# Bar Chart: Total contract value by agency for the selected year
df_agency = df_year.groupby('agency', as_index=False)['value'].sum().sort_values('value', ascending=False)
bar_chart = alt.Chart(df_agency).mark_bar().encode(
    x=alt.X('agency:N', sort='-y', title='Agency'),
    y=alt.Y('value:Q', title='Total Contract Value')
).properties(
    width=600,
    height=300
).configure_axis(
    labelFontSize=12,
    titleFontSize=14
)

#######################
# Dashboard Layout

# Top Row: Two columns for metrics and visualizations
col1, col2 = st.columns((1.5, 4.5), gap='medium')

with col1:
    st.markdown('#### Contract Metrics')
    st.metric(label="Highest Contract", value=metric_top, delta=f"Agency: {top_contract['agency']}" if not df_year.empty else "")
    st.metric(label="Lowest Contract", value=metric_bottom, delta=f"Agency: {bottom_contract['agency']}" if not df_year.empty else "")
    
    st.markdown('#### Contracts by Agency')
    st.altair_chart(bar_chart, use_container_width=True)

with col2:
    st.markdown('#### Total Contract Value by State')
    st.plotly_chart(choropleth_map, use_container_width=True)
    
    # Optional: Heatmap visualization (if 'year' column exists)
    if 'year' in df.columns:
        df_heatmap = df.groupby(['year', 'agency'], as_index=False)['value'].sum()
        heatmap = alt.Chart(df_heatmap).mark_rect().encode(
            x=alt.X('agency:N', title='Agency'),
            y=alt.Y('year:O', title='Year'),
            color=alt.Color('value:Q', scale=alt.Scale(scheme=selected_color_theme), title='Contract Value')
        ).properties(
            width=900,
            height=300
        )
        st.altair_chart(heatmap, use_container_width=True)

#######################
# Optional Extra Graph: Contract Value Distribution
if show_distribution:
    st.markdown('#### Contract Value Distribution')
    distribution_chart = alt.Chart(df_year).mark_bar().encode(
        alt.X("value:Q", bin=alt.Bin(maxbins=30), title="Contract Value"),
        alt.Y("count()", title="Number of Contracts")
    ).properties(
        width=900,
        height=300
    )
    st.altair_chart(distribution_chart, use_container_width=True)

#######################
# Bottom Row: Full-width Contracts Data Table
st.markdown('#### Contracts Data')
st.dataframe(
    df_year.sort_values('value', ascending=False),
    height=600,
    hide_index=True,
    column_config={
        "agency": st.column_config.TextColumn("Agency"),
        "value": st.column_config.ProgressColumn("Contract Value", format="$%f", min_value=0, max_value=df_year['value'].max() if not df_year.empty else 0),
        "vendor": st.column_config.TextColumn("Vendor"),
        "entity_state": st.column_config.TextColumn("State")
    }
)

with st.expander('About', expanded=True):
    st.write('''
        - **Data Source**: FPDS (Federal Procurement Data System).
        - **Metrics**: Shows the highest and lowest contract values for the selected year.
        - **Map**: Aggregates the total contract value per U.S. state.
        - **Bar Chart**: Displays total contract value by agency.
        - **Heatmap**: (Optional) Visualizes trends over the years by agency.
        - **Distribution Graph**: (Optional) Displays the distribution of contract values for the selected year.
    ''')

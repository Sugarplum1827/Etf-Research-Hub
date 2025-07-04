import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime
import os

from etf_data_service import ETFDataService
from chart_utils import ChartUtils
from comparison_utils import ComparisonUtils

# Initialize services
@st.cache_resource
def get_etf_service():
    return ETFDataService()

@st.cache_resource
def get_chart_utils():
    return ChartUtils()

@st.cache_resource
def get_comparison_utils():
    return ComparisonUtils()

def main():
    st.set_page_config(
        page_title="ETF Research Center",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize services
    etf_service = get_etf_service()
    chart_utils = get_chart_utils()
    comparison_utils = get_comparison_utils()
    
    # Title and header
    st.title("📊 ETF Research Center")
    st.markdown("Comprehensive ETF analysis and comparison tool")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Use radio buttons for better navigation experience
    page = st.sidebar.radio(
        "Select Page",
        ["ETF Search & Analysis", "ETF Comparison", "Market Overview"],
        index=0
    )
    
    if page == "ETF Search & Analysis":
        show_etf_analysis_page(etf_service, chart_utils)
    elif page == "ETF Comparison":
        show_comparison_page(etf_service, comparison_utils, chart_utils)
    else:
        show_market_overview_page(etf_service, chart_utils)

def show_etf_analysis_page(etf_service, chart_utils):
    st.header("🔍 ETF Search & Analysis")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            "Search ETF by Symbol or Name",
            placeholder="Enter ETF symbol (e.g., VTI, VOO, ARKK) or fund name",
            help="Search for ETFs by their ticker symbol or fund name"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary")
    
    # Show ETF search results or default content
    has_searched = search_term or search_button
    
    if has_searched:
        if search_term:
            with st.spinner("Fetching real-time ETF data..."):
                etf_data = etf_service.search_etf(search_term)
            
            if etf_data:
                display_etf_details(etf_data, chart_utils)
            else:
                st.error(f"No ETF found for '{search_term}'. Please check the symbol and try again.")
                st.info("💡 Try searching with popular ETF symbols like: VTI, VOO, SPY, QQQ, ARKK, VEA, VWO")
        else:
            st.warning("Please enter an ETF symbol or name to search.")
    else:
        # Show top 10 ETFs when no search is performed
        show_top_etfs_section(etf_service, chart_utils)

def display_etf_details(etf_data, chart_utils):
    # Fund Overview Section
    st.subheader("📋 Fund Overview")
    
    # Create overview metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Fund Name", etf_data.get('name', 'N/A'))
        st.metric("Ticker Symbol", etf_data.get('symbol', 'N/A'))
    
    with col2:
        st.metric("Issuer", etf_data.get('issuer', 'N/A'))
        st.metric("Category", etf_data.get('category', 'N/A'))
    
    with col3:
        expense_ratio = etf_data.get('expense_ratio', 'N/A')
        if expense_ratio != 'N/A' and expense_ratio is not None:
            st.metric("Expense Ratio", f"{expense_ratio:.4f}%")
        else:
            st.metric("Expense Ratio", "N/A")
    
    with col4:
        aum = etf_data.get('aum', 'N/A')
        st.metric("Assets Under Management", aum)
    
    # Price and Performance Metrics (if available)
    performance_data = etf_data.get('performance_data', {})
    if performance_data:
        st.subheader("📈 Price & Performance")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            current_price = etf_data.get('current_price')
            if current_price:
                st.metric("Current Price", f"${current_price:.2f}")
        
        with col2:
            day_change = etf_data.get('day_change')
            day_change_percent = etf_data.get('day_change_percent')
            if day_change and day_change_percent:
                st.metric("Day Change", f"${day_change:.2f}", f"{day_change_percent:.2f}%")
        
        with col3:
            year_return = performance_data.get('1_year_return')
            if year_return:
                st.metric("1 Year Return", f"{year_return:.2f}%")
        
        with col4:
            volatility = performance_data.get('volatility')
            if volatility:
                st.metric("Volatility", f"{volatility:.2f}%")
        
        with col5:
            volume = etf_data.get('volume')
            if volume:
                if volume >= 1e6:
                    st.metric("Volume", f"{volume/1e6:.1f}M")
                elif volume >= 1e3:
                    st.metric("Volume", f"{volume/1e3:.1f}K")
                else:
                    st.metric("Volume", f"{volume:,.0f}")
    
    # Description
    if etf_data.get('description'):
        st.markdown("**Description:**")
        st.write(etf_data['description'])
    
    st.divider()
    
    # Holdings Section
    holdings_data = etf_data.get('holdings', [])
    if holdings_data:
        st.subheader("📈 Top Holdings")
        
        holdings_df = pd.DataFrame(holdings_data)
        if not holdings_df.empty:
            # Format the holdings table
            if 'weight' in holdings_df.columns:
                holdings_df['Weight (%)'] = holdings_df['weight'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
            
            # Display the table
            display_columns = ['ticker', 'company_name', 'Weight (%)', 'sector', 'market_value']
            available_columns = [col for col in display_columns if col in holdings_df.columns]
            
            column_mapping = {
                'ticker': 'Ticker',
                'company_name': 'Company Name',
                'sector': 'Sector',
                'market_value': 'Market Value'
            }
            
            # Create display dataframe with proper column mapping
            display_df = holdings_df[available_columns].copy()
            
            # Rename columns one by one to avoid the typing issue
            for old_name, new_name in column_mapping.items():
                if old_name in display_df.columns:
                    display_df[new_name] = display_df[old_name]
                    display_df = display_df.drop(columns=[old_name])
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Holdings data is not available for this ETF.")
    else:
        st.info("Holdings data is not available for this ETF.")
    
    st.divider()
    
    # Sector Allocation Section
    sector_data = etf_data.get('sector_allocation', {})
    if sector_data:
        st.subheader("🥧 Sector Allocation")
        
        chart_type = st.radio(
            "Select Chart Type",
            ["Pie Chart", "Bar Chart"],
            horizontal=True
        )
        
        if chart_type == "Pie Chart":
            fig = chart_utils.create_sector_pie_chart(sector_data, etf_data.get('symbol', 'ETF'))
        else:
            fig = chart_utils.create_sector_bar_chart(sector_data, etf_data.get('symbol', 'ETF'))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sector allocation data is not available for this ETF.")
    
    # Performance Chart Section
    performance_data = etf_data.get('performance_data', {})
    if performance_data:
        st.divider()
        st.subheader("📈 Performance Analysis")
        
        fig = chart_utils.create_performance_chart(performance_data, etf_data.get('symbol', 'ETF'))
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance insights
        col1, col2 = st.columns(2)
        with col1:
            if performance_data.get('52_week_high') and performance_data.get('52_week_low'):
                st.metric(
                    "52-Week Range", 
                    f"${performance_data['52_week_low']:.2f} - ${performance_data['52_week_high']:.2f}"
                )
        
        with col2:
            if performance_data.get('current_vs_52w_high'):
                st.metric(
                    "% from 52W High", 
                    f"{performance_data['current_vs_52w_high']:.2f}%"
                )

def show_comparison_page(etf_service, comparison_utils, chart_utils):
    st.header("⚖️ ETF Comparison")
    
    # ETF Selection
    col1, col2 = st.columns(2)
    
    with col1:
        etf1_symbol = st.text_input(
            "First ETF Symbol",
            placeholder="e.g., VTI",
            help="Enter the symbol of the first ETF to compare"
        )
    
    with col2:
        etf2_symbol = st.text_input(
            "Second ETF Symbol",
            placeholder="e.g., VOO",
            help="Enter the symbol of the second ETF to compare"
        )
    
    compare_button = st.button("🔄 Compare ETFs", type="primary")
    
    if compare_button and etf1_symbol and etf2_symbol:
        with st.spinner("Loading ETF data for comparison..."):
            etf1_data = etf_service.search_etf(etf1_symbol)
            etf2_data = etf_service.search_etf(etf2_symbol)
        
        if etf1_data and etf2_data:
            display_etf_comparison(etf1_data, etf2_data, comparison_utils, chart_utils)
        else:
            if not etf1_data:
                st.error(f"Could not find data for ETF: {etf1_symbol}")
            if not etf2_data:
                st.error(f"Could not find data for ETF: {etf2_symbol}")
    elif compare_button:
        st.warning("Please enter both ETF symbols to compare.")

def display_etf_comparison(etf1_data, etf2_data, comparison_utils, chart_utils):
    # Basic Comparison
    st.subheader("📊 Basic Comparison")
    
    comparison_df = pd.DataFrame({
        'Metric': ['Fund Name', 'Issuer', 'Category', 'Expense Ratio (%)', 'AUM'],
        etf1_data.get('symbol', 'ETF 1'): [
            etf1_data.get('name', 'N/A'),
            etf1_data.get('issuer', 'N/A'),
            etf1_data.get('category', 'N/A'),
            etf1_data.get('expense_ratio', 'N/A'),
            etf1_data.get('aum', 'N/A')
        ],
        etf2_data.get('symbol', 'ETF 2'): [
            etf2_data.get('name', 'N/A'),
            etf2_data.get('issuer', 'N/A'),
            etf2_data.get('category', 'N/A'),
            etf2_data.get('expense_ratio', 'N/A'),
            etf2_data.get('aum', 'N/A')
        ]
    })
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Overlapping Holdings
    holdings1 = etf1_data.get('holdings', [])
    holdings2 = etf2_data.get('holdings', [])
    
    if holdings1 and holdings2:
        st.subheader("🔄 Overlapping Holdings")
        overlaps = comparison_utils.find_overlapping_holdings(holdings1, holdings2)
        
        if overlaps:
            overlap_df = pd.DataFrame(overlaps)
            st.dataframe(overlap_df, use_container_width=True, hide_index=True)
        else:
            st.info("No overlapping holdings found between these ETFs.")
    else:
        st.info("Holdings data is not available for comparison.")
    
    st.divider()
    
    # Sector Allocation Comparison
    sector1 = etf1_data.get('sector_allocation', {})
    sector2 = etf2_data.get('sector_allocation', {})
    
    if sector1 and sector2:
        st.subheader("🥧 Sector Allocation Comparison")
        
        fig = chart_utils.create_sector_comparison_chart(
            sector1, sector2,
            etf1_data.get('symbol', 'ETF 1'),
            etf2_data.get('symbol', 'ETF 2')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sector allocation data is not available for comparison.")

def show_market_overview_page(etf_service, chart_utils):
    st.header("🌍 Market Overview")
    st.info("Market overview functionality will display real-time ETF market data when connected to live data sources.")
    
    # Placeholder for market overview features
    st.subheader("Popular ETF Categories")
    
    categories = [
        "Large Cap Equity",
        "Technology",
        "Healthcare",
        "Financials",
        "International Developed",
        "Emerging Markets",
        "Fixed Income",
        "Real Estate"
    ]
    
    for category in categories:
        with st.expander(f"📂 {category}"):
            st.write(f"Popular ETFs in the {category} category will be displayed here when connected to live data.")

def show_top_etfs_section(etf_service, chart_utils):
    """Display top 10 ETFs section when no search is performed"""
    st.subheader("🏆 Top 10 Popular ETFs")
    st.markdown("Explore some of the most popular ETFs in the market. Click on any ETF to learn more!")
    
    # Get popular ETFs list
    popular_etfs = etf_service.get_popular_etfs()
    
    # Create a grid layout for ETF cards
    cols = st.columns(5)
    
    for i, etf_symbol in enumerate(popular_etfs):
        col_idx = i % 5
        with cols[col_idx]:
            with st.container():
                st.markdown(f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 5px 0;
                    text-align: center;
                    background-color: #f9f9f9;
                ">
                    <h4 style="margin: 0; color: #1f77b4;">{etf_symbol}</h4>
                    <p style="margin: 5px 0; font-size: 12px; color: #666;">
                        Click to analyze
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Analyze {etf_symbol}", key=f"btn_{etf_symbol}", use_container_width=True):
                    # Fetch and display ETF data
                    with st.spinner(f"Loading {etf_symbol} data..."):
                        etf_data = etf_service.search_etf(etf_symbol)
                    
                    if etf_data:
                        st.rerun()  # This will trigger a refresh and show the search results
    
    st.divider()
    
    # Add ETF categories overview
    st.subheader("📊 ETF Categories Overview")
    
    category_data = {
        'Large Cap Equity': ['SPY', 'VOO', 'VTI'],
        'Technology': ['QQQ', 'XLK', 'ARKK'],
        'International': ['VEA', 'VWO', 'IEFA'],
        'Fixed Income': ['AGG', 'BND', 'TLT'],
        'Sector Specific': ['XLF', 'XLE', 'XLV']
    }
    
    for category, etfs in category_data.items():
        with st.expander(f"📂 {category}"):
            st.write(f"Popular ETFs: {', '.join(etfs)}")
            
            # Create a simple visualization of the category
            fig = chart_utils.create_category_overview_chart(category, etfs)
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()

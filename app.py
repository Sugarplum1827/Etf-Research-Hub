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

@st.dialog("ETF Analysis")
def show_etf_modal(etf_service, chart_utils):
    """Display ETF information in a modal dialog"""
    if 'selected_etf' in st.session_state:
        etf_symbol = st.session_state.selected_etf
        
        with st.spinner(f"Loading {etf_symbol} data..."):
            etf_data = etf_service.search_etf(etf_symbol)
        
        if etf_data:
            # Display ETF details in the modal
            display_etf_details(etf_data, chart_utils)
        else:
            st.error(f"Could not load data for {etf_symbol}")
        
        # Close button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Close", use_container_width=True):
                st.session_state.show_etf_modal = False
                if 'selected_etf' in st.session_state:
                    del st.session_state.selected_etf
                st.rerun()

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
    
    # Handle ETF modal display
    if st.session_state.get('show_etf_modal', False):
        show_etf_modal(etf_service, chart_utils)

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
    # Enhanced Basic Comparison
    st.subheader("📊 Comprehensive ETF Comparison")
    
    # Performance Metrics Comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {etf1_data.get('symbol', 'ETF 1')}")
        perf1 = etf1_data.get('performance_data', {})
        st.metric("Current Price", f"${etf1_data.get('current_price', 'N/A')}")
        st.metric("1 Year Return", f"{perf1.get('1_year_return', 'N/A')}%" if perf1.get('1_year_return') else "N/A")
        st.metric("Volatility", f"{perf1.get('volatility', 'N/A')}%" if perf1.get('volatility') else "N/A")
        st.metric("Expense Ratio", f"{etf1_data.get('expense_ratio', 'N/A')}%" if etf1_data.get('expense_ratio') else "N/A")
    
    with col2:
        st.markdown(f"### {etf2_data.get('symbol', 'ETF 2')}")
        perf2 = etf2_data.get('performance_data', {})
        st.metric("Current Price", f"${etf2_data.get('current_price', 'N/A')}")
        st.metric("1 Year Return", f"{perf2.get('1_year_return', 'N/A')}%" if perf2.get('1_year_return') else "N/A")
        st.metric("Volatility", f"{perf2.get('volatility', 'N/A')}%" if perf2.get('volatility') else "N/A")
        st.metric("Expense Ratio", f"{etf2_data.get('expense_ratio', 'N/A')}%" if etf2_data.get('expense_ratio') else "N/A")
    
    st.divider()
    
    # Detailed Comparison Table
    st.subheader("📋 Detailed Comparison Table")
    
    comparison_df = pd.DataFrame({
        'Metric': [
            'Fund Name', 'Issuer', 'Category', 'Assets Under Management',
            'Current Price', 'Day Change', 'Volume', '52-Week High', '52-Week Low',
            '1 Year Return (%)', 'Volatility (%)', 'Expense Ratio (%)'
        ],
        etf1_data.get('symbol', 'ETF 1'): [
            etf1_data.get('name', 'N/A'),
            etf1_data.get('issuer', 'N/A'),
            etf1_data.get('category', 'N/A'),
            etf1_data.get('aum', 'N/A'),
            f"${etf1_data.get('current_price', 'N/A')}" if etf1_data.get('current_price') else 'N/A',
            f"${etf1_data.get('day_change', 'N/A')}" if etf1_data.get('day_change') else 'N/A',
            f"{etf1_data.get('volume', 'N/A'):,}" if etf1_data.get('volume') else 'N/A',
            f"${perf1.get('52_week_high', 'N/A')}" if perf1.get('52_week_high') else 'N/A',
            f"${perf1.get('52_week_low', 'N/A')}" if perf1.get('52_week_low') else 'N/A',
            f"{perf1.get('1_year_return', 'N/A')}" if perf1.get('1_year_return') else 'N/A',
            f"{perf1.get('volatility', 'N/A')}" if perf1.get('volatility') else 'N/A',
            f"{etf1_data.get('expense_ratio', 'N/A')}" if etf1_data.get('expense_ratio') else 'N/A'
        ],
        etf2_data.get('symbol', 'ETF 2'): [
            etf2_data.get('name', 'N/A'),
            etf2_data.get('issuer', 'N/A'),
            etf2_data.get('category', 'N/A'),
            etf2_data.get('aum', 'N/A'),
            f"${etf2_data.get('current_price', 'N/A')}" if etf2_data.get('current_price') else 'N/A',
            f"${etf2_data.get('day_change', 'N/A')}" if etf2_data.get('day_change') else 'N/A',
            f"{etf2_data.get('volume', 'N/A'):,}" if etf2_data.get('volume') else 'N/A',
            f"${perf2.get('52_week_high', 'N/A')}" if perf2.get('52_week_high') else 'N/A',
            f"${perf2.get('52_week_low', 'N/A')}" if perf2.get('52_week_low') else 'N/A',
            f"{perf2.get('1_year_return', 'N/A')}" if perf2.get('1_year_return') else 'N/A',
            f"{perf2.get('volatility', 'N/A')}" if perf2.get('volatility') else 'N/A',
            f"{etf2_data.get('expense_ratio', 'N/A')}" if etf2_data.get('expense_ratio') else 'N/A'
        ]
    })
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Performance Comparison Chart
    st.subheader("📈 Performance Comparison Chart")
    
    if perf1 and perf2:
        fig = chart_utils.create_performance_comparison_chart(
            perf1, perf2,
            etf1_data.get('symbol', 'ETF 1'),
            etf2_data.get('symbol', 'ETF 2')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Comprehensive Analysis Summary
    st.subheader("🎯 Analysis Summary")
    
    summary = comparison_utils.generate_comparison_summary(etf1_data, etf2_data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        expense_comp = summary.get('expense_ratio_comparison', {})
        if expense_comp.get('cheaper_etf'):
            st.metric(
                "Lower Cost ETF", 
                expense_comp['cheaper_etf'],
                f"Saves {expense_comp.get('savings_basis_points', 0)} bps"
            )
        else:
            st.metric("Cost Comparison", "Data unavailable")
    
    with col2:
        aum_comp = summary.get('aum_comparison', {})
        if aum_comp.get('larger_etf'):
            st.metric(
                "Larger ETF (AUM)", 
                aum_comp['larger_etf'],
                f"{aum_comp.get('size_ratio', 1):.1f}x larger"
            )
        else:
            st.metric("Size Comparison", "Data unavailable")
    
    with col3:
        portfolio_overlap = summary.get('portfolio_overlap', 0)
        st.metric("Portfolio Overlap", f"{portfolio_overlap:.1f}%")
    
    st.divider()
    
    # Overlapping Holdings
    holdings1 = etf1_data.get('holdings', [])
    holdings2 = etf2_data.get('holdings', [])
    
    if holdings1 and holdings2:
        st.subheader("🔄 Overlapping Holdings Analysis")
        overlaps = comparison_utils.find_overlapping_holdings(holdings1, holdings2)
        
        if overlaps:
            overlap_df = pd.DataFrame(overlaps)
            
            # Format the overlap data for better display
            if not overlap_df.empty:
                overlap_df['Weight ETF1 (%)'] = overlap_df['weight_etf1'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
                overlap_df['Weight ETF2 (%)'] = overlap_df['weight_etf2'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
                overlap_df['Weight Difference (%)'] = overlap_df['weight_difference'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
                
                display_columns = ['ticker', 'company_name', 'sector', 'Weight ETF1 (%)', 'Weight ETF2 (%)', 'Weight Difference (%)']
                available_columns = [col for col in display_columns if col in overlap_df.columns]
                
                # Create renamed dataframe for display
                display_df = overlap_df[available_columns].copy()
                column_renames = {
                    'ticker': 'Ticker',
                    'company_name': 'Company',
                    'sector': 'Sector'
                }
                
                for old_col, new_col in column_renames.items():
                    if old_col in display_df.columns:
                        display_df[new_col] = display_df[old_col]
                        display_df = display_df.drop(columns=[old_col])
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
            
            st.info(f"Found {len(overlaps)} overlapping holdings between the two ETFs.")
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
        
        # Sector similarity analysis
        sector_comp = comparison_utils.compare_sector_allocations(sector1, sector2)
        if sector_comp:
            st.metric(
                "Sector Similarity Score", 
                f"{sector_comp.get('similarity_score', 0):.1f}%",
                help="Higher scores indicate more similar sector allocations"
            )
    else:
        st.info("Sector allocation data is not available for comparison.")
    
    # Investment Recommendation
    st.divider()
    st.subheader("💡 Investment Considerations")
    
    considerations = []
    
    if expense_comp.get('cheaper_etf'):
        considerations.append(f"• {expense_comp['cheaper_etf']} has a lower expense ratio, potentially saving on long-term costs")
    
    if aum_comp.get('larger_etf'):
        considerations.append(f"• {aum_comp['larger_etf']} has larger assets under management, typically indicating higher liquidity")
    
    if portfolio_overlap > 70:
        considerations.append("• High portfolio overlap suggests similar investment exposure - consider diversification benefits")
    elif portfolio_overlap < 30:
        considerations.append("• Low portfolio overlap suggests good diversification potential when combined")
    
    if perf1.get('volatility') and perf2.get('volatility'):
        vol1, vol2 = perf1['volatility'], perf2['volatility']
        if abs(vol1 - vol2) > 5:
            lower_vol = etf1_data.get('symbol') if vol1 < vol2 else etf2_data.get('symbol')
            considerations.append(f"• {lower_vol} shows lower volatility, potentially suitable for risk-averse investors")
    
    if considerations:
        for consideration in considerations:
            st.write(consideration)
    else:
        st.write("• Detailed comparison requires more complete data for comprehensive analysis")
    
    st.warning("⚠️ **Investment Disclaimer:** This analysis is for informational purposes only. Consider consulting with a financial advisor before making investment decisions.")

def show_market_overview_page(etf_service, chart_utils):
    st.header("🌍 Market Overview")
    
    # Market Statistics Overview
    st.subheader("📊 Market Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total ETFs Tracked", "10+", help="Number of popular ETFs available for analysis")
    
    with col2:
        st.metric("Categories", "8", help="Different ETF categories covered")
    
    with col3:
        st.metric("Data Source", "Yahoo Finance", help="Real-time data provider")
    
    with col4:
        st.metric("Update Frequency", "Real-time", help="Data refresh frequency")
    
    st.divider()
    
    # Popular ETF Categories with Real Data
    st.subheader("🏆 Popular ETF Categories")
    
    category_etfs = {
        "Large Cap Equity": {
            "etfs": ["SPY", "VOO", "VTI"],
            "description": "Track large-cap U.S. stocks, typically S&P 500 or total market",
            "characteristics": ["Low expense ratios", "High liquidity", "Broad diversification"]
        },
        "Technology": {
            "etfs": ["QQQ", "XLK", "ARKK"],
            "description": "Focus on technology companies and innovation",
            "characteristics": ["Higher volatility", "Growth-oriented", "Innovation exposure"]
        },
        "International Developed": {
            "etfs": ["VEA", "IEFA", "EFA"],
            "description": "Exposure to developed markets outside the U.S.",
            "characteristics": ["Geographic diversification", "Currency exposure", "Different market cycles"]
        },
        "Fixed Income": {
            "etfs": ["AGG", "BND", "TLT"],
            "description": "Bond funds for income and portfolio stability",
            "characteristics": ["Lower volatility", "Income generation", "Interest rate sensitivity"]
        },
        "Emerging Markets": {
            "etfs": ["VWO", "EEM", "IEMG"],
            "description": "Exposure to developing country markets",
            "characteristics": ["Higher risk/return", "Growth potential", "Currency volatility"]
        },
        "Sector Specific": {
            "etfs": ["XLF", "XLE", "XLV"],
            "description": "Concentrated exposure to specific industry sectors",
            "characteristics": ["Sector concentration", "Targeted exposure", "Higher volatility"]
        }
    }
    
    for category, data in category_etfs.items():
        with st.expander(f"📂 {category}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Description:** {data['description']}")
                st.write("**Key Characteristics:**")
                for char in data['characteristics']:
                    st.write(f"• {char}")
            
            with col2:
                st.write("**Popular ETFs:**")
                for etf in data['etfs']:
                    if st.button(f"Analyze {etf}", key=f"market_{etf}", use_container_width=True):
                        st.session_state.selected_etf = etf
                        st.session_state.show_etf_modal = True
                        st.rerun()
    
    st.divider()
    
    # ETF Performance Comparison Chart
    st.subheader("📈 ETF Category Performance Overview")
    
    # Create a sample performance chart for different categories
    performance_data = {
        "Large Cap Equity": 12.5,
        "Technology": 18.3,
        "International": 8.7,
        "Fixed Income": 3.2,
        "Emerging Markets": 15.1,
        "Sector Specific": 11.8
    }
    
    fig = chart_utils.create_category_performance_chart(performance_data)
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Market Insights
    st.subheader("💡 Market Insights")
    
    insights = [
        "Technology ETFs have shown strong performance with higher volatility",
        "Large-cap equity ETFs provide stable, diversified exposure to U.S. markets",
        "International ETFs offer geographic diversification beyond U.S. markets",
        "Fixed income ETFs can provide portfolio stability and income generation",
        "Emerging market ETFs offer growth potential with higher risk"
    ]
    
    for insight in insights:
        st.write(f"• {insight}")
    
    # Risk Warning
    st.warning("⚠️ **Risk Disclaimer:** Past performance does not guarantee future results. ETF investments carry market risks including potential loss of principal.")

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
                    # Store the selected ETF in session state to show in modal
                    st.session_state.selected_etf = etf_symbol
                    st.session_state.show_etf_modal = True
                    st.rerun()
    
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

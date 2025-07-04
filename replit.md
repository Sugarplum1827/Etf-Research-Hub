# ETF Research Center

## Overview

This is a Streamlit-based web application for comprehensive ETF (Exchange-Traded Fund) research and analysis. The application provides ETF search capabilities, performance analysis, comparison tools, and market overview functionality. It integrates with multiple financial data APIs to provide real-time ETF information, holdings data, and performance metrics.

## System Architecture

The application follows a modular service-oriented architecture with clear separation of concerns:

- **Frontend**: Streamlit web framework for the user interface
- **Data Layer**: Multiple financial data APIs (Alpha Vantage, Polygon, free sources)
- **Business Logic**: Service classes for data processing and chart generation
- **Presentation Layer**: Interactive charts and visualizations using Plotly

## Key Components

### 1. Main Application (`app.py`)
- Entry point for the Streamlit application
- Navigation and page routing
- Service initialization with caching
- Multi-page architecture supporting:
  - ETF Search & Analysis
  - ETF Comparison
  - Market Overview

### 2. ETF Data Service (`etf_data_service.py`)
- **Purpose**: Centralized data fetching from multiple financial APIs
- **APIs Integrated**: Alpha Vantage, Polygon, and fallback free sources
- **Features**: ETF search by symbol or name, graceful API failover
- **Configuration**: Environment variable-based API key management

### 3. Chart Utilities (`chart_utils.py`)
- **Purpose**: Standardized chart creation and visualization
- **Chart Types**: Sector allocation pie charts, performance charts
- **Styling**: Consistent color palette and formatting
- **Technology**: Plotly for interactive visualizations

### 4. Comparison Utilities (`comparison_utils.py`)
- **Purpose**: ETF comparison and overlap analysis
- **Features**: Holdings overlap detection, weight comparison
- **Data Processing**: Pandas-based data manipulation for efficient comparisons

## Data Flow

1. **User Input**: ETF symbol or name entered through Streamlit interface
2. **Data Fetching**: ETFDataService attempts to fetch data from multiple APIs in priority order
3. **Data Processing**: Raw API data is cleaned and standardized
4. **Visualization**: ChartUtils generates interactive charts and graphs
5. **Comparison**: ComparisonUtils processes multiple ETFs for side-by-side analysis
6. **Display**: Results presented through Streamlit components

## External Dependencies

### APIs
- **Alpha Vantage**: Primary source for ETF data and financial metrics
- **Polygon**: Secondary data source for comprehensive market data
- **Free Sources**: Fallback options when premium APIs are unavailable

### Python Libraries
- **Streamlit**: Web application framework
- **Plotly**: Interactive charting and visualization
- **Pandas**: Data manipulation and analysis
- **Requests**: HTTP client for API calls

### Environment Variables
- `ETF_API_KEY`: Generic ETF API key
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API authentication
- `POLYGON_API_KEY`: Polygon.io API authentication

## Deployment Strategy

The application is designed for deployment on Replit with:
- **Streamlit Server**: Handles web interface and user interactions
- **Environment Configuration**: API keys managed through Replit secrets
- **Caching Strategy**: Streamlit's `@st.cache_resource` for service initialization
- **Stateless Design**: No persistent storage required, data fetched on-demand

Key deployment considerations:
- API rate limiting handled through multiple data sources
- Graceful degradation when APIs are unavailable
- Resource caching to minimize API calls and improve performance

## Recent Changes

- July 04, 2025 - Enhanced ETF Research App with real data integration:
  - Integrated yfinance for live ETF data from Yahoo Finance
  - Added top 10 popular ETFs section (appears by default, disappears after search)
  - Enhanced performance metrics display with price data, volatility, and 52-week ranges
  - Added interactive ETF category overview with visualization charts
  - Improved navigation from dropdown to radio buttons
  - Added comprehensive performance analysis charts
  - Real-time sector allocation data based on ETF types
  - Enhanced error handling and data formatting

## Changelog

- July 04, 2025. Initial setup
- July 04, 2025. Added yfinance integration and enhanced UI features

## User Preferences

Preferred communication style: Simple, everyday language.
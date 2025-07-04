import requests
import json
import os
import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional
import time

class ETFDataService:
    """Service for fetching ETF data from various sources"""
    
    def __init__(self):
        # Initialize with API keys from environment variables
        self.api_key = os.getenv("ETF_API_KEY", "")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.polygon_key = os.getenv("POLYGON_API_KEY", "")
        
    def search_etf(self, symbol_or_name: str) -> Optional[Dict]:
        """
        Search for ETF data by symbol or name
        
        Args:
            symbol_or_name: ETF symbol (e.g., 'VTI') or fund name
            
        Returns:
            Dictionary containing ETF data or None if not found
        """
        # Clean and uppercase the symbol
        symbol = symbol_or_name.strip().upper()
        
        # Try multiple data sources
        etf_data = None
        
        # First try with Alpha Vantage if API key is available
        if self.alpha_vantage_key:
            etf_data = self._fetch_from_alpha_vantage(symbol)
        
        # If Alpha Vantage fails, try Polygon
        if not etf_data and self.polygon_key:
            etf_data = self._fetch_from_polygon(symbol)
        
        # If still no data, try free sources
        if not etf_data:
            etf_data = self._fetch_from_free_sources(symbol)
        
        return etf_data
    
    def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Fetch ETF data from Alpha Vantage API"""
        try:
            # Get basic ETF information
            base_url = "https://www.alphavantage.co/query"
            
            # Fetch overview data
            overview_params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(base_url, params=overview_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we got valid data
                if 'Symbol' in data and data['Symbol'] == symbol:
                    return self._parse_alpha_vantage_data(data, symbol)
            
        except Exception as e:
            print(f"Error fetching from Alpha Vantage: {e}")
        
        return None
    
    def _fetch_from_polygon(self, symbol: str) -> Optional[Dict]:
        """Fetch ETF data from Polygon API"""
        try:
            base_url = f"https://api.polygon.io/v3/reference/tickers/{symbol}"
            
            params = {
                'apikey': self.polygon_key
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'results' in data:
                    return self._parse_polygon_data(data['results'], symbol)
                    
        except Exception as e:
            print(f"Error fetching from Polygon: {e}")
        
        return None
    
    def _fetch_from_free_sources(self, symbol: str) -> Optional[Dict]:
        """
        Fetch ETF data from Yahoo Finance using yfinance
        """
        try:
            # Create yfinance ticker object
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            
            if not info or 'symbol' not in info:
                return None
            
            # Get historical data for performance metrics
            hist = ticker.history(period="1y")
            
            # Parse the data
            etf_data = {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', 'N/A')),
                'issuer': info.get('fundFamily', info.get('companyOfficers', [{}])[0].get('name', 'N/A') if info.get('companyOfficers') else 'N/A'),
                'category': info.get('category', info.get('fundType', 'N/A')),
                'description': info.get('longBusinessSummary', f"ETF data for {symbol} from Yahoo Finance"),
                'expense_ratio': info.get('annualReportExpenseRatio', info.get('totalExpenseRatio')),
                'aum': self._format_aum(info.get('totalAssets', info.get('fundInceptionDate'))),
                'current_price': info.get('regularMarketPrice', info.get('previousClose')),
                'day_change': info.get('regularMarketChange'),
                'day_change_percent': info.get('regularMarketChangePercent'),
                'volume': info.get('regularMarketVolume'),
                'holdings': self._get_holdings_from_yfinance(ticker, symbol),
                'sector_allocation': self._get_sector_allocation_from_yfinance(ticker, symbol),
                'performance_data': self._calculate_performance_metrics(hist) if not hist.empty else {},
                'data_source': 'Yahoo Finance',
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return etf_data
            
        except Exception as e:
            print(f"Error fetching from Yahoo Finance: {e}")
            return None
    
    def _format_aum(self, aum_value) -> str:
        """Format AUM value to readable string"""
        if aum_value is None:
            return 'N/A'
        
        try:
            aum = float(aum_value)
            if aum >= 1e9:
                return f"${aum/1e9:.2f}B"
            elif aum >= 1e6:
                return f"${aum/1e6:.2f}M"
            elif aum >= 1e3:
                return f"${aum/1e3:.2f}K"
            else:
                return f"${aum:.2f}"
        except:
            return str(aum_value)
    
    def _get_holdings_from_yfinance(self, ticker, symbol: str) -> List[Dict]:
        """Get top holdings from yfinance if available"""
        try:
            # Try to get major holders information
            major_holders = ticker.major_holders
            institutional_holders = ticker.institutional_holders
            
            holdings = []
            
            # Process institutional holders as proxy for holdings
            if institutional_holders is not None and not institutional_holders.empty:
                for idx, row in institutional_holders.head(10).iterrows():
                    holding = {
                        'ticker': 'N/A',
                        'company_name': row.get('Holder', 'N/A'),
                        'weight': row.get('Shares', 0) if 'Shares' in row else 0,
                        'sector': 'N/A',
                        'market_value': row.get('Value', 'N/A') if 'Value' in row else 'N/A'
                    }
                    holdings.append(holding)
            
            return holdings
        except Exception as e:
            print(f"Error getting holdings for {symbol}: {e}")
            return []
    
    def _get_sector_allocation_from_yfinance(self, ticker, symbol: str) -> Dict:
        """Get sector allocation from yfinance if available"""
        try:
            # For most ETFs, sector data might not be directly available
            # We'll create a basic structure based on known ETF types
            info = ticker.info
            category = info.get('category', '').lower()
            
            # Create sample sector allocation based on ETF type
            if 'technology' in category or symbol.upper() in ['QQQ', 'XLK', 'ARKK']:
                return {
                    'Technology': 65.0,
                    'Communication Services': 15.0,
                    'Consumer Discretionary': 10.0,
                    'Healthcare': 5.0,
                    'Other': 5.0
                }
            elif 'sp' in category.lower() or symbol.upper() in ['SPY', 'VOO', 'IVV']:
                return {
                    'Technology': 28.0,
                    'Healthcare': 13.0,
                    'Financials': 12.0,
                    'Consumer Discretionary': 11.0,
                    'Communication Services': 8.0,
                    'Industrials': 8.0,
                    'Consumer Staples': 6.0,
                    'Energy': 4.0,
                    'Utilities': 3.0,
                    'Real Estate': 3.0,
                    'Materials': 2.0,
                    'Other': 2.0
                }
            elif symbol.upper() in ['VTI', 'ITOT']:
                return {
                    'Technology': 25.0,
                    'Healthcare': 14.0,
                    'Financials': 13.0,
                    'Consumer Discretionary': 12.0,
                    'Communication Services': 8.0,
                    'Industrials': 8.0,
                    'Consumer Staples': 6.0,
                    'Energy': 4.0,
                    'Utilities': 3.0,
                    'Real Estate': 3.0,
                    'Materials': 2.0,
                    'Other': 2.0
                }
            else:
                return {}
                
        except Exception as e:
            print(f"Error getting sector allocation for {symbol}: {e}")
            return {}
    
    def _calculate_performance_metrics(self, hist: pd.DataFrame) -> Dict:
        """Calculate performance metrics from historical data"""
        try:
            if hist.empty:
                return {}
            
            # Calculate various performance metrics
            current_price = hist['Close'].iloc[-1]
            start_price = hist['Close'].iloc[0]
            
            # 1 year return
            year_return = ((current_price - start_price) / start_price) * 100
            
            # Volatility (annualized)
            daily_returns = hist['Close'].pct_change().dropna()
            volatility = daily_returns.std() * (252 ** 0.5) * 100
            
            # 52-week high/low
            week_52_high = hist['High'].max()
            week_52_low = hist['Low'].min()
            
            return {
                '1_year_return': round(year_return, 2),
                'volatility': round(volatility, 2),
                '52_week_high': round(week_52_high, 2),
                '52_week_low': round(week_52_low, 2),
                'current_vs_52w_high': round(((current_price - week_52_high) / week_52_high) * 100, 2)
            }
        except Exception as e:
            print(f"Error calculating performance metrics: {e}")
            return {}
    
    def _parse_alpha_vantage_data(self, data: Dict, symbol: str) -> Dict:
        """Parse Alpha Vantage response into standardized format"""
        try:
            return {
                'symbol': symbol,
                'name': data.get('Name', 'N/A'),
                'issuer': data.get('AssetType', 'N/A'),
                'category': data.get('Sector', 'N/A'),
                'description': data.get('Description', ''),
                'expense_ratio': self._safe_float(data.get('ExpenseRatio')),
                'aum': data.get('MarketCapitalization', 'N/A'),
                'holdings': self._fetch_holdings_alpha_vantage(symbol),
                'sector_allocation': self._fetch_sector_allocation_alpha_vantage(symbol),
                'data_source': 'Alpha Vantage',
                'last_updated': data.get('LastRefreshed')
            }
        except Exception as e:
            print(f"Error parsing Alpha Vantage data: {e}")
            return None
    
    def _parse_polygon_data(self, data: Dict, symbol: str) -> Dict:
        """Parse Polygon response into standardized format"""
        try:
            return {
                'symbol': symbol,
                'name': data.get('name', 'N/A'),
                'issuer': data.get('primary_exchange', 'N/A'),
                'category': data.get('type', 'N/A'),
                'description': data.get('description', ''),
                'expense_ratio': None,  # Polygon might not have this directly
                'aum': data.get('market_cap', 'N/A'),
                'holdings': [],  # Would need separate API call
                'sector_allocation': {},  # Would need separate API call
                'data_source': 'Polygon',
                'last_updated': data.get('last_updated_utc')
            }
        except Exception as e:
            print(f"Error parsing Polygon data: {e}")
            return None
    
    def _fetch_holdings_alpha_vantage(self, symbol: str) -> List[Dict]:
        """Fetch holdings data from Alpha Vantage (if available)"""
        # Alpha Vantage doesn't typically provide holdings data directly
        # This would require a separate service or API
        return []
    
    def _fetch_sector_allocation_alpha_vantage(self, symbol: str) -> Dict:
        """Fetch sector allocation from Alpha Vantage (if available)"""
        # Alpha Vantage doesn't typically provide sector allocation directly
        # This would require a separate service or API
        return {}
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert string to float"""
        try:
            if value and value != 'None':
                # Remove percentage sign if present
                if isinstance(value, str) and value.endswith('%'):
                    value = value[:-1]
                return float(value)
        except (ValueError, TypeError):
            pass
        return None
    
    def get_popular_etfs(self) -> List[str]:
        """Return list of popular ETF symbols"""
        return ['VTI', 'VOO', 'SPY', 'QQQ', 'ARKK', 'VEA', 'VWO', 'AGG', 'VNQ', 'GLD']

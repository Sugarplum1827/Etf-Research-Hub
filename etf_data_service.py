import requests
import json
import os
import pandas as pd
from typing import Dict, List, Optional

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
        Fetch ETF data from free sources or return structured empty state
        This method provides proper error handling instead of mock data
        """
        # For demonstration, we'll return a structured response indicating data unavailability
        # In a real implementation, this would connect to free APIs like Yahoo Finance, etc.
        
        known_etfs = {
            'VTI': {
                'name': 'Vanguard Total Stock Market ETF',
                'issuer': 'Vanguard',
                'category': 'Large Cap Equity'
            },
            'VOO': {
                'name': 'Vanguard S&P 500 ETF',
                'issuer': 'Vanguard',
                'category': 'Large Cap Equity'
            },
            'SPY': {
                'name': 'SPDR S&P 500 ETF Trust',
                'issuer': 'State Street',
                'category': 'Large Cap Equity'
            },
            'QQQ': {
                'name': 'Invesco QQQ Trust',
                'issuer': 'Invesco',
                'category': 'Technology'
            },
            'ARKK': {
                'name': 'ARK Innovation ETF',
                'issuer': 'ARK Invest',
                'category': 'Thematic'
            }
        }
        
        if symbol in known_etfs:
            basic_info = known_etfs[symbol]
            return {
                'symbol': symbol,
                'name': basic_info['name'],
                'issuer': basic_info['issuer'],
                'category': basic_info['category'],
                'description': f"Real-time data for {basic_info['name']} is not available. Please configure API keys for live data access.",
                'expense_ratio': None,
                'aum': None,
                'holdings': [],
                'sector_allocation': {},
                'data_source': 'Limited',
                'last_updated': None
            }
        
        return None
    
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

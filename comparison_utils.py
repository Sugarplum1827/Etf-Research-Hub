import pandas as pd
from typing import Dict, List, Tuple, Optional

class ComparisonUtils:
    """Utility class for ETF comparison functionality"""
    
    def __init__(self):
        pass
    
    def find_overlapping_holdings(self, holdings1: List[Dict], holdings2: List[Dict]) -> List[Dict]:
        """
        Find overlapping holdings between two ETFs
        
        Args:
            holdings1: Holdings list for first ETF
            holdings2: Holdings list for second ETF
            
        Returns:
            List of overlapping holdings with comparison data
        """
        if not holdings1 or not holdings2:
            return []
        
        # Convert to DataFrames for easier processing
        df1 = pd.DataFrame(holdings1)
        df2 = pd.DataFrame(holdings2)
        
        # Check if required columns exist
        if 'ticker' not in df1.columns or 'ticker' not in df2.columns:
            return []
        
        # Find overlapping tickers
        overlapping_tickers = set(df1['ticker'].str.upper()) & set(df2['ticker'].str.upper())
        
        if not overlapping_tickers:
            return []
        
        overlaps = []
        for ticker in overlapping_tickers:
            holding1 = df1[df1['ticker'].str.upper() == ticker].iloc[0]
            holding2 = df2[df2['ticker'].str.upper() == ticker].iloc[0]
            
            overlap_data = {
                'ticker': ticker,
                'company_name': holding1.get('company_name', holding2.get('company_name', 'N/A')),
                'sector': holding1.get('sector', holding2.get('sector', 'N/A')),
                'weight_etf1': holding1.get('weight', 0),
                'weight_etf2': holding2.get('weight', 0),
                'weight_difference': abs(holding1.get('weight', 0) - holding2.get('weight', 0))
            }
            overlaps.append(overlap_data)
        
        # Sort by weight difference (largest differences first)
        overlaps.sort(key=lambda x: x['weight_difference'], reverse=True)
        
        return overlaps
    
    def calculate_portfolio_overlap(self, holdings1: List[Dict], holdings2: List[Dict]) -> float:
        """
        Calculate the portfolio overlap percentage between two ETFs
        
        Args:
            holdings1: Holdings list for first ETF
            holdings2: Holdings list for second ETF
            
        Returns:
            Overlap percentage (0-100)
        """
        if not holdings1 or not holdings2:
            return 0.0
        
        df1 = pd.DataFrame(holdings1)
        df2 = pd.DataFrame(holdings2)
        
        if 'ticker' not in df1.columns or 'ticker' not in df2.columns:
            return 0.0
        
        # Get sets of tickers
        tickers1 = set(df1['ticker'].str.upper())
        tickers2 = set(df2['ticker'].str.upper())
        
        # Calculate overlap
        overlapping_tickers = tickers1 & tickers2
        total_unique_tickers = tickers1 | tickers2
        
        if not total_unique_tickers:
            return 0.0
        
        overlap_percentage = (len(overlapping_tickers) / len(total_unique_tickers)) * 100
        return round(overlap_percentage, 2)
    
    def compare_sector_allocations(self, sector1: Dict, sector2: Dict) -> Dict:
        """
        Compare sector allocations between two ETFs
        
        Args:
            sector1: Sector allocation for first ETF
            sector2: Sector allocation for second ETF
            
        Returns:
            Dictionary with comparison metrics
        """
        if not sector1 and not sector2:
            return {}
        
        all_sectors = set(sector1.keys()) | set(sector2.keys())
        
        sector_comparison = {}
        total_difference = 0
        
        for sector in all_sectors:
            weight1 = sector1.get(sector, 0)
            weight2 = sector2.get(sector, 0)
            difference = abs(weight1 - weight2)
            total_difference += difference
            
            sector_comparison[sector] = {
                'etf1_weight': weight1,
                'etf2_weight': weight2,
                'difference': difference,
                'relative_difference': difference / max(weight1, weight2, 1) * 100 if max(weight1, weight2) > 0 else 0
            }
        
        # Calculate overall similarity score (100 - average difference)
        similarity_score = max(0, 100 - (total_difference / len(all_sectors) if all_sectors else 0))
        
        return {
            'sector_comparison': sector_comparison,
            'similarity_score': round(similarity_score, 2),
            'total_sectors': len(all_sectors),
            'common_sectors': len(set(sector1.keys()) & set(sector2.keys()))
        }
    
    def compare_expense_ratios(self, etf1_data: Dict, etf2_data: Dict) -> Dict:
        """
        Compare expense ratios between two ETFs
        
        Args:
            etf1_data: First ETF data
            etf2_data: Second ETF data
            
        Returns:
            Dictionary with expense ratio comparison
        """
        expense1 = etf1_data.get('expense_ratio')
        expense2 = etf2_data.get('expense_ratio')
        
        if expense1 is None or expense2 is None:
            return {
                'etf1_expense_ratio': expense1,
                'etf2_expense_ratio': expense2,
                'difference': None,
                'cheaper_etf': None,
                'savings_basis_points': None
            }
        
        difference = abs(expense1 - expense2)
        cheaper_etf = etf1_data.get('symbol') if expense1 < expense2 else etf2_data.get('symbol')
        savings_basis_points = difference * 100  # Convert to basis points
        
        return {
            'etf1_expense_ratio': expense1,
            'etf2_expense_ratio': expense2,
            'difference': round(difference, 4),
            'cheaper_etf': cheaper_etf,
            'savings_basis_points': round(savings_basis_points, 2)
        }
    
    def compare_aum(self, etf1_data: Dict, etf2_data: Dict) -> Dict:
        """
        Compare Assets Under Management between two ETFs
        
        Args:
            etf1_data: First ETF data
            etf2_data: Second ETF data
            
        Returns:
            Dictionary with AUM comparison
        """
        aum1 = etf1_data.get('aum')
        aum2 = etf2_data.get('aum')
        
        # Try to parse AUM values if they're strings
        aum1_numeric = self._parse_aum(aum1)
        aum2_numeric = self._parse_aum(aum2)
        
        if aum1_numeric is None or aum2_numeric is None:
            return {
                'etf1_aum': aum1,
                'etf2_aum': aum2,
                'larger_etf': None,
                'size_ratio': None
            }
        
        larger_etf = etf1_data.get('symbol') if aum1_numeric > aum2_numeric else etf2_data.get('symbol')
        size_ratio = max(aum1_numeric, aum2_numeric) / min(aum1_numeric, aum2_numeric)
        
        return {
            'etf1_aum': aum1,
            'etf2_aum': aum2,
            'etf1_aum_numeric': aum1_numeric,
            'etf2_aum_numeric': aum2_numeric,
            'larger_etf': larger_etf,
            'size_ratio': round(size_ratio, 2)
        }
    
    def _parse_aum(self, aum_value) -> Optional[float]:
        """
        Parse AUM value from various string formats
        
        Args:
            aum_value: AUM value (could be string with units or number)
            
        Returns:
            Numeric AUM value or None if cannot parse
        """
        if aum_value is None or aum_value == 'N/A':
            return None
        
        if isinstance(aum_value, (int, float)):
            return float(aum_value)
        
        if isinstance(aum_value, str):
            # Remove common currency symbols and spaces
            clean_value = aum_value.replace('$', '').replace(',', '').strip()
            
            # Handle units (B for billions, M for millions, K for thousands)
            multiplier = 1
            if clean_value.upper().endswith('B'):
                multiplier = 1_000_000_000
                clean_value = clean_value[:-1]
            elif clean_value.upper().endswith('M'):
                multiplier = 1_000_000
                clean_value = clean_value[:-1]
            elif clean_value.upper().endswith('K'):
                multiplier = 1_000
                clean_value = clean_value[:-1]
            
            try:
                return float(clean_value) * multiplier
            except ValueError:
                return None
        
        return None
    
    def generate_comparison_summary(self, etf1_data: Dict, etf2_data: Dict) -> Dict:
        """
        Generate a comprehensive comparison summary
        
        Args:
            etf1_data: First ETF data
            etf2_data: Second ETF data
            
        Returns:
            Dictionary with comprehensive comparison summary
        """
        summary = {
            'etf1_symbol': etf1_data.get('symbol', 'N/A'),
            'etf2_symbol': etf2_data.get('symbol', 'N/A'),
            'portfolio_overlap': self.calculate_portfolio_overlap(
                etf1_data.get('holdings', []),
                etf2_data.get('holdings', [])
            ),
            'sector_comparison': self.compare_sector_allocations(
                etf1_data.get('sector_allocation', {}),
                etf2_data.get('sector_allocation', {})
            ),
            'expense_ratio_comparison': self.compare_expense_ratios(etf1_data, etf2_data),
            'aum_comparison': self.compare_aum(etf1_data, etf2_data),
            'overlapping_holdings': self.find_overlapping_holdings(
                etf1_data.get('holdings', []),
                etf2_data.get('holdings', [])
            )
        }
        
        return summary

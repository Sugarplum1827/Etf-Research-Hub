import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List

class ChartUtils:
    """Utility class for creating charts and visualizations"""
    
    def __init__(self):
        # Define color palette for consistent styling
        self.color_palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
    
    def create_sector_pie_chart(self, sector_data: Dict, etf_symbol: str) -> go.Figure:
        """
        Create a pie chart for sector allocation
        
        Args:
            sector_data: Dictionary with sector names as keys and percentages as values
            etf_symbol: ETF symbol for the title
            
        Returns:
            Plotly figure object
        """
        if not sector_data:
            return self._create_empty_chart("No sector allocation data available")
        
        # Prepare data
        sectors = list(sector_data.keys())
        percentages = list(sector_data.values())
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=sectors,
            values=percentages,
            hole=0.3,
            textinfo='label+percent',
            textposition='auto',
            marker=dict(colors=self.color_palette[:len(sectors)])
        )])
        
        fig.update_layout(
            title=f"Sector Allocation - {etf_symbol}",
            title_x=0.5,
            showlegend=True,
            height=500,
            font=dict(size=12)
        )
        
        return fig
    
    def create_sector_bar_chart(self, sector_data: Dict, etf_symbol: str) -> go.Figure:
        """
        Create a bar chart for sector allocation
        
        Args:
            sector_data: Dictionary with sector names as keys and percentages as values
            etf_symbol: ETF symbol for the title
            
        Returns:
            Plotly figure object
        """
        if not sector_data:
            return self._create_empty_chart("No sector allocation data available")
        
        # Prepare data and sort by percentage
        df = pd.DataFrame(list(sector_data.items()), columns=['Sector', 'Percentage'])
        df = df.sort_values('Percentage', ascending=True)
        
        # Create horizontal bar chart
        fig = go.Figure(data=[go.Bar(
            x=df['Percentage'],
            y=df['Sector'],
            orientation='h',
            marker=dict(color=self.color_palette[0]),
            text=[f"{x:.1f}%" for x in df['Percentage']],
            textposition='auto'
        )])
        
        fig.update_layout(
            title=f"Sector Allocation - {etf_symbol}",
            title_x=0.5,
            xaxis_title="Percentage (%)",
            yaxis_title="Sector",
            height=max(400, len(df) * 30 + 100),
            font=dict(size=12),
            margin=dict(l=150)
        )
        
        return fig
    
    def create_sector_comparison_chart(self, sector1: Dict, sector2: Dict, 
                                     etf1_symbol: str, etf2_symbol: str) -> go.Figure:
        """
        Create a side-by-side comparison chart for sector allocations
        
        Args:
            sector1: Sector allocation for first ETF
            sector2: Sector allocation for second ETF
            etf1_symbol: First ETF symbol
            etf2_symbol: Second ETF symbol
            
        Returns:
            Plotly figure object
        """
        if not sector1 and not sector2:
            return self._create_empty_chart("No sector allocation data available for comparison")
        
        # Get all unique sectors
        all_sectors = set(sector1.keys()) | set(sector2.keys())
        
        # Prepare data
        comparison_data = []
        for sector in all_sectors:
            comparison_data.append({
                'Sector': sector,
                etf1_symbol: sector1.get(sector, 0),
                etf2_symbol: sector2.get(sector, 0)
            })
        
        df = pd.DataFrame(comparison_data)
        df = df.sort_values(etf1_symbol, ascending=True)
        
        # Create grouped bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name=etf1_symbol,
            y=df['Sector'],
            x=df[etf1_symbol],
            orientation='h',
            marker=dict(color=self.color_palette[0]),
            text=[f"{x:.1f}%" if x > 0 else "" for x in df[etf1_symbol]],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name=etf2_symbol,
            y=df['Sector'],
            x=df[etf2_symbol],
            orientation='h',
            marker=dict(color=self.color_palette[1]),
            text=[f"{x:.1f}%" if x > 0 else "" for x in df[etf2_symbol]],
            textposition='auto'
        ))
        
        fig.update_layout(
            title=f"Sector Allocation Comparison: {etf1_symbol} vs {etf2_symbol}",
            title_x=0.5,
            xaxis_title="Percentage (%)",
            yaxis_title="Sector",
            barmode='group',
            height=max(500, len(df) * 35 + 150),
            font=dict(size=12),
            margin=dict(l=150),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    def create_holdings_weight_chart(self, holdings: List[Dict], etf_symbol: str, top_n: int = 10) -> go.Figure:
        """
        Create a chart showing top holdings by weight
        
        Args:
            holdings: List of holding dictionaries
            etf_symbol: ETF symbol for the title
            top_n: Number of top holdings to display
            
        Returns:
            Plotly figure object
        """
        if not holdings:
            return self._create_empty_chart("No holdings data available")
        
        # Convert to DataFrame and get top holdings
        df = pd.DataFrame(holdings)
        if 'weight' not in df.columns:
            return self._create_empty_chart("Holdings weight data not available")
        
        df = df.sort_values('weight', ascending=False).head(top_n)
        
        # Create bar chart
        fig = go.Figure(data=[go.Bar(
            x=df['weight'],
            y=df.get('company_name', df.get('ticker', '')),
            orientation='h',
            marker=dict(color=self.color_palette[2]),
            text=[f"{x:.2f}%" for x in df['weight']],
            textposition='auto'
        )])
        
        fig.update_layout(
            title=f"Top {top_n} Holdings by Weight - {etf_symbol}",
            title_x=0.5,
            xaxis_title="Weight (%)",
            yaxis_title="Holdings",
            height=max(400, len(df) * 30 + 100),
            font=dict(size=12),
            margin=dict(l=200)
        )
        
        return fig
    
    def create_expense_ratio_comparison(self, etf_data: List[Dict]) -> go.Figure:
        """
        Create a comparison chart for expense ratios
        
        Args:
            etf_data: List of ETF data dictionaries
            
        Returns:
            Plotly figure object
        """
        if not etf_data:
            return self._create_empty_chart("No data available for comparison")
        
        # Filter ETFs with expense ratio data
        valid_etfs = [etf for etf in etf_data if etf.get('expense_ratio') is not None]
        
        if not valid_etfs:
            return self._create_empty_chart("No expense ratio data available")
        
        symbols = [etf['symbol'] for etf in valid_etfs]
        expense_ratios = [etf['expense_ratio'] for etf in valid_etfs]
        
        fig = go.Figure(data=[go.Bar(
            x=symbols,
            y=expense_ratios,
            marker=dict(color=self.color_palette[3]),
            text=[f"{x:.2f}%" for x in expense_ratios],
            textposition='auto'
        )])
        
        fig.update_layout(
            title="Expense Ratio Comparison",
            title_x=0.5,
            xaxis_title="ETF Symbol",
            yaxis_title="Expense Ratio (%)",
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """
        Create an empty chart with a message
        
        Args:
            message: Message to display
            
        Returns:
            Plotly figure object
        """
        fig = go.Figure()
        
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=message,
            showarrow=False,
            font=dict(size=16),
            xref="paper",
            yref="paper"
        )
        
        fig.update_layout(
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='white'
        )
        
        return fig

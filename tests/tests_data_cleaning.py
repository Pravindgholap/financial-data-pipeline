import pytest
import pandas as pd
import numpy as np
from src.data_cleaning import clean_trade_data

class TestDataCleaning:
    
    def test_remove_negative_prices(self):
        """Test that negative prices are removed"""
        df = pd.DataFrame({
            'ticker': ['AAPL', 'AAPL'],
            'timestamp': ['2024-01-01', '2024-01-02'],
            'open': [150, -10],
            'high': [155, -5],
            'low': [145, -15],
            'close': [152, -10],
            'volume': [1000, 2000]
        })
        
        cleaned = clean_trade_data(df)
        assert len(cleaned) == 1
        assert (cleaned['open'] > 0).all()
    
    def test_remove_unrealistic_prices(self):
        """Test that unrealistic prices (> $10,000) are removed"""
        df = pd.DataFrame({
            'ticker': ['AAPL', 'AAPL'],
            'timestamp': ['2024-01-01', '2024-01-02'],
            'open': [150, 15000],
            'high': [155, 15500],
            'low': [145, 14500],
            'close': [152, 15200],
            'volume': [1000, 2000]
        })
        
        cleaned = clean_trade_data(df)
        assert len(cleaned) == 1
        assert (cleaned['open'] < 10000).all()
    
    def test_handle_missing_values(self):
        """Test that null values are handled"""
        df = pd.DataFrame({
            'ticker': ['AAPL', 'AAPL', 'AAPL'],
            'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'open': [150, np.nan, 152],
            'high': [155, 156, np.nan],
            'low': [145, 146, 147],
            'close': [152, 153, 154],
            'volume': [1000, 2000, 3000]
        })
        
        cleaned = clean_trade_data(df)
        assert cleaned.isnull().sum().sum() == 0
    
    def test_remove_duplicates(self):
        """Test that duplicate records are removed"""
        df = pd.DataFrame({
            'ticker': ['AAPL', 'AAPL', 'AAPL'],
            'timestamp': ['2024-01-01', '2024-01-01', '2024-01-02'],
            'open': [150, 150, 152],
            'high': [155, 155, 156],
            'low': [145, 145, 147],
            'close': [152, 152, 154],
            'volume': [1000, 1000, 2000]
        })
        
        cleaned = clean_trade_data(df)
        assert len(cleaned) == 2
    
    def test_fix_inverted_ohlc(self):
        """Test that inverted OHLC values are fixed"""
        df = pd.DataFrame({
            'ticker': ['AAPL', 'AAPL'],
            'timestamp': ['2024-01-01', '2024-01-02'],
            'open': [150, 155],
            'high': [145, 160],  # High should be >= Low
            'low': [155, 150],
            'close': [152, 153],
            'volume': [1000, 2000]
        })
        
        cleaned = clean_trade_data(df)
        # After cleaning, high should be >= low
        assert (cleaned['high'] >= cleaned['low']).all()
    
    def test_round_prices(self):
        """Test that prices are rounded to 2 decimals"""
        df = pd.DataFrame({
            'ticker': ['AAPL'],
            'timestamp': ['2024-01-01'],
            'open': [150.1234],
            'high': [155.5678],
            'low': [145.9012],
            'close': [152.3456],
            'volume': [1000]
        })
        
        cleaned = clean_trade_data(df)
        for col in ['open', 'high', 'low', 'close']:
            assert cleaned[col].iloc[0] == round(cleaned[col].iloc[0], 2)

if __name__ == "__main__":
    pytest.main([__file__, '-v'])
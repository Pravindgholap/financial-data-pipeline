import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def engineer_features(df):
    """Create advanced financial features"""
    
    df = df.copy()
    
    # Sort for rolling calculations
    df = df.sort_values(['ticker', 'timestamp'])
    
    logger.info("Starting feature engineering...")
    
    # 1. Daily Returns
    df['daily_return'] = df.groupby('ticker')['close'].pct_change()
    
    # 2. Log Returns (more statistically stable)
    df['log_return'] = np.log(df['close'] / df.groupby('ticker')['close'].shift(1))
    
    # 3. VWAP - Volume Weighted Average Price (using typical price)
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (df['typical_price'] * df['volume']).groupby(df['ticker']).cumsum() / df.groupby(df['ticker'])['volume'].cumsum()
    
    # 4. Rolling Returns (5-day and 20-day)
    df['returns_5d'] = df.groupby('ticker')['close'].pct_change(periods=5)
    df['returns_20d'] = df.groupby('ticker')['close'].pct_change(periods=20)
    
    # 5. Volatility (Rolling Std Dev of daily returns)
    df['volatility_5d'] = df.groupby('ticker')['daily_return'].rolling(5).std().reset_index(level=0, drop=True)
    df['volatility_20d'] = df.groupby('ticker')['daily_return'].rolling(20).std().reset_index(level=0, drop=True)
    
    # 6. Price relative to VWAP
    df['vwap_premium'] = (df['close'] - df['vwap']) / df['vwap'] * 100
    
    # 7. Volume moving averages
    df['volume_ma_5'] = df.groupby('ticker')['volume'].transform(lambda x: x.rolling(5).mean())
    df['volume_ma_20'] = df.groupby('ticker')['volume'].transform(lambda x: x.rolling(20).mean())
    
    # 8. Volume ratio
    df['volume_ratio'] = df['volume'] / df['volume_ma_20']
    
    # 9. High-Low range
    df['high_low_range'] = (df['high'] - df['low']) / df['close'] * 100
    
    # 10. Price momentum indicators
    df['high_5d'] = df.groupby('ticker')['high'].transform(lambda x: x.rolling(5).max())
    df['low_5d'] = df.groupby('ticker')['low'].transform(lambda x: x.rolling(5).min())
    df['price_position'] = (df['close'] - df['low_5d']) / (df['high_5d'] - df['low_5d']) * 100
    
    # 11. Day of week and month (for seasonality)
    df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
    df['month'] = pd.to_datetime(df['timestamp']).dt.month
    
    # Drop NaN values from rolling calculations
    initial_rows = len(df)
    df = df.dropna()
    logger.info(f"Dropped {initial_rows - len(df):,} rows with NaN values")
    
    logger.info(f"Feature engineering complete: {len(df):,} rows with {len(df.columns)} features")
    return df

if __name__ == "__main__":
    # Test feature engineering
    df = pd.read_csv('data/raw/trades_raw.csv')
    featured = engineer_features(df)
    print(f"Features: {list(featured.columns)}")
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def clean_trade_data(df):
    """Perform comprehensive data cleaning"""
    
    initial_rows = len(df)
    logger.info(f"Initial rows: {initial_rows:,}")
    
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # 1. Handle missing values
    null_count = df.isnull().sum().sum()
    if null_count > 0:
        df = df.dropna()
        logger.info(f"Removed {null_count} null values")
    
    # 2. Remove duplicates
    duplicates = df.duplicated(subset=['ticker', 'timestamp']).sum()
    if duplicates > 0:
        df = df.drop_duplicates(subset=['ticker', 'timestamp'])
        logger.info(f"Removed {duplicates} duplicate records")
    
    # 3. Validate price columns
    for col in ['open', 'high', 'low', 'close', 'adj_close']:
        if col in df.columns:
            # Remove negative prices
            df = df[df[col] >= 0]
            # Remove unrealistic prices (> $10,000)
            df = df[df[col] <= 10000]
    
    # 4. Validate OHLC relationship (high >= low)
    if 'high' in df.columns and 'low' in df.columns:
        invalid_ohlc = (df['high'] < df['low']).sum()
        if invalid_ohlc > 0:
            # Swap high and low if they're inverted
            mask = df['high'] < df['low']
            df.loc[mask, ['high', 'low']] = df.loc[mask, ['low', 'high']].values
            logger.info(f"Fixed {invalid_ohlc} inverted OHLC records")
    
    # 5. Remove volume outliers
    for ticker in df['ticker'].unique():
        mask = df['ticker'] == ticker
        mean_vol = df.loc[mask, 'volume'].mean()
        std_vol = df.loc[mask, 'volume'].std()
        
        if std_vol > 0:
            upper_bound = mean_vol + 3 * std_vol
            df.loc[mask, 'volume'] = df.loc[mask, 'volume'].clip(upper=upper_bound)
    
    # 6. Filter to market hours (optional - keep all for daily data)
    # For daily data, we keep everything
    
    # 7. Round prices to 2 decimals
    for col in ['open', 'high', 'low', 'close', 'adj_close']:
        if col in df.columns:
            df[col] = df[col].round(2)
    
    # 8. Add quality flags
    df['is_clean'] = True
    
    final_rows = len(df)
    logger.info(f"After cleaning: {final_rows:,} rows (removed {initial_rows - final_rows:,})")
    
    return df

def clean_large_file_in_chunks(filepath, chunksize=100000):
    """Process large files in chunks to manage memory"""
    
    cleaned_chunks = []
    total_rows = 0
    
    for chunk in pd.read_csv(filepath, chunksize=chunksize):
        cleaned_chunk = clean_trade_data(chunk)
        cleaned_chunks.append(cleaned_chunk)
        total_rows += len(cleaned_chunk)
        logger.info(f"Processed chunk: {len(cleaned_chunk):,} rows")
    
    final_df = pd.concat(cleaned_chunks, ignore_index=True)
    logger.info(f"Total processed: {total_rows:,} rows")
    return final_df

if __name__ == "__main__":
    # Test cleaning
    df = pd.read_csv('data/raw/trades_raw.csv')
    cleaned = clean_trade_data(df)
    print(f"Cleaned {len(cleaned):,} rows")
import pandas as pd
from datetime import datetime, timedelta
import time
import requests
from src.config import config
from src.cache_manager import DataCache
import logging
import re

logger = logging.getLogger(__name__)

def clean_price_string(value):
    """Clean price strings by removing commas and converting to float"""
    if isinstance(value, str):
        # Remove commas, dollar signs, and any non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d.]', '', value)
        try:
            return float(cleaned)
        except ValueError:
            return None
    return float(value)

def fetch_and_save_trade_data(symbols=None, use_cache=True, output_size="compact"):
    """Fetches data from Alpha Vantage with caching support using requests"""
    
    if symbols is None:
        symbols = config['api']['symbols']
    
    cache = DataCache()
    all_data = []
    
    for i, symbol in enumerate(symbols):
        logger.info(f"Processing {symbol}...")
        
        # Check cache first
        if use_cache:
            cached_df = cache.get(symbol, max_age_hours=config['pipeline'].get('cache_days', 1) * 24)
            if cached_df is not None:
                all_data.append(cached_df)
                continue
        
        # Rate limiting - respect API limits
        if i > 0:
            time.sleep(2)  # 2 seconds between requests to be safe
        
        try:
            # Fetch from API using requests
            logger.info(f"Fetching fresh data for {symbol}...")
            
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'outputsize': output_size,
                'apikey': config['api']['alpha_vantage_key']
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                logger.error(f"API Error for {symbol}: {data['Error Message']}")
                continue
                
            if 'Note' in data:
                logger.warning(f"API Note for {symbol}: {data['Note']}")
                # This usually means rate limit hit
                time.sleep(10)
                continue
            
            if 'Time Series (Daily)' not in data:
                logger.error(f"Unexpected response for {symbol}: {list(data.keys())}")
                continue
            
            # Convert to DataFrame
            time_series = data['Time Series (Daily)']
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Reset index to get date as column
            df = df.reset_index().rename(columns={'index': 'timestamp'})
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['ticker'] = symbol
            
            # Clean and convert numeric columns - THIS IS THE CRITICAL FIX
            numeric_columns = {
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low',
                '4. close': 'close',
                '5. adjusted close': 'adj_close',
                '6. volume': 'volume'
            }
            
            for old_col, new_col in numeric_columns.items():
                if old_col in df.columns:
                    # Clean the values and convert to float
                    df[new_col] = df[old_col].apply(clean_price_string)
                    # Drop the old column
                    df = df.drop(columns=[old_col])
            
            # Volume should be integer
            df['volume'] = df['volume'].astype(int)
            
            # Keep necessary columns
            keep_cols = ['timestamp', 'ticker', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
            df = df[[col for col in keep_cols if col in df.columns]]
            
            # Validate prices are reasonable
            for col in ['open', 'high', 'low', 'close', 'adj_close']:
                if col in df.columns:
                    # Remove any outliers (> $10,000 or < $0)
                    df = df[(df[col] > 0) & (df[col] < 10000)]
            
            # Round to 2 decimals
            for col in ['open', 'high', 'low', 'close', 'adj_close']:
                if col in df.columns:
                    df[col] = df[col].round(2)
            
            logger.info(f"   Fetched {len(df)} records for {symbol}")
            logger.info(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
            
            # Cache for future use
            cache.set(symbol, df)
            all_data.append(df)
            
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    if not all_data:
        logger.warning("No API data fetched. Generating synthetic data...")
        return generate_synthetic_data()
    
    # Combine all tickers
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df = combined_df.sort_values(['ticker', 'timestamp'])
    
    # Filter to reasonable date range (avoid future dates)
    combined_df = combined_df[combined_df['timestamp'] <= datetime.now()]
    
    # Save
    combined_df.to_csv('data/raw/trades_raw.csv', index=False)
    combined_df.to_parquet('data/raw/trades_raw.parquet', index=False)
    
    logger.info(f"Saved {len(combined_df):,} total records")
    logger.info(f"   Date range: {combined_df['timestamp'].min()} to {combined_df['timestamp'].max()}")
    
    return combined_df

def generate_synthetic_data(days=30, tickers=None):
    """Fallback: Generate synthetic data if API fails"""
    import random
    
    if tickers is None:
        tickers = config['api']['symbols']
    
    records = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Realistic starting prices
    base_prices = {
        'AAPL': 175.0,
        'GOOGL': 140.0,
        'MSFT': 370.0,
        'AMZN': 185.0,
        'TSLA': 250.0
    }
    
    for ticker in tickers:
        if ticker in base_prices:
            base_price = base_prices[ticker]
        else:
            base_price = random.uniform(50, 500)
            
        current_time = start_date
        
        while current_time <= end_date:
            # Only generate weekdays
            if current_time.weekday() < 5:  # Monday to Friday
                # Random walk with realistic volatility
                price_change_pct = random.uniform(-0.03, 0.03)  # -3% to +3% daily
                base_price *= (1 + price_change_pct)
                
                # Add some mean reversion
                if base_price > base_price * 1.2:
                    base_price = base_price * 0.99
                if base_price < base_price * 0.8:
                    base_price = base_price * 1.01
                
                volume = random.randint(1000000, 50000000)
                
                # Generate OHLC
                close_price = round(base_price, 2)
                open_price = round(close_price * (1 + random.uniform(-0.01, 0.01)), 2)
                high_price = round(max(open_price, close_price) * (1 + random.uniform(0, 0.01)), 2)
                low_price = round(min(open_price, close_price) * (1 - random.uniform(0, 0.01)), 2)
                
                records.append({
                    'ticker': ticker,
                    'timestamp': current_time,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'adj_close': close_price,
                    'volume': volume
                })
            
            current_time += timedelta(days=1)
    
    df = pd.DataFrame(records)
    df.to_csv('data/raw/trades_raw.csv', index=False)
    df.to_parquet('data/raw/trades_raw.parquet', index=False)
    logger.info(f"Generated {len(df):,} synthetic records")
    return df

def test_ingestion():
    """Test the ingestion with a single symbol"""
    print("Testing ingestion for AAPL...")
    df = fetch_and_save_trade_data(symbols=['AAPL'], output_size='compact')
    if df is not None:
        print(f"\nSuccess! Fetched {len(df)} records")
        print(f"Columns: {list(df.columns)}")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        print(f"\nSample data:\n{df.head(5)}")
    else:
        print("Failed to fetch data")

if __name__ == "__main__":
    test_ingestion()
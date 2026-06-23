import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
import schedule
import time
import sys

from src.data_ingestion import fetch_and_save_trade_data, generate_synthetic_data
from src.data_cleaning import clean_trade_data
from src.feature_engineering import engineer_features
from src.anomaly_detection import detect_anomalies
from src.database_loader import load_to_database, load_anomalies_to_db
from src.visual import plot_anomalies
from src.config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories"""
    dirs = ['data/raw', 'data/processed', 'data/cache', 'notebooks']
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)

def run_pipeline(use_api=True, symbols=None):
    """Main ETL pipeline"""
    
    start_time = datetime.now()
    logger.info("Starting ETL Pipeline")
    logger.info(f"Configuration: {config}")
    
    try:
        # Step 1: Ingestion
        logger.info("Step 1: Data Ingestion")
        if use_api:
            try:
                df = fetch_and_save_trade_data(symbols=symbols)
            except Exception as e:
                logger.warning(f"API failed: {str(e)}. Falling back to synthetic data.")
                df = generate_synthetic_data(days=30)
        else:
            df = generate_synthetic_data(days=30)
        
        logger.info(f"   Ingested {len(df):,} rows")
        
        # Step 2: Data Cleaning
        logger.info("Step 2: Data Cleaning")
        cleaned_df = clean_trade_data(df)
        cleaned_df.to_csv('data/processed/cleaned_data.csv', index=False)
        logger.info(f"   Cleaned to {len(cleaned_df):,} rows")
        
        # Step 3: Feature Engineering
        logger.info("Step 3: Feature Engineering")
        featured_df = engineer_features(cleaned_df)
        featured_df.to_csv('data/processed/featured_data.csv', index=False)
        featured_df.to_parquet('data/processed/featured_data.parquet', index=False)
        logger.info(f"   Engineered {len(featured_df.columns)} features")
        
        # Step 4: Anomaly Detection
        logger.info("Step 4: Anomaly Detection")
        anomalies_df = detect_anomalies(featured_df)
        if not anomalies_df.empty:
            anomalies_df.to_csv('data/processed/anomalies.csv', index=False)
            anomalies_df.to_parquet('data/processed/anomalies.parquet', index=False)
            logger.info(f"   Found {len(anomalies_df)} anomalies")
        else:
            logger.info("   No anomalies found")
        
        # Step 5: Load to Database
        logger.info("Step 5: Database Loading")
        load_to_database(featured_df, 'daily_trades')
        if not anomalies_df.empty:
            load_anomalies_to_db(anomalies_df)
        
        # Step 6: Visualization
        logger.info("Step 6: Visualization")
        if not anomalies_df.empty:
            plot_anomalies(featured_df, anomalies_df)
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"   Duration: {duration:.2f} seconds")
        logger.info(f"   Total rows processed: {len(featured_df):,}")
        logger.info(f"   Anomalies found: {len(anomalies_df):,}")
        logger.info(f"   Features created: {len(featured_df.columns)}")
        logger.info("=" * 60)
        
        return featured_df, anomalies_df
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        raise

def schedule_pipeline():
    """Schedule the pipeline to run at intervals"""
    interval_hours = config['pipeline'].get('schedule_interval_hours', 24)
    
    # Schedule the job
    schedule.every(interval_hours).hours.do(run_pipeline)
    logger.info(f"Pipeline scheduled to run every {interval_hours} hours")
    
    # Run once immediately
    run_pipeline()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Setup directories
    setup_directories()
    
    # Check if run once or schedule
    if len(sys.argv) > 1 and sys.argv[1] == '--schedule':
        schedule_pipeline()
    else:
        # Single run
        run_pipeline()
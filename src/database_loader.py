import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from src.config import config
import logging

logger = logging.getLogger(__name__)

def load_to_database(df, table_name, connection_string=None, if_exists='replace'):
    """Load DataFrame to SQL database"""
    
    if connection_string is None:
        connection_string = config['database'].get('connection_string')
    
    if not connection_string:
        logger.warning("No database connection string provided. Saving to CSV instead.")
        df.to_csv(f'data/processed/{table_name}.csv', index=False)
        logger.info(f"Saved to data/processed/{table_name}.csv")
        return
    
    try:
        engine = create_engine(connection_string)
        
        # Convert timestamps for SQL compatibility
        df_copy = df.copy()
        if 'timestamp' in df_copy.columns:
            df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"Loading {len(df_copy):,} rows to {table_name}...")
        
        df_copy.to_sql(
            table_name,
            engine,
            if_exists=if_exists,
            index=False,
            method='multi',  # Faster bulk insert
            chunksize=10000
        )
        
        logger.info(f"Successfully loaded to {table_name}")
        
        # Verify
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.fetchone()[0]
            logger.info(f"Verification: {count:,} rows in database")
            
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        # Fallback to CSV
        df.to_csv(f'data/processed/{table_name}.csv', index=False)
        logger.info(f"Fallback: Saved to data/processed/{table_name}.csv")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        df.to_csv(f'data/processed/{table_name}.csv', index=False)
        logger.info(f"Fallback: Saved to data/processed/{table_name}.csv")

def load_anomalies_to_db(anomalies_df):
    """Specifically load anomaly alerts"""
    load_to_database(anomalies_df, 'anomaly_alerts', if_exists='append')
    
    if not anomalies_df.empty:
        logger.info(f"Anomaly Alert Summary:")
        logger.info(f"   Total: {len(anomalies_df)}")
        logger.info(f"   HIGH Priority: {len(anomalies_df[anomalies_df['priority'] == 'HIGH'])}")
        logger.info(f"   MEDIUM Priority: {len(anomalies_df[anomalies_df['priority'] == 'MEDIUM'])}")
        logger.info(f"   LOW Priority: {len(anomalies_df[anomalies_df['priority'] == 'LOW'])}")

if __name__ == "__main__":
    # Test database loading
    df = pd.read_csv('data/processed/featured_data.csv')
    load_to_database(df, 'test_table')
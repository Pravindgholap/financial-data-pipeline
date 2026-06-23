import time
import pandas as pd
import numpy as np
from src.data_cleaning import clean_trade_data
from src.feature_engineering import engineer_features
from src.anomaly_detection import detect_anomalies
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def benchmark_performance():
    """Benchmark the pipeline performance"""
    
    logger.info("📊 Starting Performance Benchmark")
    
    # Load data
    try:
        df = pd.read_csv('data/raw/trades_raw.csv')
        logger.info(f"Loaded {len(df):,} rows")
    except FileNotFoundError:
        logger.error("No data found. Run the pipeline first.")
        return
    
    results = {}
    
    # Benchmark 1: Data Cleaning
    logger.info("Benchmarking Data Cleaning...")
    start = time.time()
    cleaned = clean_trade_data(df)
    clean_time = time.time() - start
    results['clean_time'] = clean_time
    results['clean_rows_per_sec'] = len(df) / clean_time
    logger.info(f"   Cleaning: {clean_time:.2f}s ({results['clean_rows_per_sec']:,.0f} rows/sec)")
    
    # Benchmark 2: Feature Engineering
    logger.info("Benchmarking Feature Engineering...")
    start = time.time()
    featured = engineer_features(cleaned)
    feature_time = time.time() - start
    results['feature_time'] = feature_time
    results['feature_rows_per_sec'] = len(cleaned) / feature_time
    logger.info(f"   Feature Engineering: {feature_time:.2f}s ({results['feature_rows_per_sec']:,.0f} rows/sec)")
    
    # Benchmark 3: Anomaly Detection
    logger.info("Benchmarking Anomaly Detection...")
    start = time.time()
    anomalies = detect_anomalies(featured)
    anomaly_time = time.time() - start
    results['anomaly_time'] = anomaly_time
    results['anomaly_rows_per_sec'] = len(featured) / anomaly_time
    logger.info(f"   Anomaly Detection: {anomaly_time:.2f}s ({results['anomaly_rows_per_sec']:,.0f} rows/sec)")
    
    # Memory usage
    memory_usage = df.memory_usage(deep=True).sum() / 1024**2
    results['memory_mb'] = memory_usage
    logger.info(f"   Memory Usage: {memory_usage:.2f} MB")
    
    # Data statistics
    results['total_rows'] = len(df)
    results['anomalies_found'] = len(anomalies)
    results['features_count'] = len(featured.columns)
    
    # Save results
    results_df = pd.DataFrame([results])
    results_df.to_csv('benchmark_results.csv', index=False)
    
    # Save to markdown for README
    with open('benchmark_results.md', 'w') as f:
        f.write("# Performance Benchmark Results\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total Rows | {results['total_rows']:,} |\n")
        f.write(f"| Memory Usage | {results['memory_mb']:.2f} MB |\n")
        f.write(f"| Cleaning Speed | {results['clean_rows_per_sec']:,.0f} rows/sec |\n")
        f.write(f"| Feature Engineering Speed | {results['feature_rows_per_sec']:,.0f} rows/sec |\n")
        f.write(f"| Anomaly Detection Speed | {results['anomaly_rows_per_sec']:,.0f} rows/sec |\n")
        f.write(f"| Features Created | {results['features_count']} |\n")
        f.write(f"| Anomalies Found | {results['anomalies_found']:,} |\n")
    
    logger.info("✅ Benchmark complete. Results saved to benchmark_results.csv")
    return results

if __name__ == "__main__":
    benchmark_performance()
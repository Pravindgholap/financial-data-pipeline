import pandas as pd
import numpy as np
from src.config import config
import logging

logger = logging.getLogger(__name__)

def detect_anomalies(df):
    """Multi-strategy anomaly detection"""
    
    df = df.copy()
    anomalies = pd.DataFrame()
    
    # Get thresholds from config
    price_threshold = config['anomaly_detection']['price_zscore_threshold']
    volume_threshold = config['anomaly_detection']['volume_ratio_threshold']
    vwap_threshold = config['anomaly_detection']['vwap_divergence_threshold']
    
    logger.info("Starting anomaly detection...")
    
    for ticker in df['ticker'].unique():
        ticker_data = df[df['ticker'] == ticker].copy()
        ticker_anomalies = pd.DataFrame()
        
        # Strategy 1: Price Z-Score (for daily data, use 20-day rolling window)
        ticker_data['price_ma_20'] = ticker_data['close'].rolling(20).mean()
        ticker_data['price_std_20'] = ticker_data['close'].rolling(20).std()
        ticker_data['z_score'] = (ticker_data['close'] - ticker_data['price_ma_20']) / ticker_data['price_std_20']
        
        price_spikes = ticker_data[
            (abs(ticker_data['z_score']) > price_threshold) & 
            (ticker_data['price_std_20'].notna())
        ].copy()
        
        if not price_spikes.empty:
            price_spikes['anomaly_type'] = 'Price Spike'
            price_spikes['severity'] = abs(price_spikes['z_score'])
            ticker_anomalies = pd.concat([ticker_anomalies, price_spikes])
        
        # Strategy 2: Volume Shock
        ticker_data['volume_ma_20'] = ticker_data['volume'].rolling(20).mean()
        ticker_data['volume_ratio'] = ticker_data['volume'] / ticker_data['volume_ma_20']
        
        volume_shocks = ticker_data[
            (ticker_data['volume_ratio'] > volume_threshold) & 
            (ticker_data['volume_ma_20'].notna())
        ].copy()
        
        if not volume_shocks.empty:
            volume_shocks['anomaly_type'] = 'Volume Shock'
            volume_shocks['severity'] = volume_shocks['volume_ratio']
            ticker_anomalies = pd.concat([ticker_anomalies, volume_shocks])
        
        # Strategy 3: VWAP Divergence
        vwap_divergence = ticker_data[
            (abs(ticker_data['vwap_premium']) > vwap_threshold) & 
            (ticker_data['vwap'].notna())
        ].copy()
        
        if not vwap_divergence.empty:
            vwap_divergence['anomaly_type'] = 'VWAP Divergence'
            vwap_divergence['severity'] = abs(vwap_divergence['vwap_premium'])
            ticker_anomalies = pd.concat([ticker_anomalies, vwap_divergence])
        
        # Combine anomalies for this ticker
        if not ticker_anomalies.empty:
            # Remove duplicates (if same day triggers multiple alerts)
            ticker_anomalies = ticker_anomalies.drop_duplicates(subset=['timestamp'])
            anomalies = pd.concat([anomalies, ticker_anomalies])
    
    if not anomalies.empty:
        # Add priority levels
        anomalies['priority'] = anomalies['anomaly_type'].map({
            'Price Spike': 'HIGH',
            'Volume Shock': 'MEDIUM',
            'VWAP Divergence': 'LOW'
        })
        
        # Sort by severity
        anomalies = anomalies.sort_values('severity', ascending=False)
        
        logger.info(f"Detected {len(anomalies):,} anomalies")
        
        # Log anomaly summary
        summary = anomalies['anomaly_type'].value_counts()
        for anomaly_type, count in summary.items():
            logger.info(f"   - {anomaly_type}: {count}")
    else:
        logger.info("No anomalies detected")
    
    return anomalies

if __name__ == "__main__":
    # Test anomaly detection
    df = pd.read_csv('data/processed/featured_data.csv')  # You'd need to save this first
    anomalies = detect_anomalies(df)
    print(f"Found {len(anomalies)} anomalies")
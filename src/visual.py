import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import matplotlib.dates as mdates

logger = logging.getLogger(__name__)

# Set style for professional look
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def plot_anomalies(df, anomalies_df, save_path='anomaly_dashboard.png'):
    """Create comprehensive visualization dashboard with proper date handling"""
    
    # Make copies to avoid modifying original data
    df = df.copy()
    anomalies_df = anomalies_df.copy()
    
    # Ensure timestamps are proper datetime objects
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    if not anomalies_df.empty and 'timestamp' in anomalies_df.columns:
        anomalies_df['timestamp'] = pd.to_datetime(anomalies_df['timestamp'])
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Financial Data Anomaly Detection Dashboard', fontsize=16, fontweight='bold')
    
    # 1. Price Trends with Anomalies Highlighted
    ax1 = axes[0, 0]
    if not df.empty:
        # Get the top 3 tickers by data volume
        tickers = df['ticker'].value_counts().head(3).index.tolist()
        
        for ticker in tickers:
            ticker_data = df[df['ticker'] == ticker].sort_values('timestamp')
            
            # Plot the price line
            ax1.plot(ticker_data['timestamp'], ticker_data['close'], 
                    label=ticker, alpha=0.7, linewidth=2)
            
            # Mark anomalies for this ticker
            ticker_anomalies = anomalies_df[anomalies_df['ticker'] == ticker]
            if not ticker_anomalies.empty:
                ax1.scatter(ticker_anomalies['timestamp'], ticker_anomalies['close'], 
                           color='red', s=80, zorder=5, label=f'{ticker} Anomaly')
    
    ax1.set_title('Price Trends with Anomalies', fontsize=12)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price ($)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # CRITICAL FIX: Format dates properly
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # Show every 3 months
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Anomaly Distribution
    ax2 = axes[0, 1]
    if not anomalies_df.empty:
        anomaly_counts = anomalies_df['anomaly_type'].value_counts()
        colors = ['#ff6b6b', '#feca57', '#48dbfb']
        wedges, texts, autotexts = ax2.pie(
            anomaly_counts.values, 
            labels=anomaly_counts.index, 
            autopct='%1.1f%%',
            colors=colors[:len(anomaly_counts)],
            startangle=90,
            textprops={'fontsize': 10}
        )
        ax2.set_title('Anomaly Type Distribution', fontsize=12)
    else:
        ax2.text(0.5, 0.5, 'No Anomalies Detected', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax2.transAxes, fontsize=14)
        ax2.set_title('Anomaly Type Distribution', fontsize=12)
    
    # 3. VWAP Premium Distribution
    ax3 = axes[1, 0]
    if not df.empty and 'vwap_premium' in df.columns:
        vwap_data = df['vwap_premium'].dropna()
        if len(vwap_data) > 0:
            sns.histplot(vwap_data, bins=50, kde=True, ax=ax3, color='#2ecc71')
            ax3.axvline(x=2, color='red', linestyle='--', linewidth=2, label='Upper Threshold (+2%)')
            ax3.axvline(x=-2, color='red', linestyle='--', linewidth=2, label='Lower Threshold (-2%)')
            ax3.set_title('VWAP Premium Distribution', fontsize=12)
            ax3.set_xlabel('Premium/Discount to VWAP (%)')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        else:
            ax3.text(0.5, 0.5, 'No VWAP data available', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax3.transAxes, fontsize=14)
            ax3.set_title('VWAP Premium Distribution', fontsize=12)
    else:
        ax3.text(0.5, 0.5, 'No VWAP data available', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax3.transAxes, fontsize=14)
        ax3.set_title('VWAP Premium Distribution', fontsize=12)
    
    # 4. Volume vs Volatility Scatter
    ax4 = axes[1, 1]
    if not df.empty and 'volume_ma_20' in df.columns and 'volatility_20d' in df.columns:
        # Filter out NaN values
        sample_df = df.dropna(subset=['volume_ma_20', 'volatility_20d', 'vwap_premium'])
        
        if len(sample_df) > 0:
            # Sample for performance if too many points
            if len(sample_df) > 1000:
                sample_df = sample_df.sample(1000, random_state=42)
            
            scatter = ax4.scatter(
                sample_df['volume_ma_20'], 
                sample_df['volatility_20d'],
                c=sample_df['vwap_premium'],
                cmap='RdBu_r',
                alpha=0.6,
                s=30
            )
            ax4.set_xlabel('Average Volume (20-day MA)')
            ax4.set_ylabel('Volatility (20-day Std Dev)')
            ax4.set_title('Volume vs Volatility (Colored by VWAP Premium)', fontsize=12)
            plt.colorbar(scatter, ax=ax4, label='VWAP Premium %')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'Insufficient data for visualization', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax4.transAxes, fontsize=14)
            ax4.set_title('Volume vs Volatility', fontsize=12)
    else:
        ax4.text(0.5, 0.5, 'Insufficient data for visualization', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax4.transAxes, fontsize=14)
        ax4.set_title('Volume vs Volatility', fontsize=12)
    
    plt.tight_layout()
    
    # Save with high DPI
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    logger.info(f"📊 Dashboard saved to {save_path}")
    plt.show()
    
    return fig

def plot_performance_metrics(df):
    """Plot performance metrics for the pipeline"""
    
    df = df.copy()
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Returns distribution
    ax1 = axes[0]
    if 'daily_return' in df.columns:
        returns = df['daily_return'].dropna()
        if len(returns) > 0:
            sns.histplot(returns * 100, bins=50, kde=True, ax=ax1, color='#3498db')
            ax1.axvline(0, color='red', linestyle='--', linewidth=2)
            ax1.set_title('Daily Returns Distribution', fontsize=12)
            ax1.set_xlabel('Daily Return (%)')
            ax1.set_ylabel('Frequency')
            ax1.text(0.02, 0.9, f'Mean: {returns.mean()*100:.4f}%', transform=ax1.transAxes)
            ax1.text(0.02, 0.85, f'Std: {returns.std()*100:.4f}%', transform=ax1.transAxes)
    
    # Volatility by ticker
    ax2 = axes[1]
    if 'volatility_20d' in df.columns:
        volatility_by_ticker = df.groupby('ticker')['volatility_20d'].mean().sort_values()
        if len(volatility_by_ticker) > 0:
            bars = ax2.barh(volatility_by_ticker.index, volatility_by_ticker.values, color='#e74c3c')
            ax2.set_title('Average Volatility by Ticker (20-day)', fontsize=12)
            ax2.set_xlabel('Volatility (Std Dev of Returns)')
            
            # Add value labels
            for i, v in enumerate(volatility_by_ticker.values):
                if not np.isnan(v):
                    ax2.text(v + 0.001, i, f'{v:.4f}', va='center')
    
    plt.tight_layout()
    plt.savefig('performance_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_quick_plot(df, column='close', title='Price Chart'):
    """Quick function to plot a single column"""
    df = df.copy()
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for ticker in df['ticker'].unique():
        ticker_data = df[df['ticker'] == ticker].sort_values('timestamp')
        ax.plot(ticker_data['timestamp'], ticker_data[column], label=ticker, linewidth=2)
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel(column.replace('_', ' ').title())
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Format dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()
    return fig

if __name__ == "__main__":
    # Test visualization
    df = pd.read_csv('data/processed/featured_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create quick plot
    create_quick_plot(df, 'close', 'Stock Prices Over Time')
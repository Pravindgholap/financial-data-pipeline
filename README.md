markdown
# Financial Data Pipeline

A production-ready ETL pipeline for processing financial market data with anomaly detection using real data from Alpha Vantage API.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Pandas](https://img.shields.io/badge/pandas-2.0+-blue.svg)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Architecture
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Alpha │ │ Data │ │ Feature │ │ Anomaly │
│ Vantage │────▶│ Cleaning │────▶│ Engineering │────▶│ Detection │
│ API │ │ │ │ │ │ │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
│
▼
┌─────────────┐
│ SQL/CSV │
│ Storage │
└─────────────┘

text

## Features

- **Real Data Integration**: Fetches live/historical data from Alpha Vantage API with intelligent caching
- **Financial Calculations**: VWAP, rolling returns, volatility, price momentum indicators
- **Multi-Strategy Anomaly Detection**: Price spikes, volume shocks, VWAP divergence
- **Performance Optimized**: Vectorized Pandas operations, chunked processing, memory efficient
- **Production Ready**: Comprehensive logging, error handling, retry logic, unit tests
- **Visualization**: Automatic dashboard generation for anomaly reporting
- **Configurable**: YAML-based configuration with environment variable overrides

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Alpha Vantage API key (free at [alphavantage.co](https://www.alphavantage.co/support/#api-key))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/financial-data-pipeline
cd financial-data-pipeline

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env with your Alpha Vantage API key

# Run the pipeline
python main.py
Performance
Metric	Value
Processing Speed	~2,500 rows/sec
Memory Usage	~50 MB for 5,000 rows
Features Created	25+ financial indicators
Anomaly Detection	3 strategies with severity scoring
Testing
bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src -v
Sample Output
The pipeline generates:

Processed Data: Cleaned data with engineered features (data/processed/featured_data.csv)

Anomaly Alerts: Detected anomalies with priority levels (data/processed/anomalies.csv)

Visual Dashboard: Automatic chart generation (anomaly_dashboard.png)

Performance Logs: Detailed pipeline logs (pipeline.log)

Tech Stack
Core: Python 3.9+, Pandas, NumPy

Data Source: Alpha Vantage API

Storage: CSV, Parquet, PostgreSQL (optional)

Automation: Schedule library (upgradeable to Airflow)

Testing: Pytest with coverage

Visualization: Matplotlib, Seaborn

Configuration: YAML + Environment Variables

Project Structure
text
financial-data-pipeline/
├── src/
│   ├── config.py              # Configuration management
│   ├── cache_manager.py       # API response caching
│   ├── data_ingestion.py      # Alpha Vantage integration
│   ├── data_cleaning.py       # Data validation and cleaning
│   ├── feature_engineering.py # Financial indicator creation
│   ├── anomaly_detection.py   # Multi-strategy anomaly detection
│   ├── database_loader.py     # SQL/CSV storage
│   └── visualization.py       # Dashboard generation
├── tests/
│   └── test_data_cleaning.py
├── data/
│   ├── raw/                   # Raw API responses
│   ├── processed/             # Cleaned and featured data
│   └── cache/                 # Cached API responses
├── config.yaml                # Configuration file
├── main.py                    # Entry point
├── benchmark.py               # Performance benchmarking
└── requirements.txt
Configuration
Edit config.yaml to customize:

yaml
api:
  symbols: ['AAPL', 'GOOGL', 'MSFT']  # Stocks to track
  output_size: "compact"  # 'compact' or 'full'

anomaly_detection:
  price_zscore_threshold: 3.0
  volume_ratio_threshold: 5.0
  vwap_divergence_threshold: 2.0
Key Learnings
This project demonstrates:

Real-world API Integration: Handling rate limits and data validation

Financial Data Processing: Working with OHLCV data and calculating VWAP

Anomaly Detection: Implementing multiple detection strategies

Production Engineering: Logging, error handling, testing, and documentation

License
MIT License - see LICENSE file for details.
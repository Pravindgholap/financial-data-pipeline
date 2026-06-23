import yaml
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config():
    """Load configuration from YAML file and environment variables"""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables if present
    if os.getenv('ALPHA_VANTAGE_KEY'):
        config['api']['alpha_vantage_key'] = os.getenv('ALPHA_VANTAGE_KEY')
    
    return config

config = load_config()
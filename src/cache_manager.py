import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import pickle
import hashlib
import json

class DataCache:
    """File-based cache for API responses to respect rate limits"""
    
    def __init__(self, cache_dir="data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        """Load cache metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save cache metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _get_cache_key(self, symbol, **kwargs):
        """Generate a unique cache key"""
        key_str = f"{symbol}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, symbol, max_age_hours=24, **kwargs):
        """Retrieve cached data if it exists and is recent"""
        cache_key = self._get_cache_key(symbol, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.parquet"
        
        if cache_file.exists():
            # Check age
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < timedelta(hours=max_age_hours):
                print(f"Cache HIT for {symbol} (age: {cache_age.total_seconds()/3600:.1f}h)")
                return pd.read_parquet(cache_file)
            else:
                print(f"Cache EXPIRED for {symbol} (age: {cache_age.total_seconds()/3600:.1f}h)")
        
        print(f"Cache MISS for {symbol}")
        return None
    
    def set(self, symbol, df, **kwargs):
        """Store data in cache"""
        cache_key = self._get_cache_key(symbol, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.parquet"
        
        # Save the dataframe
        df.to_parquet(cache_file)
        
        # Update metadata
        self.metadata[cache_key] = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'rows': len(df),
            'columns': list(df.columns),
            'kwargs': kwargs
        }
        self._save_metadata()
        print(f"💾 Cached {len(df):,} rows for {symbol}")
    
    def clear(self, symbol=None):
        """Clear cache for a specific symbol or all cache"""
        if symbol:
            for key, meta in self.metadata.items():
                if meta['symbol'] == symbol:
                    cache_file = self.cache_dir / f"{key}.parquet"
                    if cache_file.exists():
                        cache_file.unlink()
                    del self.metadata[key]
            self._save_metadata()
            print(f"🧹 Cleared cache for {symbol}")
        else:
            for file in self.cache_dir.glob("*.parquet"):
                file.unlink()
            self.metadata = {}
            self._save_metadata()
            print("🧹 Cleared all cache")
    
    def get_stats(self):
        """Get cache statistics"""
        stats = {
            'total_symbols': len(set(m['symbol'] for m in self.metadata.values())),
            'total_files': len(self.metadata),
            'total_rows': sum(m['rows'] for m in self.metadata.values()),
            'symbols': {}
        }
        for key, meta in self.metadata.items():
            symbol = meta['symbol']
            if symbol not in stats['symbols']:
                stats['symbols'][symbol] = {'files': 0, 'rows': 0}
            stats['symbols'][symbol]['files'] += 1
            stats['symbols'][symbol]['rows'] += meta['rows']
        return stats
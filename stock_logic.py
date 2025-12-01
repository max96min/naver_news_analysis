import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, date
import json
import os

STOCK_CACHE_FILE = "stock_cache.json"

def save_stock_cache(stock_df, min_cap):
    """Save stock data to cache file with timestamp"""
    cache_data = {
        "date": str(date.today()),
        "min_cap": min_cap,
        "data": stock_df.to_dict('records')
    }
    try:
        with open(STOCK_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving stock cache: {e}")

def load_stock_cache(min_cap):
    """Load stock data from cache if valid (same day and same min_cap)"""
    if not os.path.exists(STOCK_CACHE_FILE):
        return None
    
    try:
        with open(STOCK_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Check if cache is from today and has same min_cap
        if cache_data.get('date') == str(date.today()) and cache_data.get('min_cap') == min_cap:
            return pd.DataFrame(cache_data['data'])
        else:
            return None
    except Exception as e:
        print(f"Error loading stock cache: {e}")
        return None

def get_high_cap_stocks(min_cap=500000000000, force_refresh=False):
    """
    Fetches a list of Korean stock names with market capitalization >= min_cap.
    Default min_cap is 500 Billion KRW.
    Uses daily cache unless force_refresh is True.
    """
    # Try to load from cache first
    if not force_refresh:
        cached_df = load_stock_cache(min_cap)
        if cached_df is not None:
            print(f"Using cached stock data from {date.today()}")
            return cached_df
    
    print("Fetching fresh stock data from FinanceDataReader...")
    try:
        # Fetch list of all stocks in KRX (KOSPI + KOSDAQ)
        df_krx = fdr.StockListing('KRX')
        
        # Filter by Market Cap (Marcap)
        # Note: 'Marcap' column might need to be fetched separately or is available in KRX listing.
        # FDR's 'KRX' listing usually contains 'Marcap'. Let's verify.
        # Actually, 'KRX' listing has 'Marcap' column.
        
        if 'Marcap' in df_krx.columns:
            # Filter by Market Cap
            high_cap_df = df_krx[df_krx['Marcap'] >= min_cap].copy()
            
            # Select relevant columns
            # Actual columns: Code, Name, Close, Changes, ChagesRatio, Marcap
            cols = ['Name', 'Code', 'Close', 'Changes', 'ChagesRatio', 'Marcap']
            # Check if columns exist to be safe
            available_cols = [c for c in cols if c in high_cap_df.columns]
            
            result_df = high_cap_df[available_cols]
            
            # Save to cache
            save_stock_cache(result_df, min_cap)
            
            return result_df
        else:
            print("Warning: 'Marcap' column not found in stock data.")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame()

def get_top_trading_stocks(top_n=30):
    """
    Fetches top N stocks by trading volume (Amount) from KRX.
    Returns DataFrame with stock names and trading info.
    """
    try:
        # Fetch all KRX stocks
        df_krx = fdr.StockListing('KRX')
        
        if 'Amount' in df_krx.columns:
            # Sort by trading amount (거래대금) and get top N
            top_stocks = df_krx.nlargest(top_n, 'Amount').copy()
            
            # Select relevant columns
            cols = ['Name', 'Code', 'Close', 'Changes', 'ChagesRatio', 'Amount', 'Volume']
            available_cols = [c for c in cols if c in top_stocks.columns]
            
            return top_stocks[available_cols]
        else:
            print("Warning: 'Amount' column not found in stock data.")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error fetching top trading stocks: {e}")
        return pd.DataFrame()

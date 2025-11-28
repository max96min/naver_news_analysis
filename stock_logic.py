import FinanceDataReader as fdr
import pandas as pd

def get_high_cap_stocks(min_cap=500000000000):
    """
    Fetches a list of Korean stock names with market capitalization >= min_cap.
    Default min_cap is 500 Billion KRW.
    """
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
            
            return high_cap_df[available_cols]
        else:
            print("Warning: 'Marcap' column not found in stock data.")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame()

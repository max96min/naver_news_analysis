import requests
import pandas as pd
from datetime import datetime, date, timedelta
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

def fetch_naver_sise_data(market='KOSPI', page=1):
    """
    Fetch stock data from Naver Finance sise (시세) API.
    market: 'KOSPI' or 'KOSDAQ'
    """
    market_code = 'KOSPI' if market == 'KOSPI' else 'KOSDAQ'
    
    url = "https://finance.naver.com/api/sise/etfItemList.nhn"
    
    # Use sise/marketSum API for market cap data
    url = f"https://finance.naver.com/sise/sise_market_sum.naver"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.naver.com/",
    }
    
    params = {
        "sosok": "0" if market == 'KOSPI' else "1",  # 0: KOSPI, 1: KOSDAQ
        "page": page
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse HTML to extract stock data
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main table
        table = soup.select_one('table.type_2')
        if not table:
            return pd.DataFrame(), False
        
        stocks = []
        rows = table.select('tbody tr')
        
        for row in rows:
            cols = row.select('td')
            if len(cols) < 10:
                continue
            
            # Extract data from columns
            try:
                # Column 1: Rank (순위) - skip
                # Column 2: Name (종목명)
                name_tag = cols[1].select_one('a')
                if not name_tag:
                    continue
                name = name_tag.text.strip()
                
                # Extract code from link
                href = name_tag.get('href', '')
                code = ''
                if 'code=' in href:
                    code = href.split('code=')[1].split('&')[0]
                
                # Column 3: Current price (현재가)
                close = cols[2].text.strip().replace(',', '')
                
                # Column 4: Change (전일비)
                changes = cols[3].text.strip().replace(',', '').replace('+', '')
                
                # Column 5: Change ratio (등락률)
                changes_ratio = cols[4].text.strip().replace('%', '').replace('+', '')
                
                # Column 7: Market cap (시가총액) - in 억원
                marcap_text = cols[6].text.strip().replace(',', '')
                
                if name and code and marcap_text:
                    # Convert 억원 to 원 (multiply by 100,000,000)
                    try:
                        marcap = int(marcap_text) * 100000000
                    except:
                        marcap = 0
                    
                    stocks.append({
                        'Name': name,
                        'Code': code,
                        'Close': int(close) if close.isdigit() or close.lstrip('-').isdigit() else 0,
                        'Changes': int(changes) if changes.lstrip('-').isdigit() else 0,
                        'ChagesRatio': float(changes_ratio) if changes_ratio.replace('.', '').replace('-', '').isdigit() else 0,
                        'Marcap': marcap
                    })
            except Exception as e:
                continue
        
        # Check if there are more pages
        paging = soup.select_one('td.pgRR')
        has_next = paging is not None
        
        return pd.DataFrame(stocks), has_next
        
    except Exception as e:
        print(f"Error fetching Naver sise data: {e}")
        return pd.DataFrame(), False

def fetch_all_naver_stocks(market='KOSPI', max_pages=10):
    """Fetch all stocks from Naver Finance with pagination"""
    all_stocks = []
    
    for page in range(1, max_pages + 1):
        df, has_next = fetch_naver_sise_data(market, page)
        
        if not df.empty:
            all_stocks.append(df)
            print(f"Fetched {market} page {page}: {len(df)} stocks")
        
        if not has_next or df.empty:
            break
    
    if all_stocks:
        return pd.concat(all_stocks, ignore_index=True)
    return pd.DataFrame()

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
    
    print("Fetching fresh stock data from Naver Finance...")
    try:
        # Fetch from both KOSPI and KOSDAQ
        kospi_df = fetch_all_naver_stocks('KOSPI', max_pages=15)
        kosdaq_df = fetch_all_naver_stocks('KOSDAQ', max_pages=15)
        
        # Combine
        if not kospi_df.empty or not kosdaq_df.empty:
            dfs = [df for df in [kospi_df, kosdaq_df] if not df.empty]
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
            else:
                combined_df = pd.DataFrame()
        else:
            combined_df = pd.DataFrame()
        
        if combined_df.empty:
            print("Failed to fetch stock data from Naver Finance")
            return pd.DataFrame()
        
        # Filter by market cap
        high_cap_df = combined_df[combined_df['Marcap'] >= min_cap].copy()
        
        # Sort by market cap descending
        high_cap_df = high_cap_df.sort_values('Marcap', ascending=False)
        
        # Reset index
        high_cap_df = high_cap_df.reset_index(drop=True)
        
        # Save to cache
        save_stock_cache(high_cap_df, min_cap)
        
        print(f"Successfully filtered {len(high_cap_df)} stocks with market cap >= {min_cap/1e12:.1f}T KRW")
        return high_cap_df
            
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        import traceback
        traceback.print_exc()
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

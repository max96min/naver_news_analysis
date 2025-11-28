import streamlit as st
import os
from dotenv import load_dotenv
import news_logic
import stock_logic
import importlib
importlib.reload(news_logic)
importlib.reload(stock_logic)
from news_logic import fetch_naver_news, group_news, summarize_group, filter_news_by_date, group_news_by_stock
from stock_logic import get_high_cap_stocks
from config_logic import load_config, save_config
from datetime import date

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Naver News AI Summarizer", layout="wide")

# Load Config
config = load_config()

def save_settings():
    """Callback to save current settings to config file"""
    new_config = {
        "grouping_method": st.session_state.grouping_method,
        "sort_option": st.session_state.sort_option,
        "similarity_threshold": st.session_state.get("similarity_threshold", 0.5),
        "enable_summary": st.session_state.enable_summary,
        "group_sort_by": st.session_state.group_sort_by
    }
    save_config(new_config)

st.title("📰 Naver News AI Summarizer")

# Sidebar for API Keys
with st.sidebar:
    st.header("Settings")
    
    # Naver Keys
    naver_client_id = os.getenv("NAVER_CLIENT_ID") or st.text_input("Naver Client ID", type="password")
    naver_client_secret = os.getenv("NAVER_CLIENT_SECRET") or st.text_input("Naver Client Secret", type="password")
    
    # OpenAI Key
    openai_api_key = os.getenv("OPENAI_API_KEY") or st.text_input("OpenAI API Key", type="password")
    
    st.markdown("---")
    st.markdown("Adjust Parameters")
    
    # Grouping Method
    grouping_method = st.radio(
        "Grouping Method", 
        ["Semantic Similarity (AI)", "Stock Name Matching"],
        index=["Semantic Similarity (AI)", "Stock Name Matching"].index(config["grouping_method"]),
        key="grouping_method",
        on_change=save_settings
    )
    
    # Stock Settings (Only if Stock Name Matching is selected)
    min_marcap = 500000000000 # Default
    if grouping_method == "Stock Name Matching":
        st.markdown("### Stock Filter")
        # Slider for Market Cap (in Trillions for easier UI, but value in Bytes)
        # 500 Billion = 0.5 Trillion
        marcap_trillion = st.slider(
            "Min Market Cap (Trillion KRW)", 
            0.1, 50.0, 0.5, 0.1,
            help="Filter stocks by minimum market capitalization."
        )
        min_marcap = int(marcap_trillion * 1000000000000)
    
    # Date Filter
    st.subheader("Date Filter")
    today = date.today()
    start_date = st.date_input("Start Date", today)
    end_date = st.date_input("End Date", today)
    
    sort_option = st.selectbox(
        "Sort Articles By", 
        ["Relevance", "Date"], 
        index=["Relevance", "Date"].index(config["sort_option"]),
        key="sort_option",
        on_change=save_settings
    )
    sort_param = "sim" if sort_option == "Relevance" else "date"

    if grouping_method == "Semantic Similarity (AI)":
        similarity_threshold = st.slider(
            "Grouping Similarity Threshold", 
            0.1, 1.0, 
            config["similarity_threshold"], 
            0.05,
            key="similarity_threshold",
            on_change=save_settings
        )
    
    # Group Sorting
    group_sort_by = st.selectbox(
        "Sort Groups By",
        ["Default", "Article Count"],
        index=["Default", "Article Count"].index(config["group_sort_by"]),
        key="group_sort_by",
        on_change=save_settings
    )

    enable_summary = st.checkbox(
        "Enable AI Summarization", 
        value=config["enable_summary"],
        key="enable_summary",
        on_change=save_settings
    )

# Main Interface
keyword = st.text_input("Enter Search Keyword", "인공지능")

# Stock List Display (if Stock Name Matching)
if grouping_method == "Stock Name Matching":
    with st.expander("View Tracked Stock List"):
        with st.spinner("Fetching stock list..."):
            stock_df = get_high_cap_stocks(min_marcap)
            if not stock_df.empty:
                st.dataframe(stock_df)
                st.caption(f"Total {len(stock_df)} stocks tracked.")
            else:
                st.warning("No stocks found with current criteria.")

if st.button("Search News"):
    if not naver_client_id or not naver_client_secret:
        st.error("Please provide Naver API Keys in the sidebar or .env file.")
    else:
        with st.spinner(f"Fetching news for '{keyword}'..."):
            news_items = fetch_naver_news(keyword, naver_client_id, naver_client_secret, sort=sort_param)
        
        if not news_items:
            st.warning("No news found or error occurred.")
        else:
            # Filter by date
            filtered_items = filter_news_by_date(news_items, start_date, end_date)
            
            if not filtered_items:
                st.warning(f"Found {len(news_items)} articles, but none match the selected date range ({start_date} ~ {end_date}). Try changing the 'Sort By' to 'Date' or widening the range.")
            else:
                st.success(f"Found {len(filtered_items)} articles (from {len(news_items)} raw results). Grouping...")
                
                groups = []
                if grouping_method == "Semantic Similarity (AI)":
                    with st.spinner("Grouping similar news (AI)..."):
                        # Use session state value for threshold
                        threshold = st.session_state.get("similarity_threshold", 0.5)
                        groups = group_news(filtered_items, openai_api_key, threshold)
                else:
                    with st.spinner("Fetching stock data and grouping..."):
                        # Re-fetch or use cached if we want, but calling again is safer for now
                        # We already fetched it for display if expanded, but let's fetch again or optimize later.
                        # For now, just fetch.
                        stock_df = get_high_cap_stocks(min_marcap)
                        groups = group_news_by_stock(filtered_items, stock_df)
                
                # Sort Groups
                if group_sort_by == "Article Count":
                    groups.sort(key=lambda x: len(x['articles']), reverse=True)

                st.info(f"Grouped into {len(groups)} clusters.")
                
                for i, group in enumerate(groups):
                    group_name = group.get('name', f"Group {i+1}")
                    
                    # Add Price Info if available
                    price = group.get('price')
                    changes_ratio = group.get('changes_ratio')
                    
                    header_text = f"### {group_name} ({len(group['articles'])} articles)"
                    if price is not None and price != 0:
                        # Format price with commas (convert to float first)
                        try:
                            price_val = float(price)
                            price_str = f"{price_val:,.0f} KRW"
                        except (ValueError, TypeError):
                            price_str = f"{price} KRW"
                        
                        # Format percentage change
                        if changes_ratio is not None:
                            try:
                                pct = float(changes_ratio)  # Already in percentage format
                            except (ValueError, TypeError):
                                pct = 0
                            if pct > 0:
                                pct_str = f"+{pct:.2f}%"
                                color = "red"  # Korean stock color for up
                            elif pct < 0:
                                pct_str = f"{pct:.2f}%"
                                color = "blue"  # Korean stock color for down
                            else:
                                pct_str = "0.00%"
                                color = "gray"
                            
                            header_text += f" | <span style='color:{color}'>{price_str} ({pct_str})</span>"
                        else:
                            header_text += f" | {price_str}"
                    
                    st.markdown(header_text, unsafe_allow_html=True)
                    
                    # AI Summary
                    if enable_summary and openai_api_key:
                        with st.spinner(f"Summarizing Group {i+1}..."):
                            summary = summarize_group(group, openai_api_key)
                            st.markdown(f"> **AI Summary:** {summary}")
                    elif enable_summary and not openai_api_key:
                        st.warning("OpenAI API Key missing for summarization.")
                    
                    # Show First Article
                    if group['articles']:
                        first_article = group['articles'][0]
                        st.markdown(f"**[{first_article['title']}]({first_article['link']})**")
                        st.caption(f"{first_article['pubDate']} | {first_article['description']}")
                    
                    # Show Remaining Articles
                    if len(group['articles']) > 1:
                        with st.expander(f"View {len(group['articles']) - 1} More Articles"):
                            for article in group['articles'][1:]:
                                st.markdown(f"- [{article['title']}]({article['link']})")
                                st.caption(f"{article['pubDate']} | {article['description']}")
                    
                    st.markdown("---")

st.markdown("Built with Streamlit, Naver API, and OpenAI.")

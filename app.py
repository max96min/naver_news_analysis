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
        "group_sort_by": st.session_state.group_sort_by,
        "min_marcap_trillion": st.session_state.get("min_marcap_trillion", 0.5)
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
            0.1, 50.0, 
            config["min_marcap_trillion"], 
            0.1,
            help="Filter stocks by minimum market capitalization.",
            key="min_marcap_trillion",
            on_change=save_settings
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
st.markdown("### 🔍 Search Keywords")

# Favorite keywords management
col1, col2 = st.columns([3, 1])

with col1:
    # Multi-keyword input
    keywords_input = st.text_input(
        "Enter keywords (comma-separated)", 
        "인공지능",
        help="Enter multiple keywords separated by commas (e.g., 삼성전자, SK하이닉스)"
    )
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    add_to_favorites = st.button("⭐ Add to Favorites", use_container_width=True)

# Add current keywords to favorites
if add_to_favorites and keywords:
    current_favorites = config.get("favorite_keywords", [])
    for keyword in keywords:
        if keyword not in current_favorites:
            current_favorites.append(keyword)
    config["favorite_keywords"] = current_favorites
    save_config(config)
    st.success(f"Added to favorites!")
    st.rerun()

# Display favorite keywords
favorite_keywords = config.get("favorite_keywords", [])
if favorite_keywords:
    st.markdown("**⭐ Favorite Keywords:**")
    
    # Create columns for favorite keyword buttons
    cols = st.columns(min(len(favorite_keywords), 5))
    
    for idx, fav_keyword in enumerate(favorite_keywords):
        col_idx = idx % 5
        with cols[col_idx]:
            # Button to use this keyword
            if st.button(f"🔍 {fav_keyword}", key=f"use_{fav_keyword}", use_container_width=True):
                st.session_state.selected_keyword = fav_keyword
                st.rerun()
    
    # Remove favorites section
    with st.expander("Manage Favorites"):
        keywords_to_remove = st.multiselect(
            "Select keywords to remove",
            favorite_keywords,
            key="remove_favorites"
        )
        if st.button("Remove Selected") and keywords_to_remove:
            updated_favorites = [k for k in favorite_keywords if k not in keywords_to_remove]
            config["favorite_keywords"] = updated_favorites
            save_config(config)
            st.success("Removed from favorites!")
            st.rerun()

# Use selected favorite keyword if available
if 'selected_keyword' in st.session_state:
    keywords = [st.session_state.selected_keyword]
    keywords_input = st.session_state.selected_keyword
    del st.session_state.selected_keyword

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

if st.button("🔍 Search News", type="primary", use_container_width=True):
    if not naver_client_id or not naver_client_secret:
        st.error("Please provide Naver API Keys in the sidebar or .env file.")
    elif not keywords:
        st.warning("Please enter at least one keyword.")
    else:
        # Search for each keyword
        all_news_items = []
        
        for keyword in keywords:
            with st.spinner(f"Fetching news for '{keyword}'..."):
                news_items = fetch_naver_news(keyword, naver_client_id, naver_client_secret, sort=sort_param)
                all_news_items.extend(news_items)
        
        if not all_news_items:
            st.warning("No news found or error occurred.")
        else:
            # Remove duplicates based on link
            seen_links = set()
            unique_news_items = []
            for item in all_news_items:
                if item['link'] not in seen_links:
                    seen_links.add(item['link'])
                    unique_news_items.append(item)
            
            # Filter by date
            filtered_items = filter_news_by_date(unique_news_items, start_date, end_date)
            
            if not filtered_items:
                st.warning(f"Found {len(unique_news_items)} articles, but none match the selected date range ({start_date} ~ {end_date}). Try changing the 'Sort By' to 'Date' or widening the range.")
            else:
                st.success(f"Found {len(filtered_items)} articles for {len(keywords)} keyword(s) (from {len(unique_news_items)} raw results). Grouping...")
                
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

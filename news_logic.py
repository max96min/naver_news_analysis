import os
import requests
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from openai import OpenAI
import json

from datetime import datetime

def fetch_naver_news(keyword, client_id, client_secret, display=100, sort='sim'):
    """
    Fetches news from Naver Open API.
    sort: 'sim' (similarity) or 'date' (date)
    """
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": keyword,
        "display": display,
        "sort": sort 
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('items', [])
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def filter_news_by_date(news_items, start_date, end_date):
    """
    Filters news items by date range (inclusive).
    Naver pubDate format: 'Thu, 28 Nov 2024 14:00:00 +0900'
    """
    filtered = []
    for item in news_items:
        try:
            # Parse pubDate. Note: %z is for timezone
            pub_date_str = item['pubDate']
            pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z").date()
            
            if start_date <= pub_date <= end_date:
                filtered.append(item)
        except Exception as e:
            print(f"Error parsing date {item['pubDate']}: {e}")
            continue
    return filtered

def get_embedding(text, client, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding

def clean_html(text):
    """
    Replaces HTML tags with Markdown or removes them.
    Naver API returns <b>keyword</b>. We replace it with **keyword** for Markdown bolding.
    """
    return text.replace('<b>', '**').replace('</b>', '**').replace('&quot;', '"')

def group_news(news_items, api_key, similarity_threshold=0.5):
    """
    Groups similar news articles based on their title and description using OpenAI Embeddings and Cosine Similarity.
    """
    if not news_items:
        return []
    
    if not api_key:
        print("OpenAI API Key missing for grouping.")
        # Fallback to single group or no grouping if key is missing, 
        # but for now let's just return individual items as groups or handle gracefully.
        # Returning one big group might be bad, returning all separate is safer.
        return [{'articles': [item], 'summary': None} for item in news_items]

    client = OpenAI(api_key=api_key)

    # Prepare text for clustering (Title + Description)
    cleaned_items = []
    for item in news_items:
        # Clean title and description for display and embedding
        title = clean_html(item['title'])
        description = clean_html(item['description'])
        
        # Create a copy of item with cleaned fields
        cleaned_item = item.copy()
        cleaned_item['title'] = title
        cleaned_item['description'] = description
        
        cleaned_items.append({
            'title': title,
            'description': description,
            'link': item['link'],
            'pubDate': item['pubDate'],
            'full_text': title, # Use only title for grouping as requested
            'original_item': cleaned_item # Store cleaned item to return in group
        })

    if len(cleaned_items) < 2:
        # Return cleaned items wrapped in group
        return [{'articles': [x['original_item'] for x in cleaned_items], 'summary': None}]

    # Generate Embeddings
    try:
        embeddings = [get_embedding(item['full_text'], client) for item in cleaned_items]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return [{'articles': [x['original_item'] for x in cleaned_items], 'summary': None}] # Fallback
    
    # Calculate Cosine Similarity
    cosine_sim = cosine_similarity(embeddings, embeddings)
    
    # Grouping Logic (Simple greedy clustering)
    visited = [False] * len(cleaned_items)
    groups = []
    
    for i in range(len(cleaned_items)):
        if visited[i]:
            continue
        
        current_group = [cleaned_items[i]['original_item']]
        visited[i] = True
        
        for j in range(i + 1, len(cleaned_items)):
            if not visited[j] and cosine_sim[i][j] >= similarity_threshold:
                current_group.append(cleaned_items[j]['original_item'])
                visited[j] = True
        
        groups.append({'articles': current_group, 'summary': None})
        
    return groups

def group_news_by_stock(news_items, stock_df):
    """
    Groups news articles based on whether their title contains a stock name from stock_df.
    stock_df: DataFrame with columns ['Name', 'Close', 'Chg', ...]
    """
    if not news_items:
        return []
    
    if stock_df.empty:
        return []
        
    groups_map = {} # {stock_name: {'articles': [], 'price_info': {...}}}
    others = []
    
    # Create a dictionary for fast lookup of stock info
    # {Name: {Close: ..., Changes: ..., ChagesRatio: ...}}
    stock_info_map = stock_df.set_index('Name')[['Close', 'Changes', 'ChagesRatio']].to_dict('index')
    stock_names = set(stock_info_map.keys())
    
    for item in news_items:
        # Clean the item fields
        cleaned_item = item.copy()
        cleaned_item['title'] = clean_html(item['title'])
        cleaned_item['description'] = clean_html(item['description'])
        
        title = cleaned_item['title']
        matched = False
        
        for stock in stock_names:
            if stock in title:
                if stock not in groups_map:
                    groups_map[stock] = {
                        'articles': [],
                        'price_info': stock_info_map[stock]
                    }
                groups_map[stock]['articles'].append(cleaned_item)
                matched = True
        
        if not matched:
            others.append(cleaned_item)
            
    # Convert map to list of groups
    groups = []
    for stock, data in groups_map.items():
        price = data['price_info'].get('Close', 0)
        changes = data['price_info'].get('Changes', 0)  # Change amount
        changes_ratio = data['price_info'].get('ChagesRatio', 0)  # Change percentage
        
        groups.append({
            'articles': data['articles'], 
            'summary': None, 
            'name': stock,
            'price': price,
            'changes': changes,
            'changes_ratio': changes_ratio
        })
        
    # Add 'Others' group if needed
    if others:
        groups.append({'articles': others, 'summary': None, 'name': 'Other News', 'price': None, 'changes': None, 'changes_ratio': None})
        
    return groups

def summarize_group(group, api_key, model="gpt-3.5-turbo"):
    """
    Summarizes a group of news articles using OpenAI API.
    """
    if not api_key:
        return "API Key missing."
    
    client = OpenAI(api_key=api_key)
    
    articles = group['articles']
    # Combine titles and descriptions for context
    text_to_summarize = "\n\n".join([f"Title: {a['title']}\nDescription: {a['description']}" for a in articles[:5]]) # Limit to top 5 to save tokens
    
    prompt = f"""
    You are a helpful news assistant. Please summarize the following related news articles into a single concise paragraph in Korean.
    Focus on the main event or topic they are discussing.
    
    News Articles:
    {text_to_summarize}
    
    Summary:
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {e}"

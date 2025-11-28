import json
import os

CONFIG_FILE = "user_config.json"

DEFAULT_CONFIG = {
    "grouping_method": "Semantic Similarity (AI)",
    "sort_option": "Relevance",
    "similarity_threshold": 0.5,
    "enable_summary": True,
    "group_sort_by": "Default", # Default or Article Count
    "min_marcap_trillion": 0.5,  # Market cap in trillion KRW
    "favorite_keywords": []  # List of favorite keywords
}

def load_config():
    """
    Loads configuration from user_config.json.
    Returns default config if file doesn't exist or error occurs.
    """
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Merge with default to ensure all keys exist
            merged_config = DEFAULT_CONFIG.copy()
            merged_config.update(config)
            return merged_config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """
    Saves configuration to user_config.json.
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")

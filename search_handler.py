import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

def clean_price(price_input):
    """
    Safely converts a price string (e.g., '₹1,299.00', '$10') 
    into a clean float (1299.00).
    """
    if price_input is None:
        return 0.0
    
    # If it's already a number, return it
    if isinstance(price_input, (int, float)):
        return float(price_input)
    
    if isinstance(price_input, str):
        try:
            # 1. Remove currency symbols (₹, $, etc), commas, and letters
            # Keeps only digits (0-9) and the decimal point (.)
            clean_str = re.sub(r'[^\d.]', '', price_input)
            
            if not clean_str:
                return 0.0
                
            return float(clean_str)
        except ValueError:
            return 0.0
            
    return 0.0

def is_relevant_result(product_title, query):
    """
    Check if product title is relevant to the search query.
    Helps filter out accessories and unrelated products.
    """
    if not product_title or not query:
        return True  # Default to showing if we can't determine
    
    product_lower = product_title.lower()
    query_lower = query.lower()
    
    # Extract key terms from query (ignore common words)
    ignore_words = {'the', 'a', 'an', 'for', 'with', 'and', 'or', 'in', 'on', 'at'}
    query_terms = [term for term in query_lower.split() if term not in ignore_words and len(term) > 2]
    
    if not query_terms:
        return True
    
    # Check if at least some key terms appear in the product title
    matches = sum(1 for term in query_terms if term in product_lower)
    match_ratio = matches / len(query_terms)
    
    # If less than 30% of query terms match, likely not relevant
    if match_ratio < 0.3:
        return False
    
    # Additional filtering: Check for accessory keywords
    accessory_keywords = ['case', 'cover', 'charger', 'cable', 'adapter', 'screen protector', 
                          'holder', 'mount', 'stand', 'bag', 'pouch', 'sleeve']
    
    # If query is about a main product (phone, laptop, etc.) but result is an accessory, filter it
    main_product_keywords = ['smartphone', 'phone', 'laptop', 'tablet', 'watch', 'camera', 
                             'headphones', 'earbuds', 'speaker']
    
    query_has_main_product = any(keyword in query_lower for keyword in main_product_keywords)
    result_is_accessory = any(keyword in product_lower for keyword in accessory_keywords)
    
    # If searching for main product but result is accessory, mark as not relevant
    if query_has_main_product and result_is_accessory:
        return False
    
    return True

def search_products(query, country='us', sort_by='BEST_MATCH'):
    """
    Search for products using RapidAPI.
    
    Args:
        query: Search query string
        country: Country code (us, in, uk, etc.)
        sort_by: Sort order - BEST_MATCH (default), LOWEST_PRICE, HIGHEST_PRICE, etc.
    """
    print(f"🔎 Searching for: {query}...")
    print(f"🌍 Target Market: {country.upper()}")
    print(f"📊 Sort By: {sort_by}")

    url = "https://real-time-product-search.p.rapidapi.com/search-v2"

    querystring = {
        "q": query,
        "country": country,
        "language": "en",
        "sort_by": sort_by  # Dynamic sorting - no hardcoding
    }

    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": os.getenv("RAPIDAPI_HOST")
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        
        data = response.json()
        products = data.get('data', {}).get('products', [])

        if not products:
            print("⚠️ No products found in this region.")
            return []

        cleaned_results = []

        for item in products:
            # Attempt to grab the price from various possible keys
            raw_price = item.get('offer', {}).get('price') or \
                        item.get('product_price') or \
                        item.get('price')
            
            final_price = clean_price(raw_price)

            if final_price == 0.0:
                continue
            
            # Get product title
            product_title = item.get('product_title', 'Unknown')
            
            # Apply relevance filtering
            if not is_relevant_result(product_title, query):
                continue
            
            # Detect currency (API usually matches country, e.g., INR for India)
            currency = "INR" if country == 'in' else "USD"

            # Extract Image
            image_url = item.get('product_photos', [None])[0] or \
                        item.get('product_photo') or \
                        "https://placehold.co/200x200?text=No+Image"

            cleaned_results.append({
                'name': product_title,
                'price': final_price,
                'currency': currency, 
                'store': item.get('offer', {}).get('store_name') or item.get('merchant', {}).get('name', 'Unknown'),
                'link': item.get('offer', {}).get('offer_page_url') or item.get('offer_page_url'),
                'image': image_url
            })
        
        print(f"✅ Found {len(cleaned_results)} relevant results in {country.upper()}.")
        return cleaned_results

    except Exception as e:
        print(f"❌ Search Error: {e}")
        return []
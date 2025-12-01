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

def search_products(query, country='us'):
    print(f"🔎 Searching for: {query}...")
    print(f"🌍 Target Market: {country.upper()}")

    url = "https://real-time-product-search.p.rapidapi.com/search-v2"

    querystring = {
        "q": query,
        "country": country,
        "language": "en",
        "sort_by": "LOWEST_PRICE"
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
            
            # Detect currency (API usually matches country, e.g., INR for India)
            currency = "INR" if country == 'in' else "USD"

            # Extract Image
            image_url = item.get('product_photos', [None])[0] or \
                        item.get('product_photo') or \
                        "https://placehold.co/200x200?text=No+Image"

            cleaned_results.append({
                'name': item.get('product_title', 'Unknown'),
                'price': final_price,
                'currency': currency, 
                'store': item.get('offer', {}).get('store_name') or item.get('merchant', {}).get('name', 'Unknown'),
                'link': item.get('offer', {}).get('offer_page_url') or item.get('offer_page_url'),
                'image': image_url
            })

        # Sort strictly by price
        cleaned_results.sort(key=lambda x: x['price'])
        
        print(f"✅ Found {len(cleaned_results)} results in {country.upper()}.")
        return cleaned_results

    except Exception as e:
        print(f"❌ Search Error: {e}")
        return []
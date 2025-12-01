import base64
import os
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Claude Client
try:
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
except Exception as e:
    print(f"❌ Initialization Error: {e}")
    client = None

def encode_image(image_path):
    """
    Helper function to convert an image file into a base64 string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_product_query(image_path):
    """
    Uses Claude 3.7 Sonnet to identify the product and return a search query.
    """
    if not client:
        print("❌ API Client not initialized. Check your API Key.")
        return None

    # Clean up path artifacts (Windows specific)
    image_path = image_path.strip('"').strip("'")

    if not os.path.exists(image_path):
        print(f"❌ Error: File not found at {image_path}")
        return None

    print(f"👁️  Asking Claude 3.7 to identify: {os.path.basename(image_path)}...")
    
    try:
        base64_image = encode_image(image_path)
        
        # Determine media type based on extension
        media_type = "image/jpeg"
        if image_path.lower().endswith(".png"):
            media_type = "image/png"
        elif image_path.lower().endswith(".webp"):
            media_type = "image/webp"

        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "You are identifying a product for online shopping search.\n\n"
                                "CRITICAL INSTRUCTIONS:\n"
                                "1. Focus ONLY on the PRIMARY/MAIN product in the image\n"
                                "2. IGNORE accessories, cases, covers, boxes, packaging, or background items\n"
                                "3. If you see a phone, return the PHONE itself, NOT phone cases or covers\n"
                                "4. If you see a laptop, return the LAPTOP itself, NOT laptop bags or accessories\n\n"
                                "REQUIRED FORMAT:\n"
                                "First identify the product CATEGORY (e.g., Smartphone, Laptop, Tablet, Watch, Headphones, Camera, Drink, Shoe)\n"
                                "Then provide: Brand, Model/Name, and Key Specifications if visible\n\n"
                                "Return ONLY the search query in this format:\n"
                                "[Category] Brand Model Specifications\n\n"
                                "EXAMPLES:\n"
                                "- Smartphone Apple iPhone 15 Pro 256GB\n"
                                "- Laptop Dell XPS 13 Intel i7\n"
                                "- Headphones Sony WH-1000XM5 Wireless\n"
                                "- Smartwatch Apple Watch Series 9 45mm\n"
                                "- Energy Drink Red Bull 250ml\n\n"
                                "Remember: Focus on the MAIN PRODUCT ONLY, not accessories or packaging."
                            )
                        }
                    ],
                }
            ],
        )

        # Extract text content from Claude's response
        search_query = message.content[0].text.strip()
        print(f"✅ Claude 3.7 Identified: {search_query}")
        return search_query

    except anthropic.APIStatusError as e:
        if e.status_code == 404:
            print("❌ Error: Model 'claude-3-7-sonnet-20250219' not found.")
            print("   -> Your API key might not have access to 3.7 yet, or you may need to add credits.")
        elif e.status_code == 400:
             print(f"❌ API Error: {e.message}")
        else:
             print(f"❌ API Error {e.status_code}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error in Vision Module: {e}")
        return None

# Quick Test Block
if __name__ == "__main__":
    print("Run main.py to use the full application.")
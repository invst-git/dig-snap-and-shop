import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from pyfiglet import Figlet

# Import our custom modules
import vision_handler
import search_handler

# Initialize Console for pretty printing
console = Console()

def print_banner():
    """Displays the cool ASCII header."""
    f = Figlet(font='slant')
    console.print(f"[bold cyan]{f.renderText('ShopScanner')}[/bold cyan]")
    console.print("[dim]Powered by Claude Vision & RapidAPI[/dim]\n")

def display_results(results):
    """Renders the search results in a clean table."""
    if not results:
        console.print("[bold red]❌ No results found or error occurred.[/bold red]")
        return

    table = Table(title="Shopping Results (Cheapest to Expensive)")

    table.add_column("Price", justify="right", style="green", no_wrap=True)
    table.add_column("Store", style="magenta")
    table.add_column("Product Name", style="white")
    table.add_column("Link", style="blue")

    for item in results:
        # Dynamic symbol based on currency code
        symbol = "₹" if item.get('currency') == 'INR' else "$"
        
        price_display = f"{symbol}{item['price']:,.2f}"
        link_display = f"[link={item['link']}]Open Link[/link]"
        
        table.add_row(
            price_display,
            item['store'],
            item['name'][:50] + "..." if len(item['name']) > 50 else item['name'],
            link_display
        )

    console.print(table)

def main():
    print_banner()

    # 1. Get Image Path
    # You can drag and drop a file into the terminal to get the path
    image_path = Prompt.ask("[bold yellow]📸 Drag & Drop an image file here[/bold yellow]")
    
    # Clean up path artifacts (Windows adds quotes sometimes)
    image_path = image_path.strip('"').strip("'")

    if not os.path.exists(image_path):
        console.print(f"[bold red]❌ File not found:[/bold red] {image_path}")
        return

    # 2. Vision Step
    with console.status("[bold green]🧠 Asking Claude to identify product...[/bold green]", spinner="dots"):
        query = vision_handler.get_product_query(image_path)
    
    if not query:
        console.print("[bold red]❌ AI could not identify the product.[/bold red]")
        return
    
    console.print(Panel(f"[bold]Search Query:[/bold] {query}", border_style="blue"))

    # 3. Search Step
    with console.status(f"[bold green]🔎 Searching prices for '{query}'...[/bold green]", spinner="earth"):
        results = search_handler.search_products(query)

    # 4. Display
    display_results(results)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]👋 Exiting...[/bold red]")
        sys.exit(0)
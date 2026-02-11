import os
import sys
from collections import Counter
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from rich.console import Console
from rich.table import Table

# Initialize Rich Console
console = Console()

# 1. Load Environment Variables
# Try finding .env.local in python-cli directory or parent
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir)) # assuming script is in python-cli/scripts
env_path = os.path.join(os.path.dirname(script_dir), '.env.local')

load_dotenv(env_path)
# Fallback
if not os.getenv('QDRANT_URL'):
    load_dotenv('.env.local')

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "normativas")

def list_municipalities():
    if not QDRANT_URL:
        console.print("[bold red]❌ Error: QDRANT_URL not found.[/bold red]")
        return

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    console.print(f"[bold]Scanning collection '{COLLECTION_NAME}' for municipalities...[/bold]")

    municipalities = Counter()
    next_offset = None
    
    try:
        while True:
            records, next_offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=100,
                offset=next_offset,
                with_payload=True,
                with_vectors=False
            )
            
            for record in records:
                # Client-side filtering
                if record.payload.get('source_type') != 'transparency_chunk':
                    continue
                    
                muni = record.payload.get('municipality', 'Unknown')
                municipalities[muni] += 1
                
            if next_offset is None:
                break
                
        # Display results
        table = Table(title="Indexed Municipalities")
        table.add_column("Municipality", style="cyan", no_wrap=True)
        table.add_column("Chunks Count", justify="right", style="green")
        
        for muni, count in municipalities.most_common():
            table.add_row(muni, str(count))
            
        console.print(table)
        console.print(f"\n[bold]Total Unique Municipalities:[/bold] {len(municipalities)}")
        
    except Exception as e:
        console.print(f"[red]Error querying Qdrant: {e}[/red]")

if __name__ == "__main__":
    list_municipalities()

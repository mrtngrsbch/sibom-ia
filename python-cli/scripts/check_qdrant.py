
import os
import sys
from rich.console import Console
from qdrant_client import QdrantClient

# Add parent dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# from config import COLLECTION_NAME
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "normativas")


def check_qdrant():
    console = Console()
    
    # Load env (simple version)
    from dotenv import load_dotenv
    
    # Try finding .env.local in python-cli directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # python-cli
    env_path = os.path.join(project_root, '.env.local')
    
    load_dotenv(env_path)
    
    if not os.getenv('QDRANT_URL'):
        # Fallback to current dir
        load_dotenv('.env.local')

    url = os.getenv('QDRANT_URL')

    key = os.getenv('QDRANT_API_KEY')
    
    if not url:
        console.print("[red]QDRANT_URL not found[/red]")
        return

    client = QdrantClient(url=url, api_key=key)
    
    
    from qdrant_client.http import models

    try:
        count = client.count(collection_name=COLLECTION_NAME)
        console.print(f"[bold green]Total Collection '{COLLECTION_NAME}' has {count.count} points.[/bold green]")
        
        # Get one point to see payload
        res = client.scroll(
            collection_name=COLLECTION_NAME, 
            limit=1
        )
        if res[0]:
            console.print("\n[bold]Sample Point Payload:[/bold]")
            console.print(res[0][0].payload)
            
    except Exception as e:
        console.print(f"[red]Error checking Qdrant: {e}[/red]")


if __name__ == "__main__":
    check_qdrant()

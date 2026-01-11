#!/usr/bin/env python3
"""
generate_embeddings.py

Generates OpenAI embeddings for all normativas and uploads them to Qdrant.
This is a ONE-TIME operation that costs ~$0.22 for 216K documents.

Usage:
    python3 generate_embeddings.py

Requirements:
    - OPENAI_API_KEY in environment
    - QDRANT_URL in environment
    - QDRANT_API_KEY in environment
    - normativas_index_minimal.json file

@version 1.0.0
@created 2026-01-10
@author Kiro AI (MIT Engineering Standards)
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict
import time
import hashlib

try:
    import openai
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from tqdm import tqdm
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Error: Missing required package: {e}")
    print("\nInstall dependencies:")
    print("  pip install openai qdrant-client tqdm python-dotenv")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()


def generate_uuid_from_id(doc_id: str) -> str:
    """
    Generate a valid UUID from document ID using MD5 hash
    Qdrant requires UUIDs or unsigned integers as point IDs
    """
    # Create MD5 hash of the ID
    hash_obj = hashlib.md5(str(doc_id).encode())
    hash_hex = hash_obj.hexdigest()
    
    # Format as UUID (8-4-4-4-12)
    uuid = f"{hash_hex[:8]}-{hash_hex[8:12]}-{hash_hex[12:16]}-{hash_hex[16:20]}-{hash_hex[20:32]}"
    return uuid

# ============================================================================
# CONFIGURATION
# ============================================================================

BATCH_SIZE = 100  # Process 100 documents at a time
COLLECTION_NAME = "normativas"
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_SIZE = 1536  # Dimensions for text-embedding-3-small

# ============================================================================
# INITIALIZATION
# ============================================================================

def load_environment():
    """Load and validate environment variables"""
    openai_key = os.getenv('OPENAI_API_KEY')
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_key = os.getenv('QDRANT_API_KEY')

    if not openai_key:
        print("❌ Error: OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='sk-proj-...'")
        sys.exit(1)

    if not qdrant_url or not qdrant_key:
        print("❌ Error: QDRANT_URL or QDRANT_API_KEY not set")
        print("Set them with:")
        print("  export QDRANT_URL='https://xxxxx.qdrant.io'")
        print("  export QDRANT_API_KEY='xxxxx'")
        sys.exit(1)

    return openai_key, qdrant_url, qdrant_key


def load_normativas_index() -> List[Dict]:
    """Load normativas index from JSON file"""
    # Try multiple possible locations
    possible_paths = [
        Path('normativas_index_minimal.json'),  # Current directory
        Path('boletines/normativas_index_minimal.json'),  # Subdirectory
        Path('../python-cli/normativas_index_minimal.json'),  # Parent directory
    ]
    
    index_path = None
    for path in possible_paths:
        if path.exists():
            index_path = path
            break
    
    if not index_path:
        print(f"❌ Error: normativas_index_minimal.json not found")
        print(f"Searched in:")
        for path in possible_paths:
            print(f"  - {path.absolute()}")
        print("\nGenerate it with:")
        print("  python3 normativas_extractor.py")
        sys.exit(1)

    print(f"📥 Loading normativas index from {index_path}...")
    with open(index_path, 'r', encoding='utf-8') as f:
        normativas = json.load(f)

    print(f"✅ Loaded {len(normativas):,} normativas")
    return normativas


# ============================================================================
# QDRANT SETUP
# ============================================================================

def setup_qdrant_collection(client: QdrantClient, force: bool = False):
    """Create or recreate Qdrant collection"""
    print(f"\n🗄️ Setting up Qdrant collection '{COLLECTION_NAME}'...")

    # Check if collection exists
    try:
        existing = client.get_collection(COLLECTION_NAME)
        print(f"⚠️ Collection already exists with {existing.points_count:,} points")
        
        if not force:
            response = input("Do you want to DELETE and recreate it? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Aborted. Use existing collection or delete it manually.")
                sys.exit(1)
        else:
            print("🗑️ Force mode: Deleting existing collection...")

        print("🗑️ Deleting existing collection...")
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # Collection doesn't exist, that's fine

    # Create collection
    print(f"📦 Creating collection with {VECTOR_SIZE} dimensions...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )
    print("✅ Collection created")


# ============================================================================
# EMBEDDING GENERATION
# ============================================================================

def generate_embeddings_batch(
    client: openai.OpenAI,
    texts: List[str]
) -> List[List[float]]:
    """Generate embeddings for a batch of texts"""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            encoding_format='float'
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"\n❌ Error generating embeddings: {e}")
        raise


def process_normativas(
    openai_client: openai.OpenAI,
    qdrant_client: QdrantClient,
    normativas: List[Dict]
):
    """Process all normativas: generate embeddings and upload to Qdrant"""
    print(f"\n🚀 Processing {len(normativas):,} normativas in batches of {BATCH_SIZE}...")
    print(f"⏱️ Estimated time: ~{len(normativas) // BATCH_SIZE // 2} minutes")
    print(f"💰 Estimated cost: ~${len(normativas) * 500 * 0.02 / 1_000_000:.2f}")

    total_batches = (len(normativas) + BATCH_SIZE - 1) // BATCH_SIZE
    successful = 0
    failed = 0

    with tqdm(total=len(normativas), desc="Generating embeddings") as pbar:
        for i in range(0, len(normativas), BATCH_SIZE):
            batch = normativas[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1

            try:
                # 1. Prepare texts for embedding
                texts = []
                for n in batch:
                    # Combine title, municipality, type, and number for better semantic search
                    text = f"{n['ti']} {n['m']} {n['t']} {n['n']}"
                    texts.append(text)

                # 2. Generate embeddings
                embeddings = generate_embeddings_batch(openai_client, texts)

                # 3. Prepare points for Qdrant
                points = []
                for j, n in enumerate(batch):
                    points.append(PointStruct(
                        id=generate_uuid_from_id(n['id']),  # Convert to UUID
                        vector=embeddings[j],
                        payload={
                            'id': n['id'],  # Keep original ID in payload for reference
                            'municipality': n['m'],
                            'type': n['t'],
                            'number': n['n'],
                            'year': n['y'],
                            'title': n['ti'],
                            'url': n['url'],
                            'source_bulletin': n['sb'],
                        }
                    ))

                # 4. Upload to Qdrant
                qdrant_client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )

                successful += len(batch)
                pbar.update(len(batch))

                # Rate limiting: small delay between batches
                if batch_num < total_batches:
                    time.sleep(0.5)

            except Exception as e:
                print(f"\n❌ Error processing batch {batch_num}: {e}")
                failed += len(batch)
                pbar.update(len(batch))
                
                # Continue with next batch
                continue

    print(f"\n✅ Processing complete!")
    print(f"   Successful: {successful:,}")
    print(f"   Failed: {failed:,}")

    return successful, failed


# ============================================================================
# VERIFICATION
# ============================================================================

def verify_collection(client: QdrantClient):
    """Verify that collection was created correctly"""
    print(f"\n🔍 Verifying collection...")

    try:
        info = client.get_collection(COLLECTION_NAME)
        print(f"✅ Collection info:")
        print(f"   Points: {info.points_count:,}")
        # Use indexed_vectors_count instead of vectors_count (API change)
        vectors = getattr(info, 'indexed_vectors_count', info.points_count)
        print(f"   Vectors: {vectors:,}")
        print(f"   Status: {info.status}")

        # Test search
        print(f"\n🧪 Testing search with query 'ordenanza municipal'...")
        test_embedding = [0.1] * VECTOR_SIZE  # Dummy vector for testing
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=test_embedding,
            limit=3
        )
        print(f"✅ Search works! Found {len(results)} results")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("OpenAI Embeddings Generator for Qdrant")
    print("=" * 70)

    # 1. Load environment
    openai_key, qdrant_url, qdrant_key = load_environment()

    # 2. Initialize clients
    print("\n🔌 Initializing clients...")
    openai_client = openai.OpenAI(api_key=openai_key)
    qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
    print("✅ Clients initialized")

    # 3. Load normativas
    normativas = load_normativas_index()

    # 4. Setup Qdrant collection
    setup_qdrant_collection(qdrant_client)

    # 5. Process normativas
    successful, failed = process_normativas(
        openai_client,
        qdrant_client,
        normativas
    )

    # 6. Verify
    if successful > 0:
        verify_collection(qdrant_client)

    # 7. Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total normativas: {len(normativas):,}")
    print(f"Successfully processed: {successful:,}")
    print(f"Failed: {failed:,}")
    print(f"Success rate: {successful / len(normativas) * 100:.1f}%")
    print("\n✅ Done! Vector search is now available.")
    print("\nNext steps:")
    print("1. Add QDRANT_URL and QDRANT_API_KEY to chatbot/.env")
    print("2. Deploy chatbot with vector search enabled")
    print("3. Test with query: 'sueldos de carlos tejedor 2025'")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

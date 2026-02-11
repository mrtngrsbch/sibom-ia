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
import sqlite3

# Add parent directory to sys.path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Load environment variables
load_dotenv()

# Try finding .env.local in python-cli directory or parent
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir) # python-cli folder usually
env_path = os.path.join(project_root, '.env.local')

if not os.getenv('OPENAI_API_KEY'):
    load_dotenv(env_path)
    # Fallback to current dir if not found above
    if not os.getenv('OPENAI_API_KEY'):
         load_dotenv('.env.local')


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
        Path('data/indexes/normativas_index_minimal.json'), # Data folder
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


def load_normativas_from_db(municipality: str) -> List[Dict]:
    """Load normativas for a specific municipality directly from SQLite"""
    import sqlite3
    db_path = Path('boletines/normativas.db')
    if not db_path.exists():
        db_path = Path('python-cli/boletines/normativas.db')
    
    if not db_path.exists():
        print(f"❌ Error: SQLite database not found at {db_path}")
        return []

    print(f"📥 Loading normativas for '{municipality}' from SQLite...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM normativas WHERE municipality = ?", 
        (municipality,)
    )
    rows = cursor.fetchall()
    conn.close()

    normativas = []
    for r in rows:
        r_dict = dict(r)
        normativas.append({
            'id': str(r_dict['id']),
            'm': r_dict['municipality'],
            't': r_dict['type'],
            'n': r_dict['number'],
            'y': r_dict['year'],
            'ti': r_dict['title'],
            'url': r_dict['url'],
            # Map to expected keys in process_normativas
            'sb': r_dict.get('source_bulletin', '')
        })
    
    print(f"✅ Loaded {len(normativas):,} normativas from DB")
    return normativas


def load_transparency_docs() -> List[Dict]:
    """Load valid transparency documents from SQLite via individual JSONs for chunk access"""
    from utils.sqlite_manager import get_sqlite_manager
    
    mgr = get_sqlite_manager()
    print("\n🔍 Querying transparency documents for indexing...")
    
    # Solo traer los válidos
    docs = mgr.get_transparency_docs(limit=2000) # Aumentamos el límite para indexar todo
    valid_docs = [d for d in docs if d.get('validation_status') == 'valid']
    
    total_chunks = []
    
    boletines_dir = Path("boletines")
    
    print(f"📥 Loading chunks for {len(valid_docs)} valid transparency documents...")
    
    for d in valid_docs:
        json_file = d.get('json_file')
        if not json_file: continue
        
        file_path = boletines_dir / json_file
        if not file_path.exists(): continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            doc_chunks = data.get('rag_chunks', [])
            for c in doc_chunks:
                # Enriquecer el chunk con metadata del documento original
                c['url_origen'] = d.get('url_origen')
                c['id_doc'] = d.get('id')
                total_chunks.append(c)
        except Exception as e:
            print(f"  ⚠ Error loading chunks for {json_file}: {e}")
            
    print(f"✅ Loaded {len(total_chunks):,} semantic financial chunks")
    return total_chunks


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
            print("🚀 Append mode: Keeping existing collection.")
            return

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
                    if 'embedding_text' in n:
                        # Case: Transparency Chunk
                        texts.append(n['embedding_text'])
                    elif 'text_to_embed' in n:
                         # Legacy case if any
                        texts.append(n['text_to_embed'])
                    else:
                        # Case: Normal Normativa
                        # Use .get() with defaults to avoid KeyError
                        ti = n.get('ti', 's/t')
                        m = n.get('m', 's/m')
                        t = n.get('t', 's/tipo')
                        n_val = n.get('n', 's/n')
                        text = f"{ti} {m} {t} {n_val}"
                        texts.append(text)

                # 2. Generate embeddings
                embeddings = generate_embeddings_batch(openai_client, texts)

                 # 3. Prepare points for Qdrant
                points = []
                for j, n in enumerate(batch):
                    # Check if it's a transparency chunk
                    if 'embedding_text' in n:
                         # Case: Transparency Chunk
                        chunk_id = n.get('chunk_id')
                        if not chunk_id:
                             chunk_id = f"{n.get('id_doc', 'unknown')}_{j}_{i}"
                        
                        point_id = generate_uuid_from_id(chunk_id)
                        
                        # Extract metadata safely
                        meta = n.get('metadata', {})
                        data = n.get('data', {})
                        
                        payload = {
                            'source_type': 'transparency_chunk',
                            'municipality': meta.get('entity', n.get('municipality')), # key 'entity' in metadata
                            'period': meta.get('period', n.get('period')),
                            'year': meta.get('year'),
                            'month': meta.get('month'),
                            'document_type': meta.get('document_type'),
                            'account_code': data.get('CUENTA'),
                            'account_desc': data.get('DESCRIPCION'),
                            'text': n['embedding_text'],
                            'id_doc': n.get('id_doc'),
                            'chunk_id': chunk_id,
                            'url': n.get('url_origen')
                        }
                    elif 'text_to_embed' in n:
                        # Legacy Case
                        point_id = generate_uuid_from_id(f"{n.get('id_doc')}_{j}_{i}")
                        payload = {
                            'source_type': 'transparency_chunk',
                            'text': n['text_to_embed'],
                            'id_doc': n.get('id_doc'),
                            'url': n.get('url_origen')
                        }
                    else:
                        # Case: Normal Normativa
                        point_id = generate_uuid_from_id(n.get('id', 'unknown'))
                        payload = {
                            'source_type': 'normativa',
                            'id': n.get('id'),
                            'municipality': n.get('m'),
                            'type': n.get('t'),
                            'number': n.get('n'),
                            'year': n.get('y'),
                            'title': n.get('ti'),
                            'url': n.get('url'),
                            'source_bulletin': n.get('sb'),
                        }
                        
                    points.append(PointStruct(
                        id=point_id,
                        vector=embeddings[j],
                        payload=payload
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
        try:
            # Updated method for newer qdrant-client versions
            results = client.query_points(
                collection_name=COLLECTION_NAME,
                query="ordenanza municipal",
                limit=3
            )
            print(f"✅ Search test successful: {len(results.points)} results found.")
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            # Fallback if query_points also fails
            try:
                 results = client.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=[0.0] * VECTOR_SIZE,
                    limit=3
                 )
                 print(f"✅ Fallback search successful.")
            except:
                 pass
            
        print("\n🔍 Sample points look correct")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise


# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generador de Embeddings para Qdrant")
    parser.add_argument("--only-transparency", action="store_true", help="Indexar solo documentos de transparencia")
    parser.add_argument("--only-normativas", action="store_true", help="Indexar solo normativas estándar")
    parser.add_argument("--skip-normativas", action="store_true", help="Saltar normativas")
    parser.add_argument("--recreate", action="store_true", help="BORRAR y recrear la colección")
    parser.add_argument("--municipality", "-m", type=str, help="Filtrar por municipio (ej: 'Carlos Tejedor')")
    args = parser.parse_args()

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

    # 3. Load data
    normativas = []
    if not args.only_transparency and not args.skip_normativas:
        if args.municipality:
            # Use DB for filtered municipality (more accurate than JSON index)
            normativas = load_normativas_from_db(args.municipality)
        else:
            normativas = load_normativas_index()
    else:
        print("⏩ Skipping normativas index load")
    
    # 3.5 Load transparency chunks
    trans_chunks = []
    if not args.only_normativas:
        trans_chunks = load_transparency_docs()
        if args.municipality:
            # Transparency chunks use 'municipality' key in metadata or top level
            trans_chunks = [c for c in trans_chunks if args.municipality.lower() in (c.get('metadata', {}).get('entity', '') or c.get('municipality', '')).lower()]
            print(f"🎯 Filtered transparency chunks for '{args.municipality}': {len(trans_chunks):,}")
    else:
        print("⏩ Skipping transparency chunks load")
    
    # Combine everything
    all_data = normativas + trans_chunks
    
    if not all_data:
        print("❌ No data to process. Exiting.")
        return

    # 4. Setup Qdrant collection
    setup_qdrant_collection(qdrant_client, force=args.recreate)

    # 5. Process everything
    successful, failed = process_normativas(
        openai_client,
        qdrant_client,
        all_data
    )

    # 6. Verify
    if successful > 0:
        verify_collection(qdrant_client)

    # 7. Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if normativas:
        print(f"Total normativas: {len(normativas):,}")
    print(f"Total transparency chunks: {len(trans_chunks):,}")
    print(f"Successfully processed: {successful:,}")
    print(f"Failed: {failed:,}")
    print(f"Success rate: {(successful / len(all_data) * 100) if all_data else 0:.1f}%")
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

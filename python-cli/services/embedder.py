"""
OpenAI Embeddings Service para RAG

Genera embeddings usando OpenAI text-embedding-3-small para indexación en Qdrant.

Características:
- Batch processing (100 chunks por request)
- Rate limiting respetando límites de OpenAI (3000 RPM)
- Progress tracking para migraciones largas
- Error handling con retries automáticos
- Costo estimado: $0.02 por 1M tokens (~$0.40 para 50K docs)

Usage:
    from services.embedder import OpenAIEmbedder
    
    embedder = OpenAIEmbedder()
    chunks = [DocumentChunk(...), ...]
    embeddings = embedder.embed_chunks(chunks, batch_size=100)
"""

import os
import time
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("openai package not installed. Run: pip install openai")


logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Resultado de embedding con metadata."""
    embedding: List[float]
    chunk_id: str
    token_count: int
    model: str


class OpenAIEmbedder:
    """
    Servicio para generar embeddings usando OpenAI API.

    Modelo por defecto: text-embedding-3-small
    - Dimensiones: 1536
    - Costo: $0.02 / 1M tokens
    - Rate limit: 3,000 RPM
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small"
    ):
        """
        Args:
            api_key: OpenAI API key (si None, lee desde OPENAI_API_KEY env var)
            model: Modelo de embeddings (default: text-embedding-3-small)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.total_tokens_used = 0

        logger.info(f"Initialized OpenAIEmbedder with model: {model}")

    def embed_text(self, text: str) -> List[float]:
        """
        Genera embedding para un texto individual.

        Args:
            text: Texto a embedear

        Returns:
            Vector de 1536 dimensiones
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )

            self.total_tokens_used += response.usage.total_tokens

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def embed_chunks(
        self,
        chunks: List,  # List[DocumentChunk] pero evitamos import circular
        batch_size: int = 100,
        show_progress: bool = True,
        max_retries: int = 3
    ) -> List[EmbeddingResult]:
        """
        Genera embeddings para múltiples chunks con batching y rate limiting.

        Args:
            chunks: Lista de DocumentChunk objects
            batch_size: Chunks por batch (max 100 para respetar límites API)
            show_progress: Mostrar progreso en consola
            max_retries: Intentos máximos por batch en caso de error

        Returns:
            Lista de EmbeddingResult con embeddings y metadata
        """
        if not chunks:
            logger.warning("No chunks provided for embedding")
            return []

        if batch_size > 100:
            logger.warning(
                f"Batch size {batch_size} exceeds recommended max (100). Setting to 100.")
            batch_size = 100

        results: List[EmbeddingResult] = []
        total_chunks = len(chunks)
        failed_chunks = []

        if show_progress:
            print(f"\n🔄 Generando embeddings para {total_chunks} chunks...")
            print(f"   Modelo: {self.model}")
            print(f"   Batch size: {batch_size}")
            print(
                f"   Batches totales: {(total_chunks + batch_size - 1) // batch_size}\n")

        # Procesar en batches
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size

            # Extraer textos del batch
            texts = [chunk.chunk_text for chunk in batch]

            # Reintentos en caso de error
            retry_count = 0
            batch_success = False

            while retry_count < max_retries and not batch_success:
                try:
                    # Llamada a OpenAI API
                    response = self.client.embeddings.create(
                        input=texts,
                        model=self.model
                    )

                    # Procesar respuesta
                    for j, (chunk, embedding_data) in enumerate(zip(batch, response.data)):
                        results.append(EmbeddingResult(
                            embedding=embedding_data.embedding,
                            chunk_id=chunk.chunk_id,
                            # Aproximación
                            token_count=response.usage.total_tokens // len(
                                batch),
                            model=self.model
                        ))

                    self.total_tokens_used += response.usage.total_tokens
                    batch_success = True

                    if show_progress:
                        percentage = (i + len(batch)) / total_chunks * 100
                        print(f"   ✓ Batch {batch_num}/{total_batches} completado "
                              f"({len(batch)} chunks) | {percentage:.1f}% | "
                              f"Tokens usados: {self.total_tokens_used:,}")

                    # Rate limiting: ~20 batches/min = 3000 RPM con batch_size=100
                    # Sleep 0.5s entre batches para evitar rate limits
                    if i + batch_size < total_chunks:
                        time.sleep(0.5)

                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count  # Exponential backoff
                        logger.warning(
                            f"Error en batch {batch_num} (intento {retry_count}/{max_retries}): {e}. "
                            f"Reintentando en {wait_time}s..."
                        )
                        if show_progress:
                            print(
                                f"   ⚠️  Error en batch {batch_num}, reintentando en {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"Batch {batch_num} falló después de {max_retries} intentos: {e}")
                        if show_progress:
                            print(
                                f"   ❌ Batch {batch_num} falló después de {max_retries} intentos")
                        failed_chunks.extend(
                            [chunk.chunk_id for chunk in batch])

        # Resumen final
        if show_progress:
            cost_estimate = (self.total_tokens_used / 1_000_000) * 0.02
            print(f"\n✅ Embeddings completados:")
            print(f"   Total chunks: {len(results)}/{total_chunks}")
            print(f"   Tokens usados: {self.total_tokens_used:,}")
            print(f"   Costo estimado: ${cost_estimate:.4f}")
            if failed_chunks:
                print(f"   ⚠️  Chunks fallidos: {len(failed_chunks)}")

        return results

    def estimate_cost(self, num_tokens: int) -> float:
        """
        Estima el costo de embeddings para un número de tokens.

        Args:
            num_tokens: Número de tokens a procesar

        Returns:
            Costo estimado en USD
        """
        return (num_tokens / 1_000_000) * 0.02

    def reset_token_counter(self):
        """Reinicia el contador de tokens usados."""
        self.total_tokens_used = 0


# Convenience function
def create_embedder(model: str = "text-embedding-3-small") -> OpenAIEmbedder:
    """
    Crea instancia de embedder con configuración por defecto.

    Args:
        model: Modelo de OpenAI (default: text-embedding-3-small)

    Returns:
        OpenAIEmbedder configurado
    """
    return OpenAIEmbedder(model=model)


if __name__ == "__main__":
    # Test básico
    import sys
    from dotenv import load_dotenv

    # Cargar .env desde raíz del proyecto
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)

    logging.basicConfig(level=logging.INFO)

    print("🧪 Test de OpenAI Embedder\n")

    try:
        embedder = create_embedder()

        # Test texto individual
        test_text = "Balance de Tesorería - Carlos Tejedor 2024-T1. Total de Recursos: $9.362.683.953,23"
        print(f"Generando embedding para texto de prueba...")
        print(f"Texto: {test_text[:100]}...\n")

        embedding = embedder.embed_text(test_text)

        print(f"✅ Embedding generado exitosamente")
        print(f"   Dimensiones: {len(embedding)}")
        print(f"   Primeros 5 valores: {embedding[:5]}")
        print(f"   Tokens usados: {embedder.total_tokens_used}")
        print(
            f"   Costo: ${embedder.estimate_cost(embedder.total_tokens_used):.6f}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

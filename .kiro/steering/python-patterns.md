---
inclusion: fileMatch
fileMatchPattern: '**/*.py'
---

# Python Engineering Patterns - SIBOM Scraper

## Code Architecture Principles

### 1. Class-Based Design Pattern

**Observed Pattern:** `python-cli/sibom_scraper.py:25-40`
```python
class SibomScraper:
    def __init__(self, base_url: str, output_dir: str, openrouter_api_key: str):
        self.openrouter_client = OpenAI(...)
        self.rate_limit_delay = 3
        self.max_retries = 3
```

**Engineering Standards:**
- **Single Responsibility:** Each class handles one domain (scraping, LLM processing, file I/O)
- **Dependency Injection:** External dependencies passed via constructor
- **Configuration Encapsulation:** All configurable parameters as instance variables
- **Immutable Configuration:** Set once in `__init__`, never modified

### 2. Error Handling Strategy

**Pattern:** Defensive Programming with Graceful Degradation
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def _make_llm_request(self, prompt: str) -> str:
    try:
        response = self.openrouter_client.chat.completions.create(...)
        return response.choices[0].message.content
    except Exception as e:
        if "429" in str(e):  # Rate limit
            time.sleep(30)
        raise e
```

**Critical Requirements:**
- **Exponential Backoff:** Use `tenacity` library for retry logic
- **Specific Exception Handling:** Catch rate limits (429) separately from general errors
- **Logging Before Retry:** Always log the error before retrying
- **Circuit Breaker Pattern:** Fail fast after max retries to prevent cascade failures

### 3. LLM Integration Patterns

**Prompt Engineering Standards:**
```python
def extract_bulletin_list(self) -> List[Dict[str, str]]:
    prompt = f"""
    Eres un experto en extracción de datos de sitios web gubernamentales argentinos.
    
    TAREA: Extraer TODOS los boletines oficiales municipales de esta página HTML.
    
    FORMATO DE SALIDA REQUERIDO:
    {{
      "bulletins": [...]
    }}
    
    REGLAS CRÍTICAS:
    1. Formato de fecha: DD/MM/YYYY exacto
    2. Links relativos que comiencen con /
    3. NO inventar datos - solo extraer lo que está visible
    
    HTML DE LA PÁGINA:
    {html_content[:8000]}
    """
```

**Engineering Principles:**
- **Structured Prompts:** Always include role, task, format, rules, and data
- **Token Management:** Truncate input to prevent context overflow (`[:8000]`)
- **JSON Schema Enforcement:** Use `response_format={"type": "json_object"}`
- **Deterministic Output:** Set `temperature=0.1` for data extraction tasks
- **Validation Layer:** Always validate LLM output before processing

### 4. Data Processing Pipeline

**Stream Processing Pattern:**
```python
def process_bulletins_parallel(self, bulletins: List[Dict], max_workers: int = 3):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(self._process_single_bulletin, bulletin) 
            for bulletin in bulletins
        ]
        
        for future in as_completed(futures):
            try:
                result = future.result()
                yield result
            except Exception as e:
                self.logger.error(f"Bulletin processing failed: {e}")
                continue
```

**Performance Requirements:**
- **Bounded Parallelism:** Never exceed `max_workers=3` to respect rate limits
- **Graceful Failure:** Individual failures don't stop the entire pipeline
- **Memory Efficiency:** Use generators (`yield`) for large datasets
- **Progress Tracking:** Integrate with `rich.progress` for user feedback

### 5. File I/O and Serialization

**Atomic Write Pattern:**
```python
def save_json_atomic(self, data: Any, filepath: str) -> None:
    """Atomic write to prevent corruption during interruption"""
    temp_path = f"{filepath}.tmp"
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Atomic move - prevents partial writes
        os.rename(temp_path, filepath)
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e
```

**Data Integrity Standards:**
- **Atomic Operations:** Use temp files + rename for atomic writes
- **UTF-8 Encoding:** Always specify encoding explicitly
- **JSON Formatting:** Use `ensure_ascii=False, indent=2` for readability
- **Cleanup on Failure:** Remove temp files if operation fails

### 6. Logging and Observability

**Structured Logging Pattern:**
```python
import structlog

logger = structlog.get_logger()

def extract_full_text(self, document_url: str) -> str:
    logger.info(
        "Starting document extraction",
        url=document_url,
        municipality=self.municipality_name,
        timestamp=datetime.utcnow().isoformat()
    )
    
    try:
        result = self._make_llm_request(prompt)
        
        logger.info(
            "Document extraction completed",
            url=document_url,
            content_length=len(result),
            processing_time=time.time() - start_time
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Document extraction failed",
            url=document_url,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

**Observability Requirements:**
- **Structured Logs:** Use `structlog` for machine-readable logs
- **Correlation IDs:** Include municipality and timestamp for tracing
- **Performance Metrics:** Log processing times for optimization
- **Error Context:** Include full error context for debugging

### 7. Configuration Management

**Environment-Based Configuration:**
```python
from dataclasses import dataclass
from typing import Optional
import os

@dataclass(frozen=True)
class ScraperConfig:
    openrouter_api_key: str
    base_url: str
    output_dir: str = "boletines"
    rate_limit_delay: int = 3
    max_retries: int = 3
    parallel_workers: int = 3
    model_name: str = "google/gemini-3-flash-preview"
    
    @classmethod
    def from_env(cls) -> 'ScraperConfig':
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            base_url=os.getenv("BASE_URL", ""),
            rate_limit_delay=int(os.getenv("RATE_LIMIT_DELAY", "3")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            parallel_workers=int(os.getenv("PARALLEL_WORKERS", "3"))
        )
```

**Configuration Standards:**
- **Immutable Config:** Use `@dataclass(frozen=True)` to prevent modification
- **Type Safety:** Explicit type hints for all configuration parameters
- **Environment Variables:** Support env var overrides for all settings
- **Validation:** Validate required fields at startup, fail fast if missing
- **Defaults:** Provide sensible defaults for optional parameters

### 8. Testing Patterns

**Property-Based Testing for Data Extraction:**
```python
from hypothesis import given, strategies as st
import pytest

class TestSibomScraper:
    
    @given(st.text(min_size=1, max_size=1000))
    def test_json_extraction_robustness(self, malformed_input: str):
        """Property: JSON extraction should handle any malformed input gracefully"""
        scraper = SibomScraper(...)
        
        # Should not raise exception, should return empty dict or valid JSON
        result = scraper._extract_json(malformed_input)
        
        # Property: Result is always valid JSON or empty
        if result:
            assert json.loads(result)  # Should not raise JSONDecodeError
    
    def test_rate_limiting_respected(self, mocker):
        """Integration test: Verify rate limiting is enforced"""
        mock_client = mocker.patch('openai.OpenAI')
        scraper = SibomScraper(rate_limit_delay=1, ...)
        
        start_time = time.time()
        scraper._make_llm_request("test")
        scraper._make_llm_request("test")
        elapsed = time.time() - start_time
        
        # Property: Minimum delay between requests is enforced
        assert elapsed >= 1.0
```

**Testing Requirements:**
- **Property-Based Tests:** Use `hypothesis` for robustness testing
- **Integration Tests:** Test rate limiting and external API behavior
- **Mock External Dependencies:** Never hit real APIs in tests
- **Performance Tests:** Verify timing constraints are met

### 9. Memory Management

**Large Dataset Processing:**
```python
def process_large_municipality(self, municipality_url: str) -> Iterator[Dict]:
    """Generator pattern for memory-efficient processing of large datasets"""
    
    bulletins = self.extract_bulletin_list(municipality_url)
    
    # Process in chunks to prevent memory exhaustion
    chunk_size = 10
    for i in range(0, len(bulletins), chunk_size):
        chunk = bulletins[i:i + chunk_size]
        
        # Process chunk and yield results immediately
        for bulletin in chunk:
            try:
                result = self._process_single_bulletin(bulletin)
                yield result
                
                # Explicit cleanup to prevent memory leaks
                del result
                
            except Exception as e:
                self.logger.error(f"Failed to process bulletin {bulletin.get('number', 'unknown')}: {e}")
                continue
        
        # Force garbage collection between chunks
        import gc
        gc.collect()
```

**Memory Efficiency Standards:**
- **Generator Pattern:** Use generators for large datasets to prevent memory exhaustion
- **Chunked Processing:** Process data in fixed-size chunks
- **Explicit Cleanup:** Delete large objects when done processing
- **Garbage Collection:** Force GC between chunks for long-running processes

### 10. Security Considerations

**Input Sanitization:**
```python
import html
import re
from urllib.parse import urlparse

def sanitize_html_input(self, html_content: str) -> str:
    """Sanitize HTML input before sending to LLM"""
    
    # Remove potentially malicious scripts
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Escape HTML entities
    html_content = html.escape(html_content)
    
    # Limit size to prevent DoS
    max_size = 50000  # 50KB limit
    if len(html_content) > max_size:
        html_content = html_content[:max_size] + "... [truncated]"
    
    return html_content

def validate_url(self, url: str) -> bool:
    """Validate URL to prevent SSRF attacks"""
    try:
        parsed = urlparse(url)
        
        # Only allow HTTPS for external requests
        if parsed.scheme not in ['https']:
            return False
            
        # Whitelist allowed domains
        allowed_domains = ['sibom.slyt.gba.gob.ar']
        if parsed.netloc not in allowed_domains:
            return False
            
        return True
        
    except Exception:
        return False
```

**Security Requirements:**
- **Input Validation:** Sanitize all external input before processing
- **URL Validation:** Whitelist allowed domains to prevent SSRF
- **Size Limits:** Enforce maximum input sizes to prevent DoS
- **No Code Execution:** Never use `eval()` or `exec()` on external input
- **Secrets Management:** Never log API keys or sensitive data

---

## Implementation Checklist

When implementing new Python modules in this project:

- [ ] Use class-based design with dependency injection
- [ ] Implement retry logic with exponential backoff
- [ ] Add structured logging with correlation IDs
- [ ] Use atomic file operations for data persistence
- [ ] Implement proper error handling and graceful degradation
- [ ] Add property-based tests for robustness
- [ ] Use generators for memory-efficient processing
- [ ] Validate and sanitize all external inputs
- [ ] Respect rate limits and implement circuit breakers
- [ ] Use immutable configuration objects
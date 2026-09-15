from google import genai

from backend.app.core.config import settings


EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 1536


client = genai.Client(
    api_key=settings.gemini_api_key,
)


# In-memory embedding cache.
# Key: normalized text
# Value: generated embedding
_embedding_cache: dict[str, list[float]] = {}


def _normalize_cache_key(text: str) -> str:
    return " ".join(text.strip().lower().split())


def generate_embedding(text: str) -> list[float]:
    """
    Generate a semantic embedding for the supplied text.

    Reuses an in-memory cached embedding when the same
    text has already been embedded.
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    cleaned_text = text.strip()
    cache_key = _normalize_cache_key(cleaned_text)

    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=cleaned_text,
        config={
            "output_dimensionality": EMBEDDING_DIMENSION,
        },
    )

    if not response.embeddings:
        raise RuntimeError("Gemini returned no embedding")

    embedding = response.embeddings[0].values

    if embedding is None:
        raise RuntimeError("Gemini returned an empty embedding")

    if len(embedding) != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Expected embedding dimension "
            f"{EMBEDDING_DIMENSION}, got {len(embedding)}"
        )

    embedding_list = list(embedding)

    _embedding_cache[cache_key] = embedding_list

    return embedding_list


def generate_embeddings(
    texts: list[str],
) -> list[list[float]]:
    """
    Generate semantic embeddings for multiple texts.

    Uses the cache for texts that have already been embedded
    and sends only uncached texts to Gemini.
    """

    if not texts:
        raise ValueError("Texts cannot be empty")

    cleaned_texts = [
        text.strip()
        for text in texts
    ]

    if any(not text for text in cleaned_texts):
        raise ValueError("Texts cannot contain empty values")

    results: list[list[float] | None] = [
        None
        for _ in cleaned_texts
    ]

    uncached_texts: list[str] = []
    uncached_indices: list[int] = []

    for index, text in enumerate(cleaned_texts):
        cache_key = _normalize_cache_key(text)

        if cache_key in _embedding_cache:
            results[index] = _embedding_cache[cache_key]
        else:
            uncached_texts.append(text)
            uncached_indices.append(index)

    # Nothing new needs to be sent to Gemini.
    if uncached_texts:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=uncached_texts,
            config={
                "output_dimensionality": EMBEDDING_DIMENSION,
            },
        )

        if not response.embeddings:
            raise RuntimeError(
                "Gemini returned no embeddings"
            )

        if len(response.embeddings) != len(uncached_texts):
            raise RuntimeError(
                "Gemini returned an unexpected number "
                "of embeddings"
            )

        for index, embedding_response in zip(
            uncached_indices,
            response.embeddings,
        ):
            embedding = embedding_response.values

            if embedding is None:
                raise RuntimeError(
                    "Gemini returned an empty embedding"
                )

            if len(embedding) != EMBEDDING_DIMENSION:
                raise RuntimeError(
                    f"Expected embedding dimension "
                    f"{EMBEDDING_DIMENSION}, "
                    f"got {len(embedding)}"
                )

            embedding_list = list(embedding)

            cache_key = _normalize_cache_key(
                cleaned_texts[index]
            )

            _embedding_cache[cache_key] = embedding_list
            results[index] = embedding_list

    return [
        embedding
        for embedding in results
        if embedding is not None
    ]
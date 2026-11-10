import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .runtime import digest


def chunks_for(url: str, text: str, size=900, overlap=100):
    normalized = re.sub(r"\s+", " ", text).strip()
    return [
        {
            "id": digest([url, start, normalized[start : start + size]])[:24],
            "url": url,
            "text": normalized[start : start + size],
        }
        for start in range(0, len(normalized), size - overlap)
        if normalized[start : start + size].strip()
    ]


def rank_chunks(chunks: list[dict], query: str, limit=5) -> list[dict]:
    words = set(re.findall(r"\b\w{3,}\b", query.casefold())) - {
        "the",
        "what",
        "how",
        "does",
        "for",
        "are",
        "can",
        "which",
        "with",
        "from",
        "that",
        "this",
    }
    if not chunks or not words:
        return []
    vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform([chunk["text"] for chunk in chunks])
    except ValueError:
        return []
    scores = cosine_similarity(
        vectorizer.transform([" ".join(sorted(words))]), matrix
    ).ravel()
    ranked = [
        {**chunk, "score": float(score)}
        for chunk, score in zip(chunks, scores)
        if score > 0.05
        and words.intersection(re.findall(r"\w+", chunk["text"].casefold()))
    ]
    return sorted(ranked, key=lambda chunk: (-chunk["score"], chunk["id"]))[:limit]

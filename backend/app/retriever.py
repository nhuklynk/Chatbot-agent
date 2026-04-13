from dataclasses import dataclass
import re
import unicodedata

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: str


class InMemoryKnowledgeBase:
    def __init__(self):
        self.docs: list[str] = []
        self.sources: list[str] = []
        self._vectorizer = TfidfVectorizer(
            stop_words=None,
            preprocessor=self._normalize_for_search,
            ngram_range=(1, 2),
        )
        self._matrix = None

    @staticmethod
    def _normalize_for_search(text: str) -> str:
        lowered = (text or "").lower()
        decomposed = unicodedata.normalize("NFKD", lowered)
        without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
        normalized = re.sub(r"[^a-z0-9\s]", " ", without_accents)
        return re.sub(r"\s+", " ", normalized).strip()

    def add_chunks(self, chunks: list[str], source: str) -> None:
        for chunk in chunks:
            self.docs.append(chunk)
            self.sources.append(source)
        self._rebuild_matrix()

    def _rebuild_matrix(self) -> None:
        if self.docs:
            self._matrix = self._vectorizer.fit_transform(self.docs)
        else:
            self._matrix = None

    def remove_source(self, source: str) -> int:
        kept_docs: list[str] = []
        kept_sources: list[str] = []
        removed_count = 0

        for doc, src in zip(self.docs, self.sources):
            if src == source:
                removed_count += 1
                continue
            kept_docs.append(doc)
            kept_sources.append(src)

        self.docs = kept_docs
        self.sources = kept_sources
        self._rebuild_matrix()
        return removed_count

    def search(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        if not self.docs or self._matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self._matrix).flatten()
        if not np.any(sims):
            return []

        top_indexes = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_indexes:
            score = float(sims[idx])
            if score <= 0:
                continue
            results.append(
                RetrievedChunk(
                    text=self.docs[idx],
                    score=score,
                    source=self.sources[idx],
                )
            )
        return results

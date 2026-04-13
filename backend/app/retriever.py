from dataclasses import dataclass

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
        self._vectorizer = TfidfVectorizer(stop_words=None)
        self._matrix = None

    def add_chunks(self, chunks: list[str], source: str) -> None:
        for chunk in chunks:
            self.docs.append(chunk)
            self.sources.append(source)
        if self.docs:
            self._matrix = self._vectorizer.fit_transform(self.docs)

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

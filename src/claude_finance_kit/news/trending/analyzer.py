"""Trending topic analyzer using n-gram frequency counting."""

import re
from collections import Counter
from itertools import tee
from typing import Dict, List, Optional, Set


class TrendingAnalyzer:
    """Analyze trending topics from news text using n-gram phrase counting."""

    def __init__(
        self,
        stop_words_file: Optional[str] = None,
        min_token_length: int = 3,
    ) -> None:
        """
        Parameters:
            stop_words_file: Path to a stop words file (one word per line).
            min_token_length: Minimum token length to be considered.
        """
        self.min_token_length = min_token_length
        self.stop_words: Set[str] = set()
        if stop_words_file:
            self.stop_words = self._load_stop_words(stop_words_file)
        self.trends: Counter = Counter()

    def _load_stop_words(self, file_path: str) -> Set[str]:
        """Load stop words from a file, ignoring blank lines and comments."""
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                return {line.strip() for line in fh if line.strip() and not line.startswith("#")}
        except FileNotFoundError:
            print(f"Stop words file not found: {file_path}")
            return set()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize text after stripping punctuation and lowercasing."""
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return cleaned.split()

    def _generate_ngrams(self, tokens: List[str], n: int) -> List[str]:
        """Generate n-grams as space-joined strings from a token list."""
        if len(tokens) < n:
            return []
        iterables = tee(tokens, n)
        for i, it in enumerate(iterables):
            for _ in range(i):
                next(it, None)
        return [" ".join(gram) for gram in zip(*iterables)]

    def update_trends(
        self,
        text: str,
        ngram_range: Optional[List[int]] = None,
    ) -> None:
        """
        Process text and update trending topic counts.

        Parameters:
            text: Input text (e.g. title + description combined).
            ngram_range: List of n-gram sizes to generate. Defaults to [2, 3, 4, 5].
        """
        if ngram_range is None:
            ngram_range = [2, 3, 4, 5]

        tokens = self._tokenize(text)
        filtered = [
            t for t in tokens
            if len(t) >= self.min_token_length and t not in self.stop_words
        ]
        phrases: List[str] = []
        for n in ngram_range:
            phrases.extend(self._generate_ngrams(filtered, n))
        self.trends.update(phrases)

    def get_top_trends(self, top_n: int = 20) -> Dict[str, int]:
        """Return the top trending phrases and their frequencies."""
        return dict(self.trends.most_common(top_n))

    def reset_trends(self) -> None:
        """Reset the trending topics counter."""
        self.trends = Counter()

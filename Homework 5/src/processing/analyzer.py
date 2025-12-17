from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from src.config import Config
from src.core.utils import clean_text

# Stopwords unificate
CUSTOM_STOPWORDS = list(ENGLISH_STOP_WORDS.union([
    "figure", "table", "fig", "tab", "image", "plot", "graph", "shown", "show",
    "left", "right", "top", "bottom", "red", "blue", "data", "results", "using"
]))

class ContextAnalyzer:
    """Gestisce l'analisi TF-IDF per un singolo paper."""
    
    def __init__(self, paragraphs):
        self.paragraphs = [clean_text(p) for p in paragraphs]
        self.vectorizer = None
        self.tfidf_matrix = None
        self._fit()

    def _fit(self):
        if len(self.paragraphs) < 3:
            return
        try:
            self.vectorizer = TfidfVectorizer(stop_words=CUSTOM_STOPWORDS)
            self.tfidf_matrix = self.vectorizer.fit_transform(self.paragraphs)
        except ValueError:
            pass # Corpus vuoto o solo stopwords

    def find_context(self, query_text, exclude_indices=None):
        """Trova paragrafi semanticamente simili alla query (caption)."""
        if self.vectorizer is None or self.tfidf_matrix is None or not query_text.strip():
            return []

        exclude_indices = exclude_indices or set()
        context = []
        
        try:
            query_vec = self.vectorizer.transform([query_text])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            relevant_idx = np.where(similarities > Config.TFIDF_THRESHOLD)[0]

            for idx in relevant_idx:
                if idx not in exclude_indices:
                    context.append(self.paragraphs[idx])
        except:
            pass
            
        return context
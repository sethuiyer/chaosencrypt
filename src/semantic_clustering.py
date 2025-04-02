import re
from typing import List, Dict, Tuple
import math
from collections import defaultdict

class SemanticClustering:
    def __init__(self, n_gram_size: int = 2, word_weight: float = 0.7, char_weight: float = 0.3):
        """Initialize semantic clustering with weights for word and character-level similarity.
        
        Args:
            n_gram_size: Size of character n-grams for similarity calculation
            word_weight: Weight for word-level similarity (0.0 to 1.0)
            char_weight: Weight for character-level similarity (0.0 to 1.0)
        """
        self.n_gram_size = n_gram_size
        self.word_weight = word_weight
        self.char_weight = char_weight

    def encrypt(self, text: str) -> str:
        """Encrypt text while preserving semantic relationships.
        
        Args:
            text: Input text to encrypt
            
        Returns:
            Encrypted text that preserves semantic relationships
        """
        # Split into words and preserve punctuation
        words = re.findall(r'\b\w+\b|[^\w\s]', text)
        
        # Encrypt each word while preserving word boundaries
        encrypted_words = []
        for word in words:
            if re.match(r'\b\w+\b', word):  # Only encrypt actual words
                # Simple word-level hash for semantic preservation
                word_hash = sum(ord(c) * (31 ** i) for i, c in enumerate(word)) % 1000000
                encrypted_words.append(f"w{word_hash}")
            else:
                encrypted_words.append(word)  # Keep punctuation as is
        
        return ' '.join(encrypted_words)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two encrypted strings.
        
        Args:
            text1: First encrypted text
            text2: Second encrypted text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Split into words
        words1 = text1.split()
        words2 = text2.split()
        
        # Calculate word-level similarity
        word_sim = self.calculate_word_similarity(words1, words2)
        
        # Calculate character-level similarity
        char_sim = self.calculate_char_similarity(text1, text2)
        
        # Combine similarities with weights
        return (self.word_weight * word_sim + 
                self.char_weight * char_sim)

    def calculate_similarities(self, texts: List[str]) -> List[List[float]]:
        """Calculate pairwise similarities between multiple texts.
        
        Args:
            texts: List of encrypted texts
            
        Returns:
            List of lists containing similarity scores
        """
        n = len(texts)
        similarities = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                sim = self.calculate_similarity(texts[i], texts[j])
                similarities[i][j] = sim
                similarities[j][i] = sim  # Symmetric matrix
            similarities[i][i] = 1.0  # Self-similarity is 1.0
        
        return similarities

    def calculate_word_similarity(self, words1: List[str], words2: List[str]) -> float:
        """Calculate similarity between two lists of encrypted words.
        
        Args:
            words1: First list of encrypted words
            words2: Second list of encrypted words
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Create word frequency dictionaries
        freq1 = defaultdict(int)
        freq2 = defaultdict(int)
        
        for word in words1:
            if word.startswith('w'):  # Only consider encrypted words
                freq1[word] += 1
        for word in words2:
            if word.startswith('w'):
                freq2[word] += 1
        
        # Calculate Jaccard similarity
        common_words = set(freq1.keys()) & set(freq2.keys())
        total_words = set(freq1.keys()) | set(freq2.keys())
        
        if not total_words:
            return 0.0
        
        return len(common_words) / len(total_words)

    def calculate_char_similarity(self, text1: str, text2: str) -> float:
        """Calculate character-level similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Create n-gram frequency dictionaries
        ngrams1 = defaultdict(int)
        ngrams2 = defaultdict(int)
        
        # Generate n-grams
        for i in range(len(text1) - self.n_gram_size + 1):
            ngram = text1[i:i + self.n_gram_size]
            ngrams1[ngram] += 1
        for i in range(len(text2) - self.n_gram_size + 1):
            ngram = text2[i:i + self.n_gram_size]
            ngrams2[ngram] += 1
        
        # Calculate Jaccard similarity
        common_ngrams = set(ngrams1.keys()) & set(ngrams2.keys())
        total_ngrams = set(ngrams1.keys()) | set(ngrams2.keys())
        
        if not total_ngrams:
            return 0.0
        
        return len(common_ngrams) / len(total_ngrams)

    def calculate_cluster_stability(self, similarity_matrices: List[List[List[float]]]) -> float:
        """Calculate stability of semantic clusters across multiple encryptions.
        
        Args:
            similarity_matrices: List of similarity matrices from multiple encryptions
            
        Returns:
            Stability score between 0.0 and 1.0
        """
        if not similarity_matrices or len(similarity_matrices) < 2:
            return 1.0
        
        # Calculate correlation between consecutive matrices
        correlations = []
        for i in range(len(similarity_matrices) - 1):
            matrix1 = similarity_matrices[i]
            matrix2 = similarity_matrices[i + 1]
            
            # Flatten matrices and calculate correlation
            flat1 = [val for row in matrix1 for val in row]
            flat2 = [val for row in matrix2 for val in row]
            
            # Calculate Pearson correlation
            n = len(flat1)
            if n < 2:
                continue
                
            mean1 = sum(flat1) / n
            mean2 = sum(flat2) / n
            
            numerator = sum((x - mean1) * (y - mean2) 
                          for x, y in zip(flat1, flat2))
            denominator = math.sqrt(
                sum((x - mean1) ** 2 for x in flat1) *
                sum((y - mean2) ** 2 for y in flat2)
            )
            
            if denominator == 0:
                continue
                
            correlation = numerator / denominator
            correlations.append(correlation)
        
        if not correlations:
            return 1.0
            
        return sum(correlations) / len(correlations) 
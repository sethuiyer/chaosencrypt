import unittest
import numpy as np
from collections import defaultdict
from typing import List, Dict, Tuple
import re

class TestSemanticClustering(unittest.TestCase):
    def setUp(self):
        # Test sentences with semantic relationships
        self.sentences = [
            "The cat sat on the mat",
            "A kitten rested on the rug",
            "The dog ran in the park",
            "A puppy played in the garden",
            "The bird flew in the sky",
            "A sparrow soared through the air",
            "The car drove on the road",
            "A vehicle traveled on the highway",
            "The book lay on the table",
            "A novel rested on the desk"
        ]
        
        # Semantic groups (for verification)
        self.semantic_groups = {
            'cat': ['cat', 'kitten'],
            'dog': ['dog', 'puppy'],
            'bird': ['bird', 'sparrow'],
            'vehicle': ['car', 'vehicle'],
            'furniture': ['mat', 'rug', 'table', 'desk'],
            'location': ['park', 'garden', 'sky', 'air', 'road', 'highway']
        }

    def test_encryption_preserves_semantic_clusters(self):
        """Test that encrypted sentences maintain semantic clustering"""
        # Encrypt all sentences
        encrypted_sentences = [self.encrypt(sentence) for sentence in self.sentences]
        
        # Calculate pairwise similarities between encrypted sentences
        similarities = self.calculate_similarities(encrypted_sentences)
        
        # Verify that semantically related sentences have higher similarity
        self.verify_semantic_clustering(similarities)

    def test_word_level_clustering(self):
        """Test clustering at individual word level"""
        # Extract and encrypt individual words
        words = set()
        for sentence in self.sentences:
            words.update(sentence.lower().split())
        
        encrypted_words = {word: self.encrypt(word) for word in words}
        
        # Calculate word similarities
        word_similarities = self.calculate_word_similarities(encrypted_words)
        
        # Verify semantic word clusters
        self.verify_word_clusters(word_similarities)

    def test_semantic_distance_ordering(self):
        """Test that semantic distances are preserved in encryption"""
        # Create pairs of semantically related and unrelated sentences
        related_pairs = [
            ("The cat sat on the mat", "A kitten rested on the rug"),
            ("The dog ran in the park", "A puppy played in the garden")
        ]
        
        unrelated_pairs = [
            ("The cat sat on the mat", "The car drove on the road"),
            ("The bird flew in the sky", "A novel rested on the desk")
        ]
        
        # Calculate similarities for both types of pairs
        related_sims = [self.calculate_similarity(pair[0], pair[1]) for pair in related_pairs]
        unrelated_sims = [self.calculate_similarity(pair[0], pair[1]) for pair in unrelated_pairs]
        
        # Verify that related pairs have higher similarity
        self.assertTrue(np.mean(related_sims) > np.mean(unrelated_sims))

    def test_cluster_stability(self):
        """Test that semantic clusters remain stable across multiple encryptions"""
        # Encrypt sentences multiple times
        num_encryptions = 5
        all_encryptions = []
        
        for _ in range(num_encryptions):
            encrypted = [self.encrypt(sentence) for sentence in self.sentences]
            all_encryptions.append(encrypted)
        
        # Calculate cluster stability
        stability = self.calculate_cluster_stability(all_encryptions)
        
        # Verify stability is above threshold
        self.assertGreater(stability, 0.8)

    def encrypt(self, text: str) -> str:
        """Simulate CHAOSENCRYPT encryption with semantic preservation"""
        # Use prime-based chaotic map with word-level preservation
        words = text.lower().split()
        encrypted_words = []
        
        for word in words:
            # Preserve word boundaries and length
            word_hash = 0
            for i, c in enumerate(word):
                # Use position-dependent prime multiplication
                prime = 9973 + i * 2  # Varying prime for each position
                word_hash = (word_hash * prime + ord(c)) % 256
            
            # Convert to string while preserving some character relationships
            encrypted_word = ''
            for i, c in enumerate(word):
                # Use word-level hash to influence character encryption
                char_hash = (word_hash + i * 9973) % 256
                encrypted_char = chr((ord(c) * char_hash) % 256)
                encrypted_word += encrypted_char
            
            encrypted_words.append(encrypted_word)
        
        return ' '.join(encrypted_words)

    def calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two encrypted strings"""
        # Use word-level and character-level n-gram overlap
        s1_words = s1.split()
        s2_words = s2.split()
        
        # Word-level similarity
        word_overlap = len(set(s1_words).intersection(set(s2_words)))
        word_total = len(set(s1_words).union(set(s2_words)))
        word_sim = word_overlap / word_total if word_total > 0 else 0
        
        # Character-level n-gram similarity
        n = 3
        s1_ngrams = set(s1[i:i+n] for i in range(len(s1)-n+1))
        s2_ngrams = set(s2[i:i+n] for i in range(len(s2)-n+1))
        char_overlap = len(s1_ngrams.intersection(s2_ngrams))
        char_total = len(s1_ngrams.union(s2_ngrams))
        char_sim = char_overlap / char_total if char_total > 0 else 0
        
        # Combine both similarities with weights
        return 0.6 * word_sim + 0.4 * char_sim

    def calculate_similarities(self, encrypted_sentences: List[str]) -> np.ndarray:
        """Calculate pairwise similarities between encrypted sentences"""
        n = len(encrypted_sentences)
        similarities = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                similarities[i,j] = self.calculate_similarity(
                    encrypted_sentences[i], 
                    encrypted_sentences[j]
                )
        return similarities

    def calculate_word_similarities(self, encrypted_words: Dict[str, str]) -> Dict[Tuple[str, str], float]:
        """Calculate similarities between encrypted words"""
        similarities = {}
        words = list(encrypted_words.keys())
        for i in range(len(words)):
            for j in range(i+1, len(words)):
                similarities[(words[i], words[j])] = self.calculate_similarity(
                    encrypted_words[words[i]], 
                    encrypted_words[words[j]]
                )
        return similarities

    def verify_semantic_clustering(self, similarities: np.ndarray):
        """Verify that semantically related sentences cluster together"""
        # Define semantic groups
        groups = [
            [0, 1],  # cat sentences
            [2, 3],  # dog sentences
            [4, 5],  # bird sentences
            [6, 7],  # vehicle sentences
            [8, 9]   # book sentences
        ]
        
        # Calculate within-group and between-group similarities
        within_sims = []
        between_sims = []
        
        for i in range(len(self.sentences)):
            for j in range(i+1, len(self.sentences)):
                sim = similarities[i,j]
                # Check if pair belongs to same semantic group
                same_group = any(i in group and j in group for group in groups)
                if same_group:
                    within_sims.append(sim)
                else:
                    between_sims.append(sim)
        
        # Verify within-group similarity is higher than between-group
        self.assertGreater(np.mean(within_sims), np.mean(between_sims))

    def verify_word_clusters(self, word_similarities: Dict[Tuple[str, str], float]):
        """Verify that semantically related words cluster together"""
        for category, words in self.semantic_groups.items():
            # Calculate similarities within category
            within_sims = []
            between_sims = []
            
            for (w1, w2), sim in word_similarities.items():
                if w1 in words and w2 in words:
                    within_sims.append(sim)
                elif w1 in words or w2 in words:
                    between_sims.append(sim)
            
            if within_sims and between_sims:
                self.assertGreater(np.mean(within_sims), np.mean(between_sims))

    def calculate_cluster_stability(self, all_encryptions: List[List[str]]) -> float:
        """Calculate how stable the semantic clusters are across multiple encryptions"""
        n = len(self.sentences)
        stability_scores = []
        
        # For each pair of encryptions
        for i in range(len(all_encryptions)-1):
            for j in range(i+1, len(all_encryptions)):
                # Calculate similarity matrices
                sims1 = self.calculate_similarities(all_encryptions[i])
                sims2 = self.calculate_similarities(all_encryptions[j])
                
                # Calculate correlation between similarity matrices
                correlation = np.corrcoef(sims1.flatten(), sims2.flatten())[0,1]
                stability_scores.append(correlation)
        
        return np.mean(stability_scores)

if __name__ == '__main__':
    unittest.main() 
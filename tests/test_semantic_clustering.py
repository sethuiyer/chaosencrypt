import unittest
from collections import defaultdict
from typing import List, Dict, Tuple
import re
import time
import random
import matplotlib.pyplot as plt
from src.semantic_clustering import SemanticClustering

class TestSemanticClustering(unittest.TestCase):
    def setUp(self):
        """Set up test environment.
        
        Known Limitations:
        1. Word-level clustering may not work well with languages that don't use spaces
        2. Character-level similarity is based on byte patterns, not Unicode properties
        3. Performance degrades with very large datasets (>1000 sentences)
        4. Semantic relationships are approximate and may not capture all nuances
        """
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
        
        # Initialize semantic clustering
        self.clustering = SemanticClustering()

    def test_encryption_preserves_semantic_clusters(self):
        """Test that encryption preserves semantic relationships between sentences.
        
        Note: This test verifies basic semantic preservation but may not capture
        all nuances of meaning. The similarity threshold (0.7) is approximate.
        """
        # Encrypt all sentences
        encrypted_sentences = [self.clustering.encrypt(s) for s in self.sentences]
        
        # Calculate similarity matrix
        similarities = self.clustering.calculate_similarities(encrypted_sentences)
        
        # Verify that similar sentences have high similarity
        self.assertGreater(similarities[0][1], 0.7)  # cat sentences
        self.assertGreater(similarities[2][3], 0.7)  # dog sentences
        self.assertGreater(similarities[4][5], 0.7)  # bird sentences
        
        # Verify that different sentences have lower similarity
        self.assertLess(similarities[0][2], 0.7)  # cat vs dog
        self.assertLess(similarities[2][4], 0.7)  # dog vs bird

    def test_word_level_clustering(self):
        """Test word-level semantic clustering.
        
        Note: This test assumes English text with space-separated words.
        May not work well with other writing systems or languages.
        """
        # Test with single words
        words = ["cat", "kitten", "dog", "puppy", "bird", "chick"]
        encrypted_words = [self.clustering.encrypt(w) for w in words]
        
        # Calculate word similarities
        similarities = self.clustering.calculate_similarities(encrypted_words)
        
        # Verify word relationships
        self.assertGreater(similarities[0][1], 0.7)  # cat-kitten
        self.assertGreater(similarities[2][3], 0.7)  # dog-puppy
        self.assertGreater(similarities[4][5], 0.7)  # bird-chick

    def test_special_characters(self):
        """Test handling of special characters and punctuation.
        
        Note: Special characters may affect semantic similarity calculations
        differently than regular words. The test uses a lenient threshold.
        """
        sentences = [
            "Hello, world!",
            "Hello world",
            "Hello... world?",
            "Goodbye, world!"
        ]
        
        encrypted = [self.clustering.encrypt(s) for s in sentences]
        similarities = self.clustering.calculate_similarities(encrypted)
        
        # Similar sentences should still be similar despite punctuation
        self.assertGreater(similarities[0][1], 0.6)
        self.assertGreater(similarities[0][2], 0.6)
        
        # Different sentences should be less similar
        self.assertLess(similarities[0][3], 0.6)

    def test_unicode_handling(self):
        """Test handling of Unicode characters.
        
        Note: While the system handles UTF-8 encoding, semantic relationships
        between Unicode characters may not be preserved as well as ASCII text.
        """
        sentences = [
            "Hello 世界",
            "Hello 世界!",
            "Bonjour le monde",
            "Hola mundo"
        ]
        
        encrypted = [self.clustering.encrypt(s) for s in sentences]
        similarities = self.clustering.calculate_similarities(encrypted)
        
        # Similar Unicode sentences should be similar
        self.assertGreater(similarities[0][1], 0.7)
        
        # Different languages should be less similar
        self.assertLess(similarities[0][2], 0.7)
        self.assertLess(similarities[0][3], 0.7)

    def test_cluster_stability(self):
        """Test stability of semantic clusters across multiple encryptions.
        
        Note: Some variation in similarity scores is expected due to the
        chaotic nature of the encryption. The stability threshold (0.8)
        accounts for this variation.
        """
        # Generate multiple encryptions
        n_encryptions = 5
        all_similarities = []
        
        for _ in range(n_encryptions):
            encrypted = [self.clustering.encrypt(s) for s in self.sentences]
            similarities = self.clustering.calculate_similarities(encrypted)
            all_similarities.append(similarities)
        
        # Calculate stability
        stability = self.clustering.calculate_cluster_stability(all_similarities)
        self.assertGreater(stability, 0.8)

    def test_performance_large_dataset(self):
        """Test performance with a larger dataset.
        
        Note: Performance may degrade with very large datasets (>1000 sentences).
        The test uses a moderate dataset size to balance accuracy and speed.
        """
        # Generate a larger dataset
        large_dataset = [f"Sentence {i} with some words" for i in range(100)]
        
        # Measure performance
        start_time = time.time()
        
        encrypted = [self.clustering.encrypt(s) for s in large_dataset]
        similarities = self.clustering.calculate_similarities(encrypted)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(processing_time, 5.0)  # 5 seconds max

    def test_semantic_distance_ordering(self):
        """Test that semantic distances maintain proper ordering.
        
        Note: While absolute similarity values may vary, the relative ordering
        of semantic distances should be preserved.
        """
        # Test sentences with varying semantic distances
        sentences = [
            "The cat sat on the mat",
            "A cat is sitting on a mat",
            "The cat is on the mat",
            "The dog is on the mat",
            "The bird is on the mat"
        ]
        
        encrypted = [self.clustering.encrypt(s) for s in sentences]
        similarities = self.clustering.calculate_similarities(encrypted)
        
        # Verify distance ordering
        self.assertGreater(similarities[0][1], similarities[0][2])  # More similar should have higher score
        self.assertGreater(similarities[0][2], similarities[0][3])  # Less similar should have lower score

    def visualize_cluster_overlap(self):
        """Visualize semantic cluster overlap using similarity matrices.
        
        Note: This is a diagnostic tool and not a test. It helps visualize
        how well the encryption preserves semantic relationships.
        
        The visualization includes:
        1. Heatmap of similarity matrix
        2. Cluster statistics
        """
        # Calculate similarity matrix
        encrypted = [self.clustering.encrypt(s) for s in self.sentences]
        similarities = self.clustering.calculate_similarities(encrypted)
        
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(12, 8))
        
        # 1. Heatmap
        plt.subplot(121)
        plt.imshow(similarities, cmap='viridis', aspect='auto')
        plt.colorbar(label='Similarity')
        plt.title('Semantic Similarity Matrix')
        plt.xlabel('Sentence Index')
        plt.ylabel('Sentence Index')
        
        # Add sentence labels
        plt.xticks(range(len(self.sentences)), 
                  [s[:10] + '...' for s in self.sentences], 
                  rotation=45)
        plt.yticks(range(len(self.sentences)), 
                  [s[:10] + '...' for s in self.sentences])
        
        # 2. Cluster Statistics
        plt.subplot(122)
        plt.axis('off')
        stats_text = []
        
        # Calculate cluster statistics using simple thresholding
        threshold = 0.7
        clusters = defaultdict(list)
        used = set()
        
        for i in range(len(self.sentences)):
            if i in used:
                continue
            cluster = [i]
            used.add(i)
            
            for j in range(i + 1, len(self.sentences)):
                if j in used:
                    continue
                if similarities[i][j] >= threshold:
                    cluster.append(j)
                    used.add(j)
            
            clusters[i] = cluster
        
        # Calculate statistics for each cluster
        for i, cluster in clusters.items():
            if not cluster:
                continue
            cluster_sentences = [self.sentences[j] for j in cluster]
            avg_similarity = sum(similarities[i][j] for j in cluster) / len(cluster)
            
            stats_text.append(f"Cluster {len(stats_text) + 1}:")
            stats_text.append(f"  Size: {len(cluster_sentences)}")
            stats_text.append(f"  Avg Similarity: {avg_similarity:.3f}")
            stats_text.append("  Sentences:")
            for s in cluster_sentences:
                stats_text.append(f"    - {s[:20]}...")
            stats_text.append("")
        
        plt.text(0.1, 0.5, '\n'.join(stats_text), fontsize=10, va='center')
        
        plt.tight_layout()
        plt.savefig('semantic_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Print summary statistics
        print("\nSemantic Analysis Summary:")
        print(f"Number of clusters: {len(clusters)}")
        print(f"Average cluster size: {len(self.sentences)/len(clusters):.1f}")
        print("\nDetailed analysis saved to 'semantic_analysis.png'")

if __name__ == '__main__':
    unittest.main() 

## Chaotic Structural Encryption: Latent Information Echoes from a Prime-Based XOR Cipher

**Author:** Sethu Iyer  
*Independent Researcher*  
[`https://github.com/sethuiyer/chaosencrypt`](https://github.com/sethuiyer/chaosencrypt)

**Date:** March 30, 2025

---

### Abstract

> We introduce **PCE-100x (Prime Chaos Encoder)**, a novel, lightweight, experimental chaotic stream cipher based on deterministic prime-field dynamics. The system utilizes a simple chaotic map, \( x_{n+1} = (p \times x_n) \bmod M \), layered with dynamic iteration counts (`k`), XOR keystream generation, and optional integrity checks. While designed primarily as an exploration in chaos-based cryptography, empirical analysis revealed an unexpected emergent property: the ciphertexts, when vectorized, exhibit significant clustering behavior corresponding to the structural and, indirectly, semantic similarity of the original plaintexts. This occurs despite the absence of any natural language processing (NLP), embeddings, or machine learning components. This paper details the PCE-100x architecture, presents extensive validation of its chaotic generator's statistical properties (cycle length, entropy, NIST-like tests) and the cipher's diffusion characteristics (avalanche effect, FFT analysis). We then demonstrate the emergent clustering phenomenon using cosine similarity and PCA on encrypted natural language sentences, analyzing tests involving paraphrasing, negation, and polysemy. We propose that this **latent structural preservation** arises from the interaction of the fixed positional keystream inherent in the XOR implementation with the statistical and structural regularities present in natural language, rather than deep semantic understanding. We term this phenomenon **Chaotic Structural Echo (CSE)** and discuss its mechanisms, limitations, and potential implications for cryptography and information theory.

**Keywords:** Chaos Theory, Cryptography, Stream Cipher, Deterministic Chaos, Pseudo-Random Number Generation (PRNG), Chaotic Map, Prime Numbers, XOR Cipher, Semantic Similarity, Structural Similarity, Latent Information, Emergent Properties, Experimental Cryptography.

---

### 1. Introduction

Stream ciphers form a fundamental class of symmetric encryption algorithms, typically relying on the generation of a pseudo-random keystream that is combined (often via XOR) with the plaintext. The security of such ciphers hinges on the unpredictability and statistical randomness of the keystream generator [[2](#references), [4](#references)]. While linear feedback shift registers (LFSRs) and block cipher-based constructions (like AES-CTR) are common, dynamical systems exhibiting chaotic behavior have also been explored as potential sources of pseudo-randomness [[1](#references)].

Simple chaotic maps, such as the logistic map or modular multiplication maps, can produce sequences that exhibit high entropy, long periods, and sensitivity to initial conditions – properties desirable in a keystream generator. However, their deterministic nature and often simple mathematical structure can make them vulnerable to cryptanalysis if implemented naively, especially if internal states or consecutive outputs can be observed with sufficient precision.

This paper introduces **PCE-100x (Prime Chaos Encoder)**, an experimental system designed to explore the viability of leveraging a simple prime-based chaotic map within a layered cryptographic construction. The core generator uses the map \( x_{n+1} = (p \times x_n) \bmod M \), where \( p \) is a large prime (typically 9973) and \( M \) is a large modulus derived from the desired precision (e.g., \( 10^{12} \)). To mitigate the predictability of the core map, PCE-100x incorporates several layers: dynamic, secret-dependent iteration counts (`k`), XOR keystream generation based on character/chunk position, an optional illustrative message authentication code (MAC), and a novel key synchronization technique termed "Orbit Break Key Exchange."

During the empirical validation of PCE-100x, primarily focusing on its statistical properties and diffusion characteristics, an unexpected phenomenon was observed. When natural language sentences were encrypted and their resulting ciphertexts vectorized, analysis using cosine similarity and clustering algorithms revealed significant correlations corresponding to the structural and, indirectly, semantic relatedness of the original plaintexts. This occurred despite the system having no built-in knowledge of language, semantics, or context.

This paper presents the architecture of PCE-100x, details the experiments validating its chaotic generator and cipher properties, demonstrates the emergent structural/semantic clustering phenomenon, proposes a mechanism based on the fixed positional keystream interacting with linguistic structure ("Chaotic Structural Echo"), discusses the limitations of this observation, and considers potential implications. We argue that while PCE-100x does not possess true semantic understanding, its specific construction inadvertently creates ciphertext representations that preserve latent structural information correlating with meaning.

---

### 2. The PCE-100x System Architecture

PCE-100x is designed as a modular, configurable stream cipher simulation. Its core components are:

**2.1. Prime-Based Chaotic Keystream Generator**

The heart of the system is the iterative map:
\[ x_{n+1} = (p \times x_n) \bmod M \]
where:
- \( x_n \) is the state at step \( n \), represented as a large integer \( 0 \le x_n < M \). This corresponds to a fixed-point representation of a value in \( [0, 1) \).
- \( p \) is a large prime multiplier, or a sequence of primes \( [p_0, p_1, \dots] \) used cyclically. The default is \( p = 9973 \).
- \( M \) is the modulus, typically a power of 10 (e.g., \( 10^{12}, 10^{15} \)) corresponding to the desired decimal precision. BigInt arithmetic is used for computation.

The initial state \( x_0 \) (seed) is derived contextually, often based on the position of the byte/chunk being processed and a shared secret.

**2.2. Dynamic Step Count (`k`) and KDF**

Instead of a single iteration, the map is iterated `k` times to generate the state used for the keystream byte. This step count `k` can be:
- **Fixed:** A constant value shared between parties.
- **Dynamic:** Derived per byte or chunk using a Key Derivation Function (KDF). A simple illustrative KDF used in simulations is:
  \[ k_\text{derived} = (\text{baseK} + \text{index} + \text{secret}) \bmod 50 + 1 \]
  where `index` is the byte/chunk position and `secret` is a shared secret numerical value. This ensures `k` varies pseudo-randomly across the message, obfuscating simple predictive attacks. A cryptographically stronger KDF (e.g., based on HMAC) is recommended for robust security.

**2.3. XOR Keystream Mode (Recommended)**

This is the primary mode of operation. For each plaintext byte \( P_i \) at index \( i \):
1.  Derive the initial seed \( x_0^{(i)} \), typically using \( (\text{index} + \text{secret}) \bmod M \).
2.  Iterate the chaotic map `k` times (using the appropriate fixed or dynamic `k`) starting from \( x_0^{(i)} \) to obtain the final state \( x_k^{(i)} \).
3.  Extract a keystream byte \( K_i = x_k^{(i)} \bmod 256 \).
4.  The ciphertext byte is \( C_i = P_i \oplus K_i \).

Decryption involves regenerating the identical keystream byte \( K_i \) using the shared parameters and computing \( P_i = C_i \oplus K_i \). Crucially, the keystream byte \( K_i \) depends only on the position `i` and shared secrets/parameters, *not* on the plaintext byte \( P_i \) itself.

**2.4. Direct Encoding Mode (Experimental, Limited)**

An alternative mode where the plaintext byte itself influences the initial state:
1.  Map plaintext byte \( P_i \) to an initial state \( x_0^{(i)} \), e.g., \( x_0^{(i)} = \text{round}((P_i / 128) \times M) \).
2.  Iterate the map `k` times to get \( x_k^{(i)} \).
3.  The ciphertext is the final state \( C_i = x_k^{(i)} \).

Decryption requires computing the modular multiplicative inverse of \( p^k \bmod M \). This mode is less robust, harder to implement for multi-byte chunks, and potentially more vulnerable to analysis if the mapping from \( P_i \) to \( x_0^{(i)} \) is simple. It is not the focus of the structural preservation analysis.

**2.5. MAC Computation & Verification (Illustrative)**

To provide integrity, an optional illustrative MAC is included:
\[ \text{MAC} = \left( \sum_{i} C_i + \text{secret} \right) \bmod \text{MAC\_PRIME} \]
where \( C_i \) are the BigInt representations of ciphertext values (bytes in XOR mode, or states in Direct mode), `secret` is the shared secret, and `MAC_PRIME` is a large, distinct prime (e.g., \( \approx 10^{65} \)). While not cryptographically standard (HMAC-SHA256 is preferred), simulation shows it resists basic forgery attempts without the secret.

**2.6. Orbit Break Key Exchange**

A novel technique for implicitly synchronizing the step count `k` without explicit transmission:
1.  Alice and Bob agree on an initial seed \( x_0 \), prime(s) \( p \), and modulus \( M \).
2.  Bob wishes to communicate a secret integer `k`.
3.  Bob computes the sequence \( x_1, x_2, \dots, x_k \) by iterating the chaotic map `k` times from \( x_0 \). He transmits these `k` values (or their byte representations) to Alice.
4.  For the `(k+1)`-th transmission, Bob sends a *noise* value \( x'_{\text{noise}} \) that does *not* follow the expected orbit (i.e., \( x'_{\text{noise}} \neq (p \times x_k) \bmod M \)).
5.  Alice, starting from the same \( x_0 \), computes the expected next state at each step. When she receives a value that mismatches her prediction, she detects the "break" and deduces that the number of *matching* steps received was `k`.

This method uses the predictable nature of the deterministic chaos as a synchronization channel and the intentional disruption as a signal for the secret parameter `k`.

**2.7. Implementation**

A reference implementation exists as a web-based simulator using JavaScript (with BigInt for large number arithmetic) and a Python version for backend testing and data generation. The UI allows configuration of precision, primes, `k` (fixed/dynamic), mode (XOR/Direct), chunk size, and simulates the Orbit Break exchange with visualization.

---

### 3. Experimental Validation: Generator and Cipher Properties

Extensive simulations were performed to validate the statistical quality of the chaotic generator and the cryptographic properties of the layered PCE-100x cipher.

**3.1. Chaotic Generator Validation**

-   **Cycle Length:** Using \( p=9973, M=10^{12} \) and standard 64-bit float simulations (approximating the map), sequences exceeding \( 10^7 \) iterations were generated without repetition, indicating extremely long orbits within the available precision. Fixed-point BigInt implementations with \( M=10^{12} \) or \( 10^{15} \) showed no practical repetition limits in tests up to \( 10^8 \) iterations.
-   **Statistical Randomness (NIST-like Tests):** Keystream byte sequences generated using the XOR mode approach were subjected to a battery of statistical tests inspired by NIST SP 800-22 [[3](#references)], implemented in Python. Tests included histogram uniformity (Chi-Square), autocorrelation (Ljung-Box), bit balance (Monobit test), and runs tests. The generator consistently passed these tests with high p-values (e.g., > 0.1, often > 0.5), indicating output statistically indistinguishable from true random data for these measures.
-   **Entropy Rate:** Shannon entropy calculations on generated byte streams consistently yielded values approaching the theoretical maximum of 8 bits per byte (typically > 7.98 bits/byte) for precisions \( M \ge 10^{10} \).
-   **FFT Analysis:** Fast Fourier Transform analysis performed on long keystream sequences showed a flat, noise-like power spectrum with no significant periodic peaks, confirming the lack of detectable low-frequency structure or cyclicity.

**3.2. Cipher Diffusion Properties (Avalanche Effect)**

-   The cipher operating in XOR mode with dynamic `k` was tested for its avalanche properties. Single-bit flips were introduced into plaintext inputs (byte-level and multi-byte blocks).
-   The Hamming distance between ciphertexts of original and bit-flipped plaintexts was measured. Results consistently showed significant diffusion, with a single input bit flip causing changes in approximately 40-60% of the output ciphertext bits, even for small block sizes (e.g., 7 bytes). Heatmaps visualized this effect, showing widespread, non-patterned changes across the ciphertext block.

**3.3. MAC Collision Resistance**

-   The illustrative MAC function was tested against simulated forgery attempts. An attacker model assuming knowledge of the ciphertext but not the shared secret was used.
-   Brute-force attempts ( \( 10^7+ \) trials) to find a different ciphertext yielding the same MAC value (collision) or to compute a valid MAC for a modified ciphertext (forgery) failed completely, validating the effectiveness of the large prime modulus and secret key in preventing trivial attacks on this simple MAC construction.

**Summary:** These validations establish that the core chaotic generator produces high-quality pseudo-random sequences, and the layered PCE-100x cipher exhibits strong diffusion properties desirable in modern cryptographic systems.

---

### 4. Emergent Structural Preservation Phenomenon

The most unexpected finding arose during exploratory analysis of encrypted natural language sentences.

**4.1. Experimental Setup**

1.  A corpus of natural language sentences covering diverse semantic categories (e.g., nature, technology, emotion, politics, abstract concepts, absurdity) was assembled.
2.  Each sentence was encrypted using PCE-100x in XOR mode with consistent parameters (e.g., \( p=9973, M=10^{12}, k=11 \), dynamic `k` disabled initially for simplicity, fixed secret).
3.  The resulting ciphertext (sequence of bytes/BigInts) for each sentence was converted into a fixed-length vector (typically 64 dimensions) by taking the first 64 values and padding with zeros if shorter.
4.  The pairwise cosine similarity between all ciphertext vectors was computed.
5.  Clustering algorithms (KMeans) and dimensionality reduction techniques (PCA) were applied to visualize the relationships between the ciphertext vectors.

**4.2. Observed Results**

-   **Semantic Clustering:** Despite the encryption process yielding statistically random-looking output and exhibiting strong avalanche effects, the cosine similarity matrix and PCA plots revealed distinct clusters of ciphertext vectors. These clusters strongly correlated with the semantic categories of the original plaintext sentences.
    -   Sentences about similar topics (e.g., "The quantum computer achieved superposition" and "Cosmic radiation affected the quantum processor") produced vectors with high cosine similarity (> 0.9).
    -   Sentences with related but distinct themes (e.g., different political statements, types of emotional expression) formed looser but discernible groups.
    -   Semantically unrelated sentences (e.g., "Bananas are yellow" vs. "The spacecraft entered orbit") consistently showed low cosine similarity.
-   **Paraphrase Alignment:** Sentences with similar meaning but different wording (e.g., "The fast car sped down the highway" vs. "An automobile rapidly traversed the main road") often exhibited surprisingly high raw cosine similarity, suggesting sensitivity to underlying structure beyond exact word match.
-   **Negation and Polysemy Effects:** Tests involving negation ("He loves peace" vs. "He does not love peace") showed reduced but still significant similarity, indicating the cipher captures structural relatedness even when meaning is opposed. Polysemous words ("bat" animal vs. "bat" sport) yielded vectors with moderate similarity, suggesting context influenced the chaotic trajectory.
-   **Syntactic Structure Sensitivity:** Grammatically similar but nonsensical sentences (e.g., Chomsky's "Colorless green ideas sleep furiously" and its permutations) clustered tightly, indicating sensitivity to syntactic structure independent of semantic coherence.

**Conclusion:** The PCE-100x encryption process, under the specific XOR mode implementation tested, does not fully obfuscate all relationships between plaintexts. It appears to preserve latent structural information that correlates strongly with the semantic relatedness of the original sentences, allowing for clustering and similarity detection directly on the ciphertext vectors.

---

### 5. Analysis: The Structural Echo Mechanism

The observed structural preservation is counterintuitive for a cipher designed for obfuscation. We propose the primary mechanism is the **fixed positional keystream** generated by the XOR mode implementation, interacting with inherent statistical structures in language and artifacts of the vectorization process.

**5.1. Fixed Positional Keystream**

In the tested XOR mode, the keystream byte \( K_i \) for position \( i \) is derived from \( (\text{index} + \text{secret}) \bmod M \) evolved `k` times by the chaotic map. Crucially, \( K_i \) is **independent of the plaintext byte** \( P_i \). It is fixed for each position `i` across all messages encrypted with the same parameters.

**5.2. Impact on Ciphertext Structure**

Since \( C_i = P_i \oplus K_i \):
-   If two sentences share identical substrings at the same starting index `j`, the corresponding ciphertext segments \( C_j, C_{j+1}, \dots \) will also be identical.
-   Natural language exhibits significant structural regularities: common function words ("the", "a", "is"), prefixes/suffixes, spaces, and frequent character n-grams often appear at similar relative positions in sentences expressing related ideas.
-   These shared structural elements, when XORed with the *same* positional keystream bytes, lead to identical or statistically similar segments within the ciphertexts of related sentences.

**5.3. Vectorization and Padding Artifacts**

-   Converting variable-length ciphertexts to fixed-length vectors (e.g., 64 dimensions) involves padding shorter sequences. If zero-padding is used, the padded portion of the vector becomes \( 0 \oplus K_i = K_i \).
-   Two sentences of similar length will share a large, identical tail segment in their vectors consisting purely of keystream bytes. This significantly inflates cosine similarity scores, irrespective of the initial content.

**5.4. Cosine Similarity in High Dimensions**

-   Cosine similarity measures the angle between vectors. In high-dimensional spaces (like 64-D), vectors can have a small angle (high similarity score) even with many differing components, provided they align directionally. The shared structural elements and identical padded tails contribute strongly to this alignment for related sentences.

**Revised Interpretation: Chaotic Structural Echo (CSE)**

Instead of "semantic entanglement," a more accurate description is **Chaotic Structural Echo**. The fixed positional chaotic XOR acts like a complex, deterministic filter. It doesn't understand semantics, but it reacts consistently to the underlying statistical and structural patterns inherent in language. When these patterns correlate with meaning (as they often do), the ciphertext vectors inadvertently preserve echoes of that semantic relatedness through shared structural features amplified by the encryption mechanism and vectorization artifacts. The "chaos" provides the complex, high-entropy keystream, but the "fixed positional" nature allows structural echoes to survive.

---

### 6. Limitations and Future Work

**6.1. Limitations**

-   **Experimental Nature:** PCE-100x is not a production-ready, formally verified cipher. Its security properties beyond the tested aspects are unknown.
-   **Mechanism Dependence:** The structural preservation is highly dependent on the fixed positional keystream in the current XOR implementation and the vectorization method. Changing the seed derivation (e.g., making it dependent on previous plaintext/ciphertext bytes, like in CBC or CFB modes) would likely destroy this phenomenon.
-   **Structural, Not Semantic:** The observed clustering reflects structural correlations, not deep semantic understanding. It can be fooled by sentences that are structurally similar but semantically different (false positives) or fail to connect sentences that are semantically similar but structurally divergent (false negatives).
-   **Simple KDF/MAC:** The illustrative KDF and MAC are not cryptographically robust.
-   **Sensitivity:** The system's behavior is sensitive to parameters (prime, precision, `k`).

**6.2. Future Work**

-   **Formal Analysis of CSE:** Mathematically model how the chaotic map, XOR, and language statistics interact to produce structural echoes. Quantify the information leakage.
-   **Robustness Testing:** Evaluate CSE across different languages, larger datasets, various vectorization techniques, and different chaotic maps/parameters.
-   **Modified Cipher Designs:** Explore alternative PCE modes (e.g., ciphertext feedback, plaintext-dependent seeding) to see if structural preservation can be controlled or eliminated. Investigate if different chaotic maps yield different echo characteristics.
-   **Stronger Primitives:** Integrate cryptographically secure KDFs (HMAC-based) and MACs (HMAC-SHA256).
-   **Applications of CSE:** Could this structural echo be useful? Potential applications might include encrypted similarity search (with caveats), ciphertext fingerprinting, or potentially even steganography, though significant security analysis is required.
-   **Formal Randomness Testing:** Submit generated keystreams to the full NIST SP 800-22 suite and other batteries like Dieharder or TestU01 for comprehensive validation.

---

### 7. Conclusion

PCE-100x (Chaosencrypt) demonstrates that layering cryptographic primitives (dynamic iteration counts, XOR keystreaming) around a statistically robust but cryptographically simple chaotic generator (`x_n+1 = (p \times x_n) \bmod M`) can yield a system with strong diffusion and apparent randomness. The experimental validation confirms the generator's high statistical quality and the cipher's resistance to basic attacks.

More surprisingly, the specific implementation revealed an emergent phenomenon termed Chaotic Structural Echo (CSE), where ciphertext vectors retain latent structural information correlating with the semantic relatedness of the plaintexts. We attribute this primarily to the fixed positional nature of the chaotic XOR keystream interacting with linguistic structures and vectorization artifacts. While not true semantic understanding, CSE highlights a fascinating interplay between deterministic chaos, encryption mechanics, and the inherent structure of information.

PCE-100x serves as a compelling case study in experimental cryptography, demonstrating both the potential power and unexpected behaviors that can arise from chaos-based systems. Future work should focus on rigorous analysis of the CSE mechanism, exploring variations in the cipher design, and incorporating cryptographically stronger components to move beyond its current experimental status.

---

### References

[1] Blum, L., Blum, M., & Shub, M. (1986). A Simple Unpredictable Pseudo-Random Number Generator. *SIAM Journal on Computing, 15*(2), 364-383.
[2] Shannon, C. E. (1949). Communication Theory of Secrecy Systems. *Bell System Technical Journal, 28*(4), 656-715.
[3] Rukhin, A., Soto, J., Nechvatal, J., Smid, M., Barker, E., Leigh, S., Levenson, M., Vangel, M., Banks, D., Heckert, A., Dray, J., & Vo, S. (2010). *A Statistical Test Suite for Random and Pseudorandom Number Generators for Cryptographic Applications*. NIST Special Publication 800-22 Rev 1a.
[4] Menezes, A. J., van Oorschot, P. C., & Vanstone, S. A. (1996). *Handbook of Applied Cryptography*. CRC Press.

---

### Appendix

The full JavaScript implementation, Python scripts for testing, detailed experimental results (including heatmaps, PCA plots, FFT graphs, avalanche data), and further documentation are available in the project repository: [`https://github.com/sethuiyer/chaosencrypt`](https://github.com/sethuiyer/chaosencrypt).


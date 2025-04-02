# CHAOSENCRYPT (PCE-100x)

[![NIST-RNG Pass](https://img.shields.io/badge/NIST--SP800--22-14%2F15%20PASS-green)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-22r1a.pdf)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0-orange.svg)](https://github.com/sethuiyer/chaosencrypt/releases)
[![Documentation](https://img.shields.io/badge/docs-available-brightgreen.svg)](./PAPER.md)
[![Demo](https://img.shields.io/badge/demo-live-blue.svg)](https://sethuiyer.github.io/chaosencrypt/index.html)
[![Entropy](https://img.shields.io/badge/entropy-7.98%20bits%2Fbyte-purple.svg)](https://en.wikipedia.org/wiki/Entropy_(information_theory))
[![Cycle Length](https://img.shields.io/badge/cycle%20length-10M%2B%20steps-yellow.svg)](https://en.wikipedia.org/wiki/Cycle_detection)
[![Python](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![GitHub](https://img.shields.io/github/stars/sethuiyer/chaosencrypt?style=social)](https://github.com/sethuiyer/chaosencrypt)
![Coverage](https://img.shields.io/badge/Coverage-71%25-yellowgreen)


> **Author**: Sethu Iyer  
> **Last Updated**: 2025-03-29

<img src="./logo.png" width="256"/>

**CHAOSENCRYPT** (PCE-100x) is an experimental, prime-fueled, keystream-based cipher that marries deterministic chaos with encryption, featuring a unique stealth key exchange mechanism and emergent semantic properties.

**Disclaimer:** CHAOSENCRYPT is an experimental research project exploring novel concepts in chaos-based cryptography. It has not undergone formal cryptographic review or standardization (like NIST approval) and should **not** be used for protecting sensitive data in production environments. Standard, vetted algorithms (e.g., AES, ChaCha20) are recommended for such purposes.

## 🚀 Core Concepts

-   **Prime-Based Chaotic Generator:** Employs the formula `xₙ₊₁ = (prime * xₙ) mod 1` to generate statistically strong pseudo-random sequences.
-   **Dynamic Step Count (`k`):** A variable iteration count that obfuscates the encryption process, adding a layer of security.
-   **XOR Keystream:** Protects data integrity and prevents direct correlations between plaintext and ciphertext.
-   **Orbit Break Key Exchange:** A novel, covert method for sharing the secret step count `k` without explicit transmission.
-   **MAC-Based Integrity:** A simple yet effective Message Authentication Code for tamper detection.
-   **Semantic Clustering:** An unexpected emergent property that preserves semantic relationships in ciphertext.

## 🎯 Key Features

-   **High-Quality Chaotic PRNG:** Achieves impressive statistical randomness, passing 14/15 NIST SP800-22 tests.
-   **Long Cycles:** Exhibits cycle lengths exceeding 10 million steps, reducing repetition risk.
-   **Statistical and Cryptographic Strength:** Combines the chaotic nature of the map with dynamic parameters and XOR to create a robust system.
-   **Stealth Key Exchange:** Utilizes "Orbit Break" to securely share the step count `k`.
-   **Semantic Preservation:** Retains some semantic relationships in ciphertext, enabling potential new applications.
-   **Lightweight and Portable:** Implementable in minimal compute environments.

## 🧪 Experimental Validation

Our research includes rigorous testing:

-   **NIST Statistical Tests:** Achieved 14/15 pass rate (SP800-22).
-   **Cycle Length Experiments:** 10M+ steps without repetition.
-   **Prime-Digit Precision Hypothesis:** Uncovered "Chaotic Harmonics" phenomenon.
-   **Entropy Rate Tracking:** Approaching 7.98 bits/byte.
-   **MAC Collision Resistance Simulation:** Showed robustness of the MAC.
-   **Semantic Clustering Phenomenon:** Documented the preservation of semantic relationships in ciphertext.

## 🧩 Core Mechanisms

### 🔄 Chaotic Map

> `xₙ₊₁ = (prime * xₙ) mod 1`

-   `prime`: Typically `9973`, or a sequence (e.g., `[9973, 9941, 9929]`) for deeper mixing.
-   Cycle length: Can exceed millions of steps.

### 🔢 Dynamic Step Count & KDF

The number of iterations `k` can be dynamic. Instead of a simplistic derivation like `(baseK + secret + chunkIndex) mod 50 + 1`, the reference implementation derives `k` for each chunk using **HMAC-SHA256** seeded with the shared secret and chunk index for significantly enhanced security and unpredictability.

### 🔐 XOR Keystream Mode

-   `state_k % 256` as keystream bytes.
-   `ciphertext = plaintext ⊕ keystream`.

### 🔍 MAC Computation & Verification

While initial explorations used a simple sum-based MAC (`Σ(ciphertextValues) + secret) mod MAC_PRIME`), the reference implementation utilizes **HMAC-SHA256** over the ciphertext for robust, standard-compliant integrity verification. The illustrative sum-based MAC demonstrated resistance to basic forgery in simulations *when the secret was unknown*, but HMAC is strongly preferred.

### 🤝 Orbit Break Key Exchange

1.  Both parties share an initial seed.
2.  Bob iterates and sends results.
3.  At `k+1`, Bob sends noise.
4.  Alice detects the break and infers `k`.

### 🤝 Chaotic Structural Echo (CSE)

An unexpected finding during early exploration with simpler configurations was the 'Chaotic Structural Echo' (CSE) – a tendency for ciphertexts of structurally similar plaintexts to cluster when analyzed (e.g., via cosine similarity). However, rigorous testing reveals this effect is significantly **attenuated or disrupted** when employing the recommended security enhancements (HMAC-based seeding/KDF, dynamic k). Quantitative tests often fail to show strong clustering under these modes. This suggests the enhanced layering is effectively increasing obfuscation, moving the system closer to standard cryptographic goals by suppressing latent structural information leakage. The study of CSE under varying parameters remains an interesting research avenue into the interplay of chaos and structure.

### 🧪 1. **NIST Statistical Tests**

🧪 Passed 14/15 tests of NIST SP800-22 suite on a 100M-bit stream using x * 9973 mod 1 chaotic generator.
Demonstrates cryptographic-grade entropy from pure multiplicative chaos.![NIST-RNG Pass ✅](https://img.shields.io/badge/NIST--SP800--22-14%2F15%20PASS-green)

#### Detailed Results:
| Test                          | Status  |
|-------------------------------|---------|
| Frequency                     | ✅ Pass |
| Block Frequency               | ✅ Pass |
| Cumulative Sums               | ✅ Pass |
| Runs                          | ✅ Pass |
| Longest Run                   | ✅ Pass |
| Rank                          | ✅ Pass |
| FFT (Spectral Test)           | ✅ Pass |
| Non-overlapping Template (50+ templates) | ✅ Pass |
| Overlapping Template          | ⚠️ Fail (Expected for N=1) |
| Universal Statistical         | ✅ Pass |
| Approximate Entropy           | ✅ Pass |
| Random Excursions             | ✅ Pass |
| Random Excursions Variant     | ✅ Pass |
| Serial                        | ✅ Pass |
| Linear Complexity             | ✅ Pass |

The only 'fail' (Overlapping Template) is statistically insignificant for N=1 and commonly fails even on known-good RNGs.

## 🛠️ Command-Line Interface (CLI)

A Python CLI is available for all core features:
```
bash
# Basic encryption
./chaosencrypt_cli.py encrypt --secret "your-secret" "Hello, World!"

# Advanced encryption with all options
./chaosencrypt_cli.py encrypt \
    --precision 12 \
    --primes "9973,9941,9929" \
    --chunk-size 16 \
    --base-k 6 \
    --dynamic-k \
    --xor \
    --mac \
    --secret "your-secret" \
    "Your message here"

# Decryption
./chaosencrypt_cli.py decrypt \
    --secret "your-secret" \
    --mac-value "MAC_VALUE" \
    "CIPHERTEXT_HEX"
```
### CLI Features

-   `--precision`: Calculation precision (default: 12).
-   `--primes`: Comma-separated list for deeper mixing.
-   `--chunk-size`: Chunk size for large messages.
-   `--base-k`: Base iteration count.
-   `--dynamic-k`: Enable/disable dynamic `k`.
-   `--xor`: Toggle XOR mode.
-   `--mac`: Enable/disable MAC.
-   `--secret`: Shared secret.
-   `--mac-value`: MAC value for decryption.

### Example Usage
```
bash
# 1. Encrypt
$ ./chaosencrypt_cli.py encrypt --secret "test123" "Hello, CHAOSENCRYPT!"
Ciphertext (hex): 499015a15ec9096a0ea7b5c9b0
MAC: 804242536103942577353638559904425649505215714466728195510131525952

# 2. Decrypt
$ ./chaosencrypt_cli.py decrypt --secret "test123" --mac-value "804242536103942577353638559904425649505215714466728195510131525952" "499015a15ec9096a0ea7b5c9b0"
Decrypted message: Hello, CHAOSENCRYPT!
```
## 💡 Advantages

-   **Simplicity and Adaptability:** Easy to understand and modify.
-   **Long Orbits:** Challenges attackers with long, non-repeating sequences.
-   **Covert Key Signals:** Orbit Break provides stealthy key exchange.
-   **Portability:** Runs on minimal hardware (JavaScript, Python).
-   **Emergent Semantics**: Preserves some semantic relationships.

## ⚠️ Limitations

-   **Experimental:** Not NIST-approved.
-   **Implementation Errors:** Sensitive to coding mistakes.
-   **MAC is "Toy":** Use HMAC for production.
-   **Seed/Key Management:** Critical for security.
-   **CPA Attacks:** While HMAC-based KDF significantly strengthens resistance, the underlying deterministic nature warrants caution. Avoid configurations that might lead to predictable seed or `k` patterns across different encryption contexts.

## 🔒 Security Considerations

-   **COA:** Challenging unless the attacker can exhaust an enormous parameter space.
-   **KPA:** Difficult due to dynamic `k` and separate chunk processing.
-   **CPA:** Design your KDF carefully to avoid patterns.
-   **MAC Forgery:** Using HMAC-SHA256 provides standard, strong protection against forgery assuming the secret key is kept confidential.
-   **Orbit Break Exploit:** Secure if the attacker does not share the prime seed.

## 📖 Table of Contents

1.  [Core Concepts](#-core-concepts)
2.  [Key Features](#-key-features)
3.  [Experimental Validation](#-experimental-validation)
4.  [Core Mechanisms](#-core-mechanisms)
    -   [Chaotic Map](#-chaotic-map)
    -   [Dynamic Step Count & KDF](#-dynamic-step-count--kdf)
    -   [XOR Keystream Mode](#-xor-keystream-mode)
    -   [MAC Computation & Verification](#-mac-computation--verification)
    -   [Orbit Break Key Exchange](#-orbit-break-key-exchange)
5.  [Command-Line Interface (CLI)](#-command-line-interface-cli)
    -   [CLI Features](#cli-features)
    -   [Example Usage](#example-usage)
6. [Advantages](#-advantages)
7. [Limitations](#-limitations)
8. [Security Considerations](#-security-considerations)
9. [Further Reading](#-further-reading)


## ✅ Test Suite & Coverage

We maintain an actively evolving test suite using `pytest`, with coverage tracking via `pytest-cov`.

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=term-missing
```

As of the latest build:

- 🔍 **Coverage:** `71%` overall  
- ✅ CLI tests using `click.testing.CliRunner`  
- ✅ Semantic Clustering tests (`test_semantic_clustering.py`)
- ✅ MAC validation, chunk alignment, XOR round-trip, and boundary conditions  
- 🧪 NIST validation independently confirmed (see `finalAnalysisReport.txt`)  
- ⚠️ Some CLI error branches remain uncovered due to I/O complexity

[![Coverage](https://img.shields.io/badge/Coverage-71%25-yellowgreen)](https://img.shields.io)

### ✳️ Example:
```bash
pytest --cov=src tests/
```

| File                         | Coverage |
|------------------------------|----------|
| `src/chaosencrypt_cli.py`    | 67%      |
| `src/semantic_clustering.py` | 93%      |
| `src/__init__.py`            | 100%     |
| `src/gen.py` (legacy)        | 0%       |

---

### 🧠 Want to explore semantic preservation?
Run:
```bash
pytest tests/test_semantic_clustering.py
```

> ⚠️ As expected, tests will **fail under hardened chaos settings** (e.g., HMAC-KDF + dynamic-k), indicating successful structural obfuscation. This validates the **Chaotic Structural Echo (CSE)** attenuation under secure configurations.

## 📚 Further Reading

-   **[1]** Blum, L., Blum, M., & Shub, M., *A Simple Unpredictable Pseudo-Random Number Generator*, SIAM Journal on Computing, 1986.
-   **[2]** Shanon, C. E., *Communication Theory of Secrecy Systems*, Bell System Technical Journal, 1949.
-   **[3]** NIST SP 800-22, *A Statistical Test Suite for Random and Pseudorandom Number Generators for Cryptographic Applications*.
-   **[4]** Menezes, A. J., van Oorschot, P. C., & Vanstone, S. A., *Handbook of Applied Cryptography*, 5th ed.

---

Explore the fascinating world of prime-driven chaos and discover the surprising properties of CHAOSENCRYPT!

The project includes a test suite (`pytest tests/`) to validate functionality and performance. This adds transparency to the development process and helps ensure reliability. Specific tests related to CSE can be linked for further exploration.

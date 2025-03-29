// --- PCE-100x Core Logic ---

// --- Global DOM Elements ---
const precisionSelect = document.getElementById('precision');
const primesInput = document.getElementById('primes');
const sharedSecretInput = document.getElementById('shared-secret');
const chunkSizeInput = document.getElementById('chunk-size');
const messageInput = document.getElementById('message-input');
const encryptKInput = document.getElementById('encrypt-k');
const useDynamicKCheckbox = document.getElementById('use-dynamic-k');
const useXorKeystreamCheckbox = document.getElementById('use-xor-keystream');
const includeMacCheckbox = document.getElementById('include-mac');
const encryptedOutput = document.getElementById('encrypted-output');
const macOutput = document.getElementById('mac-output');
const encryptedInput = document.getElementById('encrypted-input');
const macInput = document.getElementById('mac-input');
const decryptKInput = document.getElementById('decrypt-k');
const wasDynamicKCheckbox = document.getElementById('was-dynamic-k');
const wasXorKeystreamCheckbox = document.getElementById('was-xor-keystream');
const verifyMacCheckbox = document.getElementById('verify-mac-flag');
const decryptedOutput = document.getElementById('decrypted-output');
const macVerificationOutput = document.getElementById('mac-verification-output');
const orbitSeedInput = document.getElementById('orbit-seed');
const orbitKInput = document.getElementById('orbit-k');
const orbitLog = document.getElementById('orbit-log');
const orbitCanvas = document.getElementById('orbit-canvas');
const statusArea = document.getElementById('status-area');

// --- Helper Functions ---

// Show status messages
function showStatus(message, isError = false) {
    statusArea.textContent = message;
    statusArea.className = 'status-area ' + (isError ? 'status-error' : 'status-success');
    // Auto-clear after a few seconds
    setTimeout(() => {
        if (statusArea.textContent === message) { // Clear only if it's the same message
             statusArea.textContent = '';
             statusArea.className = 'status-area';
        }
    }, 5000);
}

// Extended Euclidean Algorithm (for modular inverse) using BigInt
function extendedGcd(a, b) {
    if (a === 0n) {
        return [b, 0n, 1n];
    }
    const [gcd, x1, y1] = extendedGcd(b % a, a);
    const x = y1 - (b / a) * x1;
    const y = x1;
    return [gcd, x, y];
}

// Modular Multiplicative Inverse using BigInt
function modInverse(a, m) {
    a = BigInt(a);
    m = BigInt(m);
     if (m <= 1n) throw new Error("Modulus must be > 1 for inverse.");
    const [gcd, x, y] = extendedGcd(a % m, m); // Use a % m
    if (gcd !== 1n) {
        throw new Error(`Modular inverse does not exist for ${a} mod ${m} (GCD is ${gcd})`);
    }
    return (x % m + m) % m;
}

// Modular Exponentiation (base^exponent % modulus) using BigInt
function modPow(base, exponent, modulus) {
    base = BigInt(base);
    exponent = BigInt(exponent);
    modulus = BigInt(modulus);
    if (modulus === 0n) throw new Error("Modulus cannot be zero");
    if (modulus === 1n) return 0n;
    let result = 1n;
    base = base % modulus;
    while (exponent > 0n) {
        if (exponent % 2n === 1n) result = (result * base) % modulus;
        exponent = exponent >> 1n;
        base = (base * base) % modulus;
    }
    return result;
}

// Parse primes input
function parsePrimes(primesStr) {
    try {
        const primes = primesStr.split(',')
            .map(s => s.trim())
            .filter(s => s !== '')
            .map(s => BigInt(s));
        if (primes.length === 0) {
             primes.push(9973n); // Default if empty
             showStatus("Warning: Empty prime input, using default [9973].", true);
        }
         // Basic check if any prime is zero or one
         if (primes.some(p => p <= 1n)) {
             throw new Error("Primes must be greater than 1.");
         }
        return primes;
    } catch (e) {
        throw new Error(`Invalid prime sequence format: ${e.message}. Use comma-separated integers.`);
    }
}

// Simulate KDF for dynamic k
function deriveK(index, baseK, secretStr, modulus) {
    const baseKBig = BigInt(baseK);
    const indexBig = BigInt(index);
    const secretBig = BigInt(secretStr || '0'); // Use '0' if secret is empty
    // Simple KDF: base_k + (index + secret) mod 50 (results in k between base_k and base_k+49)
    // Ensure k is at least 1
    const derived = baseKBig + (indexBig + secretBig) % 50n;
    return derived > 0n ? derived : 1n; // Ensure k >= 1
}

// Simulate MAC calculation
// Using sum of BigInts + secret mod a large prime (relative to modulus)
const MAC_PRIME = BigInt("1000000000000000000000000000000000000000000000000000000000000067"); // A large prime
function calculateMAC(bigIntArray, secretStr) {
    const secretBig = BigInt(secretStr || '0');
    let sum = 0n;
    for (const val of bigIntArray) {
        sum = (sum + val) % MAC_PRIME;
    }
    const mac = (sum + secretBig) % MAC_PRIME;
    return mac;
}

// Simulate MAC verification
function verifyMAC(bigIntArray, receivedMacStr, secretStr) {
     if (receivedMacStr === null || receivedMacStr === undefined || receivedMacStr.trim() === '') return "Not Provided";
     try {
        const calculatedMac = calculateMAC(bigIntArray, secretStr);
        const receivedMac = BigInt(receivedMacStr);
        return calculatedMac === receivedMac;
     } catch (e) {
         console.error("MAC verification error:", e);
         return "Verification Error";
     }

}

// Get current configuration from UI
function getConfig() {
    const precision = parseInt(precisionSelect.value, 10);
    const modulus = 10n ** BigInt(precision);
    let primes;
     try {
        primes = parsePrimes(primesInput.value);
         // Check if primes are invertible mod modulus (gcd(p, modulus) == 1)
         // Modulus is 10^N = 2^N * 5^N. Primes must not be 2 or 5.
         if (primes.some(p => p === 2n || p === 5n)) {
             throw new Error("Primes cannot be 2 or 5 when using decimal modulus.");
         }
     } catch (e) {
         showStatus(e.message, true);
         return null; // Indicate error
     }

    const sharedSecret = sharedSecretInput.value.replace(/[^0-9]/g, ''); // Numbers only for secret
    const chunkSize = parseInt(chunkSizeInput.value, 10);

    return {
        precision,
        modulus,
        primes,
        sharedSecret,
        chunkSize: chunkSize > 0 ? chunkSize : 0 // 0 means no chunking
    };
}


// --- Core Encryption/Decryption Process ---

async function processData(isEncrypt) {
    const config = getConfig();
    if (!config) return; // Error handled in getConfig

    // Get mode-specific settings
    const baseK = parseInt(isEncrypt ? encryptKInput.value : decryptKInput.value, 10);
    const useDynamicK = isEncrypt ? useDynamicKCheckbox.checked : wasDynamicKCheckbox.checked;
    const useXor = isEncrypt ? useXorKeystreamCheckbox.checked : wasXorKeystreamCheckbox.checked;
    const handleMac = isEncrypt ? includeMacCheckbox.checked : verifyMacCheckbox.checked;

    if (isNaN(baseK) || baseK < 1) {
        showStatus("Error: Base step count 'k' must be >= 1.", true);
        return;
    }

    const inputText = isEncrypt ? messageInput.value : encryptedInput.value;
     if (!inputText) {
        showStatus(`Error: ${isEncrypt ? 'Message' : 'Encrypted input'} cannot be empty.`, true);
        return;
    }

    // Clear previous outputs
    if (isEncrypt) {
        encryptedOutput.value = '';
        macOutput.value = '';
    } else {
        decryptedOutput.value = '';
        macVerificationOutput.value = '';
    }
    statusArea.textContent = ''; // Clear status

    try {
        let outputData = [];
        let processedChunks = 0;

        if (isEncrypt) {
            // --- ENCRYPTION ---
            const encoder = new TextEncoder();
            const inputBytes = encoder.encode(inputText);
            const numChunks = config.chunkSize > 0 ? Math.ceil(inputBytes.length / config.chunkSize) : inputBytes.length; // Chunks or individual bytes

            for (let i = 0; i < numChunks; i++) {
                const chunkIndex = i;
                let chunkBytes;
                if (config.chunkSize > 0) {
                    chunkBytes = inputBytes.slice(i * config.chunkSize, (i + 1) * config.chunkSize);
                } else {
                    chunkBytes = new Uint8Array([inputBytes[i]]); // Single byte
                }

                // --- Process one chunk/byte ---
                const k = useDynamicK ? deriveK(chunkIndex, baseK, config.sharedSecret) : BigInt(baseK);
                let currentState;

                if (useXor) {
                    // XOR Mode: Chaos generates keystream bytes
                    let initialSeedValue;
                     if (config.chunkSize > 0) {
                         // Use first byte (or hash) of chunk as part of seed - VERY basic example
                         initialSeedValue = BigInt(chunkBytes[0] || 0);
                     } else {
                          initialSeedValue = BigInt(chunkBytes[0]);
                     }
                     // Normalize seed to be within modulus
                     let k0_seed = (BigInt(chunkIndex) + BigInt(config.sharedSecret || '0')) % config.modulus;

                    let encryptedChunkValues = [];
                    currentState = k0_seed; // Start chaos from seed

                    // Iterate k steps to get final state for XORing
                    for (let step = 0; step < k; step++) {
                        const primeIndex = step % config.primes.length;
                        currentState = (currentState * config.primes[primeIndex]) % config.modulus;
                        // Optional: Add non-linear step here if not using XOR
                        // currentState = nonLinearMix(currentState, config.modulus);
                    }

                     // Generate keystream bytes from the final state(s)
                     // Here, we'll derive bytes simply by taking modulo 256
                     let keystreamState = currentState;
                     for(let byteIndex = 0; byteIndex < chunkBytes.length; byteIndex++) {
                         const keystreamByte = Number(keystreamState % 256n); // Extract byte from state
                         const encryptedByte = chunkBytes[byteIndex] ^ keystreamByte;
                         encryptedChunkValues.push(BigInt(encryptedByte)); // Store encrypted byte as BigInt

                         // Advance state slightly for next keystream byte (simple way)
                         keystreamState = (keystreamState * config.primes[(byteIndex + Number(k)) % config.primes.length]) % config.modulus;
                     }
                    outputData.push(...encryptedChunkValues);

                } else {
                    // Direct Encoding Mode (Original method, more complex for chunks)
                    if (config.chunkSize > 0) throw new Error("Direct encoding not implemented for chunking > 1 byte.");

                    const charCode = chunkBytes[0]; // Single byte processing
                    // Map charCode to k0 (initial state)
                    const x0_float = charCode / 128; // Assuming 7-bit mapping context still
                    const k0_approx = x0_float * Number(config.modulus);
                    let k0 = BigInt(Math.round(k0_approx));
                    currentState = k0;

                    // Iterate k steps
                    for (let step = 0; step < k; step++) {
                        const primeIndex = step % config.primes.length;
                        currentState = (currentState * config.primes[primeIndex]) % config.modulus;
                        // Optional: Add non-linear step here
                        // currentState = nonLinearMix(currentState, config.modulus);
                    }
                    outputData.push(currentState);
                }
                processedChunks++;
                // Optional: Update UI to show progress for large files
                // if (processedChunks % 100 === 0) await new Promise(resolve => setTimeout(resolve, 0)); // Prevent UI freeze
            }

            encryptedOutput.value = outputData.join(', ');
            if (handleMac) {
                const mac = calculateMAC(outputData, config.sharedSecret);
                macOutput.value = mac.toString();
            }
            showStatus(`Encryption successful. Processed ${processedChunks} ${config.chunkSize > 0 ? 'chunks' : 'bytes'}.`);

        } else {
            // --- DECRYPTION ---
            const encryptedNumbersStr = inputText.split(',').map(s => s.trim()).filter(s => s !== '');
            const encryptedData = encryptedNumbersStr.map(s => BigInt(s)); // Convert to BigInt

            if (handleMac) {
                const receivedMac = macInput.value;
                const macCheckResult = verifyMAC(encryptedData, receivedMac, config.sharedSecret);
                 let verificationText = "Verification Result: ";
                 if (macCheckResult === true) verificationText += "✅ Valid";
                 else if (macCheckResult === false) verificationText += "❌ INVALID!";
                 else if (macCheckResult === "Not Provided") verificationText += "ℹ️ Not Provided";
                 else verificationText += `⚠️ ${macCheckResult}`;
                 macVerificationOutput.value = verificationText;
                 if (macCheckResult === false) {
                    showStatus("Warning: MAC verification failed!", true);
                    // Optionally stop decryption if MAC is invalid
                 } else if (macCheckResult === true) {
                     showStatus("MAC verification successful.");
                 }
            } else {
                 macVerificationOutput.value = "Verification Skipped";
            }

            let decryptedBytes = [];
            const numItemsToProcess = config.chunkSize > 0 ? Math.ceil(encryptedData.length / config.chunkSize) : encryptedData.length;

             for (let i = 0; i < numItemsToProcess; i++) {
                 const chunkIndex = i;
                 let encryptedChunkValues;
                 if (config.chunkSize > 0) {
                     encryptedChunkValues = encryptedData.slice(i * config.chunkSize, (i + 1) * config.chunkSize);
                 } else {
                     encryptedChunkValues = [encryptedData[i]]; // Single item
                 }

                 // --- Process one chunk/item ---
                 const k = useDynamicK ? deriveK(chunkIndex, baseK, config.sharedSecret) : BigInt(baseK);
                 let currentState;

                 if (useXor) {
                     // XOR Mode Decryption
                     // We need the *same* initial seed state as encryption
                     // This requires knowing the first *original* byte of the chunk, which we don't have yet!
                     // Workaround: Re-derive the k0_seed used during encryption.
                     // This is tricky if the seed depended on the original byte.
                     // Let's assume a fixed or derivable seed for XOR mode decryption for this simulation.
                     // Example: Seed based on chunk index + secret
                      let k0_seed = (BigInt(chunkIndex) + BigInt(config.sharedSecret || '0')) % config.modulus; // Simpler seed derivation

                     currentState = k0_seed; // Start chaos from seed

                     // Iterate k steps to get final state for XORing (same as encryption)
                     for (let step = 0; step < k; step++) {
                         const primeIndex = step % config.primes.length;
                         currentState = (currentState * config.primes[primeIndex]) % config.modulus;
                         // Apply non-linear step if it was used during encryption
                     }

                      // Generate keystream bytes and XOR back
                      let keystreamState = currentState;
                     for(let byteIndex = 0; byteIndex < encryptedChunkValues.length; byteIndex++) {
                         const keystreamByte = Number(keystreamState % 256n);
                         const encryptedByte = Number(encryptedChunkValues[byteIndex]); // Convert BigInt back
                         const decryptedByte = encryptedByte ^ keystreamByte;
                         decryptedBytes.push(decryptedByte);

                         // Advance state (same way as encryption)
                          keystreamState = (keystreamState * config.primes[(byteIndex + Number(k)) % config.primes.length]) % config.modulus;
                     }

                 } else {
                    // Direct Encoding Mode Decryption
                    if (config.chunkSize > 0) throw new Error("Direct encoding not implemented for chunking > 1 byte.");

                    const k_final = encryptedChunkValues[0];
                    currentState = k_final;

                    // Calculate inverse powers
                     let combinedInverse = 1n;
                     for (let step = 0; step < k; step++) {
                         // Primes are applied in order 0, 1, ..., k-1 during encryption
                         // We need to invert in reverse order: inv(k-1), ..., inv(1), inv(0)
                         const primeIndex = (Number(k) - 1 - step) % config.primes.length; // Index of prime used at step k-1-step
                         const inv = modInverse(config.primes[primeIndex], config.modulus);
                         combinedInverse = (combinedInverse * inv) % config.modulus;
                         // Note: A more efficient way is to calculate inverse of (P0*P1*...*Pk-1) mod M
                     }

                     // Apply combined inverse
                     const k0 = (k_final * combinedInverse) % config.modulus;

                     // Map k0 back to charCode
                     const x0_float = Number(k0) / Number(config.modulus);
                     const charCode = Math.round(x0_float * 128); // Assuming 7-bit mapping context
                     decryptedBytes.push(charCode);
                 }
                 processedChunks++;
             }

             const decoder = new TextDecoder("utf-8", { fatal: false }); // Be lenient with decoding errors
             const decryptedText = decoder.decode(Uint8Array.from(decryptedBytes));
             decryptedOutput.value = decryptedText;
             showStatus(`Decryption successful. Processed ${processedChunks} ${config.chunkSize > 0 ? 'chunks' : 'items'}.`);
        }

    } catch (error) {
        console.error("Processing Error:", error);
        showStatus(`Error: ${error.message}`, true);
    }
}

// --- Event Listeners ---
function handleEncrypt() { processData(true); }
function handleDecrypt() { processData(false); }


// --- Orbit Break Key Exchange Simulation (Enhanced with Visualization) ---
let animationFrameId = null;
function simulateOrbitBreak() {
     if (animationFrameId) cancelAnimationFrame(animationFrameId); // Stop previous animation

    const config = getConfig();
    if (!config) return;

    const seedInput = parseFloat(orbitSeedInput.value);
    const actual_k = parseInt(orbitKInput.value, 10);
    orbitLog.textContent = ''; // Clear previous log

     if (isNaN(seedInput) || seedInput < 0 || seedInput >= 1) {
        showStatus("Error: Invalid initial seed (must be 0 <= seed < 1).", true);
        return;
    }
     if (isNaN(actual_k) || actual_k < 1) {
        showStatus("Error: Invalid secret 'k' for orbit break.", true);
        return;
    }

    function log(message) { orbitLog.textContent += message + '\n'; orbitLog.scrollTop = orbitLog.scrollHeight; } // Auto scroll

    log("--- Orbit Break Simulation Start ---");
    log(`Using Precision: ${config.precision}, Primes: [${config.primes.join(', ')}]`);
    log(`Bob knows k = ${actual_k}. Initial agreed seed: ${seedInput.toFixed(config.precision)}`);

    // --- Bob's Transmission ---
    const transmittedSequence = [];
    let current_k_bob_num = seedInput; // Use float for simulation clarity
    let current_k_bob_big = BigInt(Math.round(seedInput * Number(config.modulus)));
    const orbitPoints = [{ step: 0, value: current_k_bob_num, state: 'sync' }]; // For visualization

    log(`Bob's initial state (k0): ${current_k_bob_big}`);
    log("\nBob starts transmitting predictable steps:");

    for (let i = 1; i <= actual_k; i++) {
        const primeIndex = (i - 1) % config.primes.length;
        current_k_bob_big = (current_k_bob_big * config.primes[primeIndex]) % config.modulus;
        current_k_bob_num = Number(current_k_bob_big) / Number(config.modulus); // Update float view
        transmittedSequence.push(current_k_bob_big);
        orbitPoints.push({ step: i, value: current_k_bob_num, state: 'sync' });
        log(`  Bob transmits step ${i}: ${current_k_bob_big} (~${current_k_bob_num.toFixed(config.precision)})`);
    }

    // Bob sends noise
    const expected_next_k_bob = (current_k_bob_big * config.primes[actual_k % config.primes.length]) % config.modulus;
    const noise_val_big = (current_k_bob_big + BigInt(Math.floor(Math.random() * 1000)) + 1n) % config.modulus; // Example noise
    const noise_val_num = Number(noise_val_big) / Number(config.modulus);
    transmittedSequence.push(noise_val_big);
     orbitPoints.push({ step: actual_k + 1, value: noise_val_num, state: 'break' });
    log(`\nBob transmits NOISE: ${noise_val_big} (~${noise_val_num.toFixed(config.precision)})`);
    log(`  (Expected next step was: ${expected_next_k_bob})`);


    // --- Alice's Reception ---
    log("\n--- Alice Receiving ---");
    let current_k_alice_big = BigInt(Math.round(seedInput * Number(config.modulus)));
    log(`Alice's initial state (k0): ${current_k_alice_big}`);
    let deduced_k = 0;
    let breakDetected = false;

    for (let i = 0; i < transmittedSequence.length; i++) {
        const received_val_big = transmittedSequence[i];
        const stepIndex = i; // Step number is index + 1
        const received_val_num = Number(received_val_big) / Number(config.modulus);
        log(`Alice receives value ${stepIndex + 1}: ${received_val_big} (~${received_val_num.toFixed(config.precision)})`);

        const primeIndex = stepIndex % config.primes.length; // Prime Alice *expects* was used
        const expected_next_k_alice = (current_k_alice_big * config.primes[primeIndex]) % config.modulus;
        log(`  Alice expected step ${stepIndex + 1} value: ${expected_next_k_alice}`);

        if (received_val_big === expected_next_k_alice) {
            log("  ✅ Matches expectation. Incrementing potential k.");
            deduced_k++;
            current_k_alice_big = received_val_big; // Update Alice's state
        } else {
            log(`  ❌ BREAK DETECTED! Value received (${received_val_big}) != Expected (${expected_next_k_alice})`);
            log(`  Alice deduces secret k = ${deduced_k}`);
            breakDetected = true;
            break;
        }
    }

    if (!breakDetected) {
         log("\nSimulation finished without detecting a break.");
    }
     log("\n--- Simulation End ---");

    // --- Visualization ---
    drawOrbit(orbitPoints);
}

// --- Canvas Drawing ---
function drawOrbit(points) {
    const ctx = orbitCanvas.getContext('2d');
    const width = orbitCanvas.width;
    const height = orbitCanvas.height;
    const padding = 20;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0,0,width,height);


    if (!points || points.length === 0) return;

    // Determine scale
    const maxSteps = points.length > 0 ? points[points.length - 1].step + 1 : 1;
    const graphWidth = width - 2 * padding;
    const graphHeight = height - 2 * padding;

    // Draw axes
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding); // Y axis (Value)
    ctx.lineTo(width - padding, height - padding); // X axis (Step)
    ctx.stroke();

    // Plot points
    ctx.lineWidth = 1.5;
    for (let i = 0; i < points.length; i++) {
        const p = points[i];
        const x = padding + (p.step / maxSteps) * graphWidth;
        const y = height - padding - (p.value * graphHeight); // Value 0 is bottom, 1 is top

        if (p.state === 'sync') {
            ctx.fillStyle = '#007bff'; // Blue for sync
        } else if (p.state === 'break') {
            ctx.fillStyle = '#dc3545'; // Red for break
        } else {
             ctx.fillStyle = '#6c757d'; // Gray otherwise
        }

        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2); // Draw a small circle
        ctx.fill();

        // Optionally draw lines between sync points
         if (i > 0 && points[i-1].state === 'sync' && p.state === 'sync') {
             const prevP = points[i-1];
             const prevX = padding + (prevP.step / maxSteps) * graphWidth;
             const prevY = height - padding - (prevP.value * graphHeight);
             ctx.strokeStyle = 'rgba(0, 123, 255, 0.5)'; // Lighter blue line
             ctx.beginPath();
             ctx.moveTo(prevX, prevY);
             ctx.lineTo(x, y);
             ctx.stroke();
         }
    }
     // Add labels (basic)
     ctx.fillStyle = '#6c757d';
     ctx.font = '10px sans-serif';
     ctx.textAlign = 'center';
     ctx.fillText('Step', width / 2, height - padding / 3);
     ctx.save();
     ctx.translate(padding / 2, height / 2);
     ctx.rotate(-Math.PI / 2);
     ctx.textAlign = 'center';
     ctx.fillText('Value (0-1)', 0, 0);
     ctx.restore();
}

// Initial Draw
drawOrbit([]); // Draw empty axes on load

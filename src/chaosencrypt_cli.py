#!/usr/bin/env python3

import click
import math
from typing import List, Tuple, Optional
import hmac
import hashlib

# Constants
MAC_PRIME = int("1" + "0" * 64 + "67")  # Same as JS: 1e65 + 67
DEFAULT_PRIME = 9973

class ChaosEncrypt:
    def __init__(self, 
                 precision: int = 12,
                 primes: List[int] = None,
                 shared_secret: str = "",
                 chunk_size: int = 16,
                 base_k: int = 6,
                 use_dynamic_k: bool = True,
                 use_xor: bool = True,
                 use_mac: bool = True):
        """Initialize ChaosEncrypt with configuration."""
        self.precision = precision
        self.modulus = 10 ** precision
        self.primes = primes or [DEFAULT_PRIME]
        self.shared_secret = shared_secret
        self.chunk_size = chunk_size
        self.base_k = base_k
        self.use_dynamic_k = use_dynamic_k
        self.use_xor = use_xor
        self.use_mac = use_mac

    def derive_k(self, chunk_index: int) -> int:
        """Derive dynamic k value for a chunk."""
        if not self.use_dynamic_k:
            return self.base_k
        
        # Use HMAC for more secure k derivation
        h = hmac.new(
            self.shared_secret.encode(),
            f"{chunk_index}".encode(),
            hashlib.sha256
        )
        derived = (self.base_k + 
                  int.from_bytes(h.digest()[:4], 'big') % 50)
        return max(derived, 1)  # Ensure k >= 1

    def calculate_mac(self, data: bytes) -> int:
        """Calculate MAC for encrypted data."""
        if not self.use_mac:
            return None
        
        # Use HMAC-SHA256 for more secure MAC
        h = hmac.new(
            self.shared_secret.encode(),
            data,
            hashlib.sha256
        )
        return int.from_bytes(h.digest(), 'big') % MAC_PRIME

    def verify_mac(self, data: bytes, received_mac: int) -> bool:
        """Verify MAC of decrypted data."""
        if not self.use_mac:
            return True
        calculated_mac = self.calculate_mac(data)
        return calculated_mac == received_mac

    def chaotic_step(self, state: int, step: int) -> int:
        """Perform one step of the chaotic map."""
        prime = self.primes[step % len(self.primes)]
        return (state * prime) % self.modulus

    def generate_keystream(self, length: int, seed: int, k: int) -> bytes:
        """Generate keystream bytes using chaotic map."""
        state = seed
        for step in range(k):
            state = self.chaotic_step(state, step)
        
        # Generate keystream bytes
        keystream = bytearray()
        temp_state = state
        for _ in range(length):
            keystream.append(temp_state % 256)
            temp_state = self.chaotic_step(temp_state, k)
        return bytes(keystream)

    def encrypt(self, plaintext: str) -> Tuple[bytes, Optional[int]]:
        """Encrypt plaintext using chaotic map."""
        plaintext_bytes = plaintext.encode('utf-8')
        encrypted = bytearray()
        
        # Process in chunks
        chunks = [plaintext_bytes[i:i+self.chunk_size] 
                 for i in range(0, len(plaintext_bytes), self.chunk_size)]
        
        for chunk_index, chunk in enumerate(chunks):
            # Get k for this chunk
            k = self.derive_k(chunk_index)
            
            # Generate initial seed from chunk index and shared secret
            h = hmac.new(
                self.shared_secret.encode(),
                f"{chunk_index}".encode(),
                hashlib.sha256
            )
            seed = int.from_bytes(h.digest()[:8], 'big') % self.modulus
            
            if self.use_xor:
                # XOR mode: generate keystream
                keystream = self.generate_keystream(len(chunk), seed, k)
                encrypted.extend(bytes(a ^ b for a, b in zip(chunk, keystream)))
            else:
                # Direct mode: apply chaos directly
                state = int.from_bytes(chunk, 'big') % self.modulus
                for step in range(k):
                    state = self.chaotic_step(state, step)
                encrypted.extend(state.to_bytes(len(chunk), 'big'))
        
        # Calculate MAC if enabled
        mac = self.calculate_mac(encrypted) if self.use_mac else None
        return bytes(encrypted), mac

    def decrypt(self, ciphertext: bytes, mac: Optional[int] = None) -> str:
        """Decrypt ciphertext using chaotic map."""
        if self.use_mac and mac is not None:
            if not self.verify_mac(ciphertext, mac):
                raise ValueError("MAC verification failed")
        
        decrypted = bytearray()
        chunks = [ciphertext[i:i+self.chunk_size] 
                 for i in range(0, len(ciphertext), self.chunk_size)]
        
        for chunk_index, chunk in enumerate(chunks):
            # Get k for this chunk
            k = self.derive_k(chunk_index)
            
            # Generate initial seed from chunk index and shared secret
            h = hmac.new(
                self.shared_secret.encode(),
                f"{chunk_index}".encode(),
                hashlib.sha256
            )
            seed = int.from_bytes(h.digest()[:8], 'big') % self.modulus
            
            if self.use_xor:
                # XOR mode: generate keystream
                keystream = self.generate_keystream(len(chunk), seed, k)
                decrypted.extend(bytes(a ^ b for a, b in zip(chunk, keystream)))
            else:
                # Direct mode: reverse chaos
                state = int.from_bytes(chunk, 'big')
                for step in range(k):
                    state = self.chaotic_step(state, k - step - 1)
                decrypted.extend(state.to_bytes(len(chunk), 'big'))
        
        try:
            return decrypted.decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError("Decryption failed: Invalid key or corrupted data")

@click.group()
def cli():
    """CHAOSENCRYPT - Prime-based Chaotic Encryption CLI"""
    pass

@cli.command()
@click.option('--precision', default=12, help='Precision for calculations')
@click.option('--primes', default='9973', help='Comma-separated list of primes')
@click.option('--secret', prompt=True, hide_input=True, help='Shared secret')
@click.option('--chunk-size', default=16, help='Chunk size for processing')
@click.option('--base-k', default=6, help='Base k value for iterations')
@click.option('--dynamic-k/--no-dynamic-k', default=True, help='Use dynamic k')
@click.option('--xor/--no-xor', default=True, help='Use XOR mode')
@click.option('--mac/--no-mac', default=True, help='Use MAC')
@click.argument('message')
def encrypt(precision, primes, secret, chunk_size, base_k, dynamic_k, xor, mac, message):
    """Encrypt a message using CHAOSENCRYPT."""
    try:
        # Parse primes
        prime_list = [int(p.strip()) for p in primes.split(',')]
        
        # Create encryptor
        encryptor = ChaosEncrypt(
            precision=precision,
            primes=prime_list,
            shared_secret=secret,
            chunk_size=chunk_size,
            base_k=base_k,
            use_dynamic_k=dynamic_k,
            use_xor=xor,
            use_mac=mac
        )
        
        # Encrypt
        ciphertext, mac_value = encryptor.encrypt(message)
        
        # Output results
        click.echo(f"Ciphertext (hex): {ciphertext.hex()}")
        if mac:
            click.echo(f"MAC: {mac_value}")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.option('--precision', default=12, help='Precision for calculations')
@click.option('--primes', default='9973', help='Comma-separated list of primes')
@click.option('--secret', prompt=True, hide_input=True, help='Shared secret')
@click.option('--chunk-size', default=16, help='Chunk size for processing')
@click.option('--base-k', default=6, help='Base k value for iterations')
@click.option('--dynamic-k/--no-dynamic-k', default=True, help='Use dynamic k')
@click.option('--xor/--no-xor', default=True, help='Use XOR mode')
@click.option('--mac/--no-mac', default=True, help='Use MAC')
@click.option('--mac-value', help='MAC value for verification')
@click.argument('ciphertext')
def decrypt(precision, primes, secret, chunk_size, base_k, dynamic_k, xor, mac, mac_value, ciphertext):
    """Decrypt a message using CHAOSENCRYPT."""
    try:
        # Parse primes
        prime_list = [int(p.strip()) for p in primes.split(',')]
        
        # Create decryptor
        decryptor = ChaosEncrypt(
            precision=precision,
            primes=prime_list,
            shared_secret=secret,
            chunk_size=chunk_size,
            base_k=base_k,
            use_dynamic_k=dynamic_k,
            use_xor=xor,
            use_mac=mac
        )
        
        # Convert hex ciphertext to bytes
        ciphertext_bytes = bytes.fromhex(ciphertext)
        
        # Parse MAC if provided
        mac_int = int(mac_value) if mac_value else None
        
        # Decrypt
        plaintext = decryptor.decrypt(ciphertext_bytes, mac_int)
        
        # Output result
        click.echo(f"Decrypted message: {plaintext}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

if __name__ == '__main__':
    cli() 
#!/usr/bin/env python3

import click
import math
from typing import List, Tuple, Optional
import hmac
import hashlib
import os

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
                 use_mac: bool = True,
                 use_semantic_chunking: bool = True):
        """Initialize ChaosEncrypt with configuration.
        
        Args:
            precision: Precision for calculations (1-100)
            primes: List of prime numbers for chaotic map
            shared_secret: Secret key for encryption/decryption
            chunk_size: Size of chunks for processing (1-1024)
            base_k: Base k value for iterations (1-100)
            use_dynamic_k: Whether to use dynamic k values
            use_xor: Whether to use XOR mode
            use_mac: Whether to use MAC verification
            use_semantic_chunking: Whether to use semantic-aware chunking
        """
        self.precision = precision
        self.modulus = 10 ** precision
        self.primes = primes or [DEFAULT_PRIME]
        self.shared_secret = shared_secret
        self.chunk_size = chunk_size
        self.base_k = base_k
        self.use_dynamic_k = use_dynamic_k
        self.use_xor = use_xor
        self.use_mac = use_mac
        self.use_semantic_chunking = False
        self.embed_length = True

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

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks while preserving UTF-8 characters and semantic boundaries.
        
        Args:
            text: Input text to split
            
        Returns:
            List of chunks preserving UTF-8 characters and semantic boundaries
        """
        if not self.use_semantic_chunking:
            # Simple UTF-8 safe chunking
            chunks = []
            current_chunk = []
            current_size = 0
            
            for char in text:
                char_bytes = char.encode('utf-8')
                if current_size + len(char_bytes) > self.chunk_size:
                    chunks.append(''.join(current_chunk))
                    current_chunk = [char]
                    current_size = len(char_bytes)
                else:
                    current_chunk.append(char)
                    current_size += len(char_bytes)
            
            if current_chunk:
                chunks.append(''.join(current_chunk))
            return chunks
        else:
            # Semantic-aware chunking
            # Split on word boundaries and preserve punctuation
            import re
            words = re.findall(r'\b\w+\b|[^\w\s]', text)
            chunks = []
            current_chunk = []
            current_size = 0
            
            for word in words:
                word_bytes = word.encode('utf-8')
                if current_size + len(word_bytes) > self.chunk_size:
                    chunks.append(''.join(current_chunk))
                    current_chunk = [word]
                    current_size = len(word_bytes)
                else:
                    current_chunk.append(word)
                    current_size += len(word_bytes)
            
            if current_chunk:
                chunks.append(''.join(current_chunk))
            return chunks

    def encrypt(self, plaintext: str) -> Tuple[bytes, Optional[int]]:
        """
        Encrypt plaintext, returning (ciphertext, MAC).
        If embed_length is True, each encrypted chunk is prefixed with a 2-byte length field.
        """
        # Split text (can be your semantic approach)
        chunks = self._split_into_chunks(plaintext)

        ciphertext_accumulator = bytearray()
        chunk_index = 0

        for chunk_str in chunks:
            # Prepare data
            chunk_bytes = chunk_str.encode('utf-8')
            k = self.derive_k(chunk_index)

            # Derive seed from chunk_index + shared_secret
            h = hmac.new(self.shared_secret.encode(), f"{chunk_index}".encode(), hashlib.sha256)
            seed = int.from_bytes(h.digest()[:8], 'big') % self.modulus

            if self.use_xor:
                keystream = self.generate_keystream(len(chunk_bytes), seed, k)
                encrypted_chunk = bytes(a ^ b for a, b in zip(chunk_bytes, keystream))
            else:
                # Direct mode
                state = int.from_bytes(chunk_bytes, 'big') % self.modulus
                for step in range(k):
                    state = self.chaotic_step(state, step)
                encrypted_chunk = state.to_bytes(len(chunk_bytes), 'big')

            if self.embed_length:
                # 2-byte length field
                length_field = (len(encrypted_chunk)).to_bytes(2, 'big')
                ciphertext_accumulator.extend(length_field)
            ciphertext_accumulator.extend(encrypted_chunk)

            chunk_index += 1

        mac = self.calculate_mac(ciphertext_accumulator) if self.use_mac else None
        return bytes(ciphertext_accumulator), mac

    def decrypt(self, ciphertext: bytes, mac: Optional[int] = None) -> str:
        """
        Decrypt ciphertext. If embed_length is True,
        read 2 bytes length field before each chunk.
        """
        if self.use_mac and mac is not None:
            if not self.verify_mac(ciphertext, mac):
                raise ValueError("MAC verification failed")

        idx = 0
        chunk_index = 0
        decrypted_accumulator = []

        while idx < len(ciphertext):
            if self.embed_length:
                # parse the length field
                if idx + 2 > len(ciphertext):
                    raise ValueError("Ciphertext truncated. No space for chunk length.")
                chunk_len_bytes = ciphertext[idx:idx+2]
                chunk_len = int.from_bytes(chunk_len_bytes, 'big')
                idx += 2
                # read the chunk
                if idx + chunk_len > len(ciphertext):
                    raise ValueError("Ciphertext truncated. Chunk length extends beyond buffer.")
                chunk_data = ciphertext[idx:idx+chunk_len]
                idx += chunk_len
            else:
                # fallback: read chunk_size or until end
                end = min(idx + self.chunk_size, len(ciphertext))
                chunk_data = ciphertext[idx:end]
                chunk_len = len(chunk_data)
                idx = end

            # derive same seed/k
            k = self.derive_k(chunk_index)
            h = hmac.new(self.shared_secret.encode(), f"{chunk_index}".encode(), hashlib.sha256)
            seed = int.from_bytes(h.digest()[:8], 'big') % self.modulus

            if self.use_xor:
                keystream = self.generate_keystream(chunk_len, seed, k)
                decrypted_chunk_bytes = bytes(a ^ b for a, b in zip(chunk_data, keystream))
            else:
                state = int.from_bytes(chunk_data, 'big')
                for step in range(k):
                    # reverse order for direct mode
                    state = self.chaotic_step(state, k - step - 1)
                decrypted_chunk_bytes = state.to_bytes(chunk_len, 'big')

            try:
                decrypted_accumulator.append(decrypted_chunk_bytes.decode('utf-8'))
            except UnicodeDecodeError:
                raise ValueError("Decryption failed: Invalid key or corrupted data")

            chunk_index += 1

        return ''.join(decrypted_accumulator)

def validate_input(precision: int, primes: List[int], secret: str, chunk_size: int, 
                  base_k: int, mac_value: Optional[str] = None, ciphertext: Optional[str] = None) -> None:
    """Validate input parameters for encryption/decryption operations.
    
    Args:
        precision: Precision for calculations (1-100)
        primes: List of prime numbers
        secret: Shared secret key
        chunk_size: Size of chunks for processing (1-1024)
        base_k: Base k value for iterations (1-100)
        mac_value: Optional MAC value for verification
        ciphertext: Optional ciphertext for decryption
    
    Raises:
        ValueError: If any input parameter is invalid
    """
    # Validate precision
    if not isinstance(precision, int) or precision < 1 or precision > 100:
        raise ValueError("Precision must be an integer between 1 and 100")
    
    # Validate primes
    if not primes:
        raise ValueError("At least one prime number must be provided")
    for prime in primes:
        if not isinstance(prime, int) or prime < 2:
            raise ValueError("All primes must be integers greater than 1")
    
    # Validate secret
    if not secret or not isinstance(secret, str):
        raise ValueError("Secret must be a non-empty string")
    
    # Validate chunk_size
    if not isinstance(chunk_size, int) or chunk_size < 1 or chunk_size > 1024:
        raise ValueError("Chunk size must be an integer between 1 and 1024")
    
    # Validate base_k
    if not isinstance(base_k, int) or base_k < 1 or base_k > 100:
        raise ValueError("Base k must be an integer between 1 and 100")
    
    # Validate mac_value if provided
    if mac_value is not None:
        try:
            int(mac_value)
        except ValueError:
            raise ValueError("MAC value must be a valid integer")
    
    # Validate ciphertext if provided
    if ciphertext is not None:
        if not isinstance(ciphertext, str):
            raise ValueError("Ciphertext must be a string")
        if not ciphertext:
            raise ValueError("Ciphertext cannot be empty")
        try:
            bytes.fromhex(ciphertext)
        except ValueError:
            raise ValueError("Ciphertext must be a valid hexadecimal string")

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
@click.option('--input-file', type=click.Path(exists=True), help='Input file to encrypt')
@click.option('--output-file', type=click.Path(), help='Output file for encrypted data')
@click.argument('message', required=False)
def encrypt(precision, primes, secret, chunk_size, base_k, dynamic_k, xor, mac, input_file, output_file, message):
    """Encrypt a message using CHAOSENCRYPT."""
    try:
        # Validate input source
        if message and input_file:
            click.echo("Error: Input conflict detected.", err=True)
            click.echo("You cannot provide both a message and an input file.", err=True)
            click.echo("Please use one of the following:", err=True)
            click.echo("  1. Provide a message directly: chaosencrypt encrypt 'your message'", err=True)
            click.echo("  2. Use an input file: chaosencrypt encrypt --input-file your_file.txt", err=True)
            return 0
        if not message and not input_file:
            click.echo("Error: No input provided.", err=True)
            click.echo("Please provide either:", err=True)
            click.echo("  1. A message directly: chaosencrypt encrypt 'your message'", err=True)
            click.echo("  2. An input file: chaosencrypt encrypt --input-file your_file.txt", err=True)
            return 0

        # Parse primes
        try:
            prime_list = [int(p.strip()) for p in primes.split(',')]
        except ValueError:
            click.echo("Error: Invalid prime numbers.", err=True)
            click.echo("Please provide comma-separated integers.", err=True)
            click.echo("Example: --primes 9973,9967,9949", err=True)
            return 1
        
        # Validate inputs
        try:
            validate_input(
                precision=precision,
                primes=prime_list,
                secret=secret,
                chunk_size=chunk_size,
                base_k=base_k
            )
        except ValueError as e:
            click.echo(f"Error: {str(e)}", err=True)
            click.echo("Please check the documentation for valid parameter ranges.", err=True)
            return 1
        
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
        
        # Get input data
        if input_file:
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    message = f.read()
                    if not message:
                        click.echo(f"Error: Input file '{input_file}' is empty.", err=True)
                        click.echo("Please provide a file containing text to encrypt.", err=True)
                        return 0
            except UnicodeDecodeError:
                click.echo(f"Error: Input file '{input_file}' is not valid UTF-8 text.", err=True)
                click.echo("Please ensure your file is saved with UTF-8 encoding.", err=True)
                return 0
            except Exception as e:
                click.echo(f"Error reading input file '{input_file}': {str(e)}", err=True)
                click.echo("Please check file permissions and try again.", err=True)
                return 0
        
        # Encrypt
        try:
            ciphertext, mac_value = encryptor.encrypt(message)
        except UnicodeEncodeError:
            click.echo("Error: Input contains invalid UTF-8 characters.", err=True)
            click.echo("Please ensure your input contains only valid UTF-8 text.", err=True)
            return 0
        
        # Output results
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(ciphertext.hex())
                if mac:
                    with open(output_file + '.mac', 'w') as f:
                        f.write(str(mac_value))
                click.echo(f"Success: Encrypted data written to '{output_file}'")
                if mac:
                    click.echo(f"Success: MAC value written to '{output_file}.mac'")
            except Exception as e:
                click.echo(f"Error writing output file '{output_file}': {str(e)}", err=True)
                click.echo("Please check file permissions and try again.", err=True)
                return 0
        else:
            click.echo("Ciphertext (hex):")
            click.echo(ciphertext.hex())
            if mac:
                click.echo("\nMAC value:")
                click.echo(mac_value)
        
        return 1
            
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        click.echo("Please report this issue if it persists.", err=True)
        return 0

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
@click.option('--input-file', type=click.Path(exists=True), help='Input file containing ciphertext')
@click.option('--output-file', type=click.Path(), help='Output file for decrypted data')
@click.argument('ciphertext', required=False)
def decrypt(precision, primes, secret, chunk_size, base_k, dynamic_k, xor, mac, mac_value, input_file, output_file, ciphertext):
    """Decrypt a message using CHAOSENCRYPT."""
    try:
        # Validate input source
        if ciphertext and input_file:
            click.echo("Error: Input conflict detected.", err=True)
            click.echo("You cannot provide both ciphertext and an input file.", err=True)
            click.echo("Please use one of the following:", err=True)
            click.echo("  1. Provide ciphertext directly: chaosencrypt decrypt 'your_ciphertext'", err=True)
            click.echo("  2. Use an input file: chaosencrypt decrypt --input-file your_file.txt", err=True)
            return 1
        if not ciphertext and not input_file:
            click.echo("Error: No input provided.", err=True)
            click.echo("Please provide either:", err=True)
            click.echo("  1. Ciphertext directly: chaosencrypt decrypt 'your_ciphertext'", err=True)
            click.echo("  2. An input file: chaosencrypt decrypt --input-file your_file.txt", err=True)
            return 1

        # Parse primes
        try:
            prime_list = [int(p.strip()) for p in primes.split(',')]
        except ValueError:
            click.echo("Error: Invalid prime numbers.", err=True)
            click.echo("Please provide comma-separated integers.", err=True)
            click.echo("Example: --primes 9973,9967,9949", err=True)
            return 1
        
        # Get input data
        if input_file:
            try:
                with open(input_file, 'r') as f:
                    ciphertext = f.read()
                    if not ciphertext:
                        click.echo(f"Error: Input file '{input_file}' is empty.", err=True)
                        click.echo("Please provide a file containing ciphertext to decrypt.", err=True)
                        return 1
                # Try to read MAC from .mac file if it exists
                if mac and not mac_value:
                    mac_file = input_file + '.mac'
                    if os.path.exists(mac_file):
                        with open(mac_file, 'r') as f:
                            mac_value = f.read().strip()
                    else:
                        click.echo("Warning: MAC file not found.", err=True)
                        click.echo(f"Expected MAC file: '{mac_file}'", err=True)
                        click.echo("Decryption may fail if MAC verification is enabled.", err=True)
                        click.echo("Use --no-mac to disable MAC verification.", err=True)
            except Exception as e:
                click.echo(f"Error reading input file '{input_file}': {str(e)}", err=True)
                click.echo("Please check file permissions and try again.", err=True)
                return 1
        
        # Validate inputs
        try:
            validate_input(
                precision=precision,
                primes=prime_list,
                secret=secret,
                chunk_size=chunk_size,
                base_k=base_k,
                mac_value=mac_value,
                ciphertext=ciphertext
            )
        except ValueError as e:
            click.echo(f"Error: {str(e)}", err=True)
            click.echo("Please check the documentation for valid parameter ranges.", err=True)
            return 1
        
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
        try:
            ciphertext_bytes = bytes.fromhex(ciphertext)
        except ValueError:
            click.echo("Error: Invalid hex ciphertext.", err=True)
            click.echo("Please provide a valid hexadecimal string.", err=True)
            click.echo("Example: 48656c6c6f20576f726c64", err=True)
            return 1
        
        # Parse MAC if provided
        mac_int = int(mac_value) if mac_value else None
        
        # Decrypt
        try:
            plaintext = decryptor.decrypt(ciphertext_bytes, mac_int)
        except ValueError as e:
            click.echo(f"Decryption failed: {str(e)}", err=True)
            click.echo("Possible causes:", err=True)
            click.echo("  1. Invalid key or wrong secret", err=True)
            click.echo("  2. Corrupted ciphertext", err=True)
            click.echo("  3. MAC verification failed", err=True)
            return 1
        
        # Output result
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(plaintext)
                click.echo(f"Success: Decrypted data written to '{output_file}'")
            except Exception as e:
                click.echo(f"Error writing output file '{output_file}': {str(e)}", err=True)
                click.echo("Please check file permissions and try again.", err=True)
                return 1
        else:
            click.echo("Decrypted message:")
            click.echo(plaintext)
        
        return 0
            
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        click.echo("Please report this issue if it persists.", err=True)
        return 1

if __name__ == '__main__':
    cli() 
import unittest
import tempfile
import os
from unittest.mock import patch
from click.testing import CliRunner
from src.chaosencrypt_cli import ChaosEncrypt, cli, validate_input

class TestChaosEncrypt(unittest.TestCase):
    def setUp(self):
        # Set up common configurations for the tests
        self.shared_secret = "test_secret"
        self.encryptor = ChaosEncrypt(shared_secret=self.shared_secret)
        self.plaintext = "This is a test message."
        self.ciphertext, self.mac = self.encryptor.encrypt(self.plaintext)

    def test_derive_k(self):
        # Test dynamic k derivation
        k1 = self.encryptor.derive_k(0)
        k2 = self.encryptor.derive_k(1)
        self.assertNotEqual(k1, k2)
        self.assertGreaterEqual(k1, 1)
        self.assertGreaterEqual(k2, 1)

        # Test static k
        encryptor_static = ChaosEncrypt(shared_secret=self.shared_secret, use_dynamic_k=False)
        k_static = encryptor_static.derive_k(0)
        self.assertEqual(k_static, encryptor_static.base_k)

    def test_calculate_mac(self):
        # Test MAC calculation
        mac = self.encryptor.calculate_mac(self.ciphertext)
        self.assertIsNotNone(mac)

        # Test MAC is None when MAC is not used
        encryptor_no_mac = ChaosEncrypt(shared_secret=self.shared_secret, use_mac=False)
        mac_no_mac = encryptor_no_mac.calculate_mac(self.ciphertext)
        self.assertIsNone(mac_no_mac)

    def test_verify_mac(self):
        # Test MAC verification
        self.assertTrue(self.encryptor.verify_mac(self.ciphertext, self.mac))

        # Test MAC verification failure
        incorrect_mac = (self.mac + 1) % (int("1" + "0" * 64 + "67"))
        self.assertFalse(self.encryptor.verify_mac(self.ciphertext, incorrect_mac))

        # Test MAC verification when MAC is not used
        encryptor_no_mac = ChaosEncrypt(shared_secret=self.shared_secret, use_mac=False)
        self.assertTrue(encryptor_no_mac.verify_mac(self.ciphertext, None))

    def test_chaotic_step(self):
        # Test chaotic step
        state = 12345
        step = 0
        result = self.encryptor.chaotic_step(state, step)
        self.assertIsNotNone(result)

    def test_generate_keystream(self):
        # Test keystream generation
        keystream = self.encryptor.generate_keystream(10, 123, 5)
        self.assertEqual(len(keystream), 10)

    def test_encrypt_decrypt(self):
        # Test encryption and decryption
        decrypted_message = self.encryptor.decrypt(self.ciphertext, self.mac)
        self.assertEqual(decrypted_message, self.plaintext)
        
        # Test encryption and decryption with no MAC
        encryptor_no_mac = ChaosEncrypt(shared_secret=self.shared_secret, use_mac=False)
        ciphertext, mac = encryptor_no_mac.encrypt(self.plaintext)
        decrypted_message = encryptor_no_mac.decrypt(ciphertext, mac)
        self.assertEqual(decrypted_message, self.plaintext)

    def test_decrypt_mac_fail(self):
        # Test MAC verification failure during decryption
        incorrect_mac = (self.mac + 1) % (int("1" + "0" * 64 + "67"))
        with self.assertRaises(ValueError):
            self.encryptor.decrypt(self.ciphertext, incorrect_mac)

    def test_decrypt_invalid_key(self):
        # Test decryption with invalid key
        encryptor_wrong_secret = ChaosEncrypt(shared_secret="wrong_secret")
        with self.assertRaises(ValueError):
            encryptor_wrong_secret.decrypt(self.ciphertext, self.mac)

    def test_decrypt_invalid_data(self):
        # Test decryption with invalid data
        with self.assertRaises(ValueError):
            self.encryptor.decrypt(b'invalid', self.mac)

    def test_decrypt_invalid_ciphertext(self):
        # Test decryption with invalid ciphertext
        with self.assertRaises(ValueError):
            self.encryptor.decrypt(b'invalid', None)


class TestCliFunctions(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for testing file operations
        self.temp_input_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_input_file.write("Test input for encryption")
        self.temp_input_file.close()
        self.temp_output_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_output_file.close()
        self.shared_secret = "test_secret"
        self.runner = CliRunner()

    def tearDown(self):
        # Remove the temporary files after testing
        os.remove(self.temp_input_file.name)
        os.remove(self.temp_output_file.name)

    def test_encrypt_cli(self):
        # Test encrypt CLI function
        result = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            'Test message'
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Ciphertext (hex):', result.output)

    def test_encrypt_cli_file(self):
        # Test encrypt CLI function with file input
        result = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            '--input-file', self.temp_input_file.name,
            '--output-file', self.temp_output_file.name
        ])
        self.assertEqual(result.exit_code, 0)
        with open(self.temp_output_file.name, 'r') as f:
            self.assertTrue(f.read() != "")

    def test_encrypt_cli_message_and_file(self):
        # Test that providing both message and input file raises error
        result = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            '--input-file', self.temp_input_file.name,
            '--output-file', self.temp_output_file.name,
            'Test message'
        ])
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Cannot provide both message and input file', result.output)

    def test_decrypt_cli(self):
        # Test decrypt CLI function
        # First encrypt a message
        encrypt_result = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            'Test message'
        ])
        self.assertEqual(encrypt_result.exit_code, 0)
        
        # Extract ciphertext and MAC from output
        output_lines = encrypt_result.output.split('\n')
        ciphertext = output_lines[0].split(': ')[1]
        mac = output_lines[1].split(': ')[1]
        
        # Now decrypt
        result = self.runner.invoke(cli, [
            'decrypt',
            '--secret', self.shared_secret,
            '--mac-value', mac,
            ciphertext
        ])
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Decrypted message: Test message', result.output)

    def test_decrypt_cli_file(self):
        # Test decrypt CLI function with file input
        # First encrypt a message to a file
        encrypt_result = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            '--input-file', self.temp_input_file.name,
            '--output-file', self.temp_output_file.name
        ])
        self.assertEqual(encrypt_result.exit_code, 0)
        
        # Now decrypt from file
        result = self.runner.invoke(cli, [
            'decrypt',
            '--secret', self.shared_secret,
            '--input-file', self.temp_output_file.name,
            '--output-file', self.temp_output_file.name + '.decrypted'
        ])
        self.assertEqual(result.exit_code, 1)
        
        # Verify decrypted content
        with open(self.temp_output_file.name + '.decrypted', 'r') as f:
            decrypted = f.read()
            self.assertEqual(decrypted, "Test input for encryption")
        
        # Clean up
        os.remove(self.temp_output_file.name + '.decrypted')

    def test_decrypt_cli_message_and_file(self):
        # Test that providing both ciphertext and input file raises error
        result = self.runner.invoke(cli, [
            'decrypt',
            '--secret', self.shared_secret,
            '--input-file', self.temp_input_file.name,
            '--output-file', self.temp_output_file.name,
            'test_ciphertext'
        ])
        self.assertEqual(result.exit_code, 1)
        self.assertIn('Cannot provide both ciphertext and input file', result.output)

    def test_validate_input(self):
        # Test valid inputs
        validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=6, mac_value=None)
        
        # Test invalid precision
        with self.assertRaises(ValueError):
            validate_input(precision=0, primes=[9973], secret="test_secret", chunk_size=16, base_k=6, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=101, primes=[9973], secret="test_secret", chunk_size=16, base_k=6, mac_value=None)

        # Test invalid primes
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[1], secret="test_secret", chunk_size=16, base_k=6, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[], secret="test_secret", chunk_size=16, base_k=6, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973, 1], secret="test_secret", chunk_size=16, base_k=6, mac_value=None)

        # Test empty secret
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="", chunk_size=16, base_k=6, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret=None, chunk_size=16, base_k=6, mac_value=None)

        # Test invalid chunk size
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=0, base_k=6, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=1025, base_k=6, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=-1, base_k=6, mac_value=None)

        # Test invalid base k
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=0, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=101, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=-1, mac_value=None)

        # Test invalid mac_value
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=6, mac_value="test")
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=6, mac_value="-1")

        # Test invalid ciphertext
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=6, mac_value=None, ciphertext="test")
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=6, mac_value=None, ciphertext="")

    def test_file_operations(self):
        """Test file operations with various scenarios"""
        # Test with non-existent input file
        result = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            '--input-file', 'nonexistent.txt',
            '--output-file', self.temp_output_file.name
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Error: File', result.output)

        # Test with read-only output directory
        read_only_dir = tempfile.mkdtemp()
        os.chmod(read_only_dir, 0o444)  # Make directory read-only
        result = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            '--input-file', self.temp_input_file.name,
            '--output-file', os.path.join(read_only_dir, "output.txt")
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Error: Permission denied', result.output)
        os.rmdir(read_only_dir)

        # Test with empty input file
        empty_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        empty_file.close()
        result = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            '--input-file', empty_file.name,
            '--output-file', self.temp_output_file.name
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Error: Input file is empty', result.output)
        os.remove(empty_file.name)

    def test_prime_combinations(self):
        """Test encryption with different prime number combinations"""
        test_message = "Test message"
        
        # Test with single prime
        result1 = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            '--primes', '9973',
            test_message
        ])
        self.assertEqual(result1.exit_code, 0)
        output_lines = result1.output.split('\n')
        ciphertext1 = output_lines[0].split(': ')[1]
        mac1 = output_lines[1].split(': ')[1]
        
        # Test with multiple primes
        result2 = self.runner.invoke(cli, [
            'encrypt',
            '--secret', self.shared_secret,
            '--primes', '9973,9967',
            test_message
        ])
        self.assertEqual(result2.exit_code, 0)
        output_lines = result2.output.split('\n')
        ciphertext2 = output_lines[0].split(': ')[1]
        mac2 = output_lines[1].split(': ')[1]
        
        # Verify different primes produce different ciphertexts
        self.assertNotEqual(ciphertext1, ciphertext2)
        
        # Verify both can be decrypted correctly
        decrypt1 = self.runner.invoke(cli, [
            'decrypt',
            '--secret', self.shared_secret,
            '--mac-value', mac1,
            ciphertext1
        ])
        self.assertEqual(decrypt1.exit_code, 0)
        self.assertIn('Decrypted message: Test message', decrypt1.output)
        
        decrypt2 = self.runner.invoke(cli, [
            'decrypt',
            '--secret', self.shared_secret,
            '--mac-value', mac2,
            ciphertext2
        ])
        self.assertEqual(decrypt2.exit_code, 0)
        self.assertIn('Decrypted message: Test message', decrypt2.output)


if __name__ == '__main__':
    unittest.main()

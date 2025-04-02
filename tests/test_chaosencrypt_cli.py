import unittest
import tempfile
import os
from unittest.mock import patch
from chaosencrypt_cli import ChaosEncrypt, encrypt, decrypt, validate_input

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

    def tearDown(self):
        # Remove the temporary files after testing
        os.remove(self.temp_input_file.name)
        os.remove(self.temp_output_file.name)

    @patch('click.echo')
    def test_encrypt_cli(self, mock_echo):
        # Test encrypt CLI function
        encrypt(precision=12, primes='9973', secret=self.shared_secret, chunk_size=16, base_k=6, dynamic_k=True, xor=True, mac=True, input_file=None, output_file=None, message="Test message")
        mock_echo.assert_called()

    @patch('click.echo')
    def test_encrypt_cli_file(self, mock_echo):
        # Test encrypt CLI function with file input
        encrypt(precision=12, primes='9973', secret=self.shared_secret, chunk_size=16, base_k=6, dynamic_k=True, xor=True, mac=True, input_file=self.temp_input_file.name, output_file=self.temp_output_file.name, message=None)
        mock_echo.assert_not_called()
        with open(self.temp_output_file.name, 'r') as f:
            self.assertTrue(f.read() != "")

    @patch('click.echo')
    def test_encrypt_cli_message_and_file(self, mock_echo):
        with self.assertRaises(ValueError):
            encrypt(precision=12, primes='9973', secret=self.shared_secret, chunk_size=16, base_k=6, dynamic_k=True, xor=True, mac=True, input_file=self.temp_input_file.name, output_file=self.temp_output_file.name, message="Test message")

    @patch('click.echo')
    def test_decrypt_cli(self, mock_echo):
        # Test decrypt CLI function
        encryptor = ChaosEncrypt(shared_secret=self.shared_secret)
        ciphertext, mac = encryptor.encrypt("Test message")
        decrypt(precision=12, primes='9973', secret=self.shared_secret, chunk_size=16, base_k=6, dynamic_k=True, xor=True, mac=True, mac_value=str(mac), input_file=None, output_file=None, ciphertext=ciphertext.hex())
        mock_echo.assert_called()

    @patch('click.echo')
    def test_decrypt_cli_file(self, mock_echo):
        # Test decrypt CLI function with file input
        encryptor = ChaosEncrypt(shared_secret=self.shared_secret)
        ciphertext, mac = encryptor.encrypt("Test message")
        
        with open(self.temp_input_file.name, 'w') as f:
            f.write(ciphertext.hex())
        
        decrypt(precision=12, primes='9973', secret=self.shared_secret, chunk_size=16, base_k=6, dynamic_k=True, xor=True, mac=True, mac_value=str(mac), input_file=self.temp_input_file.name, output_file=self.temp_output_file.name, ciphertext=None)
        mock_echo.assert_not_called()
        with open(self.temp_output_file.name, 'r') as f:
            self.assertTrue(f.read() != "")
    
    @patch('click.echo')
    def test_decrypt_cli_message_and_file(self, mock_echo):
        # Test decrypt CLI function with file input
        encryptor = ChaosEncrypt(shared_secret=self.shared_secret)
        ciphertext, mac = encryptor.encrypt("Test message")
        with self.assertRaises(ValueError):
            decrypt(precision=12, primes='9973', secret=self.shared_secret, chunk_size=16, base_k=6, dynamic_k=True, xor=True, mac=True, mac_value=str(mac), input_file=self.temp_input_file.name, output_file=self.temp_output_file.name, ciphertext=ciphertext.hex())

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

        # Test empty secret
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="", chunk_size=16, base_k=6, mac_value=None)

        # Test invalid chunk size
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=0, base_k=6, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=1025, base_k=6, mac_value=None)

        # Test invalid base k
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=0, mac_value=None)
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=101, mac_value=None)

        # Test invalid mac_value
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=6, mac_value="test")

        # Test invalid ciphertext
        with self.assertRaises(ValueError):
            validate_input(precision=12, primes=[9973], secret="test_secret", chunk_size=16, base_k=6, mac_value=None, ciphertext="test")


if __name__ == '__main__':
    unittest.main()
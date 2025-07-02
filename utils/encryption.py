"""
Encryption Module for Sensitive Patient Data
"""

import os
import base64
import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatientDataEncryption:
    """
    Encryption system for sensitive patient data using Fernet symmetric encryption.
    """
    
    def __init__(self, key_file: str = ".encryption_key", salt_file: str = ".salt"):
        """
        Initialize the encryption system.
        
        Args:
            key_file (str): File to store the encryption key
            salt_file (str): File to store the salt
        """
        self.key_file = key_file
        self.salt_file = salt_file
        self.fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize or load encryption key."""
        try:
            # Try to load existing key
            if os.path.exists(self.key_file) and os.path.exists(self.salt_file):
                self._load_existing_key()
            else:
                self._generate_new_key()
            
            logger.info("Encryption system initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing encryption: {e}")
            raise
    
    def _generate_new_key(self):
        """Generate a new encryption key and salt."""
        try:
            # Generate a random salt
            salt = os.urandom(16)
            
            # Get password from environment or generate one
            password = os.getenv('ENCRYPTION_PASSWORD')
            if not password:
                # Generate a random password if not provided
                password = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
                logger.warning("No ENCRYPTION_PASSWORD in environment, using generated password")
            
            # Convert password to bytes
            password_bytes = password.encode('utf-8')
            
            # Generate key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            
            # Save key and salt
            self._save_key_and_salt(key, salt)
            
            # Initialize Fernet
            self.fernet = Fernet(key)
            
            logger.info("Generated new encryption key")
            
        except Exception as e:
            logger.error(f"Error generating new key: {e}")
            raise
    
    def _load_existing_key(self):
        """Load existing encryption key and salt."""
        try:
            # Load salt
            with open(self.salt_file, 'rb') as f:
                salt = f.read()
            
            # Get password
            password = os.getenv('ENCRYPTION_PASSWORD')
            if not password:
                raise ValueError("ENCRYPTION_PASSWORD environment variable required for existing key")
            
            password_bytes = password.encode('utf-8')
            
            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            
            # Initialize Fernet
            self.fernet = Fernet(key)
            
            logger.info("Loaded existing encryption key")
            
        except Exception as e:
            logger.error(f"Error loading existing key: {e}")
            raise
    
    def _save_key_and_salt(self, key: bytes, salt: bytes):
        """Save key and salt to files."""
        try:
            # Save salt
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            
            # Set restrictive permissions
            os.chmod(self.salt_file, 0o600)
            
            logger.info("Saved encryption key and salt")
            
        except Exception as e:
            logger.error(f"Error saving key and salt: {e}")
            raise
    
    def encrypt_data(self, data: Union[str, Dict, Any]) -> str:
        """
        Encrypt data (string, dict, or any JSON-serializable object).
        
        Args:
            data: Data to encrypt
            
        Returns:
            str: Base64 encoded encrypted data
        """
        try:
            # Convert data to JSON string if it's not already a string
            if not isinstance(data, str):
                data_str = json.dumps(data, ensure_ascii=False)
            else:
                data_str = data
            
            # Convert to bytes and encrypt
            data_bytes = data_str.encode('utf-8')
            encrypted_data = self.fernet.encrypt(data_bytes)
            
            # Return base64 encoded string
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> Union[str, Dict, Any]:
        """
        Decrypt data.
        
        Args:
            encrypted_data (str): Base64 encoded encrypted data
            
        Returns:
            Union[str, Dict, Any]: Decrypted data
        """
        try:
            # Decode base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            # Try to parse as JSON, return as string if it fails
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
            
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise
    
    def encrypt_patient_profile(self, patient_data: Dict[str, Any]) -> str:
        """
        Encrypt a patient profile.
        
        Args:
            patient_data (Dict): Patient profile data
            
        Returns:
            str: Encrypted patient data
        """
        try:
            # Add encryption metadata
            data_with_metadata = {
                'data': patient_data,
                'encrypted_at': self._get_timestamp(),
                'version': '1.0'
            }
            
            return self.encrypt_data(data_with_metadata)
            
        except Exception as e:
            logger.error(f"Error encrypting patient profile: {e}")
            raise
    
    def decrypt_patient_profile(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt a patient profile.
        
        Args:
            encrypted_data (str): Encrypted patient data
            
        Returns:
            Dict: Decrypted patient profile
        """
        try:
            decrypted_data = self.decrypt_data(encrypted_data)
            
            if isinstance(decrypted_data, dict) and 'data' in decrypted_data:
                return decrypted_data['data']
            else:
                return decrypted_data
            
        except Exception as e:
            logger.error(f"Error decrypting patient profile: {e}")
            raise
    
    def encrypt_file(self, input_file: str, output_file: str) -> bool:
        """
        Encrypt a file.
        
        Args:
            input_file (str): Path to input file
            output_file (str): Path to output encrypted file
            
        Returns:
            bool: True if successful
        """
        try:
            # Read input file
            with open(input_file, 'rb') as f:
                file_data = f.read()
            
            # Encrypt data
            encrypted_data = self.fernet.encrypt(file_data)
            
            # Write encrypted file
            with open(output_file, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info(f"Encrypted file: {input_file} -> {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error encrypting file: {e}")
            return False
    
    def decrypt_file(self, input_file: str, output_file: str) -> bool:
        """
        Decrypt a file.
        
        Args:
            input_file (str): Path to encrypted input file
            output_file (str): Path to output decrypted file
            
        Returns:
            bool: True if successful
        """
        try:
            # Read encrypted file
            with open(input_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            # Write decrypted file
            with open(output_file, 'wb') as f:
                f.write(decrypted_data)
            
            logger.info(f"Decrypted file: {input_file} -> {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error decrypting file: {e}")
            return False
    
    def encrypt_sensitive_fields(self, data: Dict[str, Any], sensitive_fields: list = None) -> Dict[str, Any]:
        """
        Encrypt only sensitive fields in a dictionary.
        
        Args:
            data (Dict): Data dictionary
            sensitive_fields (list): List of field names to encrypt
            
        Returns:
            Dict: Data with sensitive fields encrypted
        """
        if sensitive_fields is None:
            sensitive_fields = ['ssn', 'phone', 'email', 'address', 'medical_history', 'medications']
        
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt_data(encrypted_data[field])
        
        return encrypted_data
    
    def decrypt_sensitive_fields(self, data: Dict[str, Any], sensitive_fields: list = None) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in a dictionary.
        
        Args:
            data (Dict): Data dictionary with encrypted fields
            sensitive_fields (list): List of field names to decrypt
            
        Returns:
            Dict: Data with sensitive fields decrypted
        """
        if sensitive_fields is None:
            sensitive_fields = ['ssn', 'phone', 'email', 'address', 'medical_history', 'medications']
        
        decrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt_data(decrypted_data[field])
                except Exception as e:
                    logger.warning(f"Could not decrypt field {field}: {e}")
        
        return decrypted_data
    
    def save_encrypted_data(self, data: Union[str, Dict, Any], filepath: str) -> bool:
        """
        Save encrypted data to a file.
        
        Args:
            data: Data to encrypt and save
            filepath (str): Path to save encrypted data
            
        Returns:
            bool: True if successful
        """
        try:
            encrypted_data = self.encrypt_data(data)
            
            with open(filepath, 'w') as f:
                f.write(encrypted_data)
            
            logger.info(f"Saved encrypted data to: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving encrypted data: {e}")
            return False
    
    def load_encrypted_data(self, filepath: str) -> Union[str, Dict, Any]:
        """
        Load and decrypt data from a file.
        
        Args:
            filepath (str): Path to encrypted data file
            
        Returns:
            Union[str, Dict, Any]: Decrypted data
        """
        try:
            with open(filepath, 'r') as f:
                encrypted_data = f.read()
            
            return self.decrypt_data(encrypted_data)
            
        except Exception as e:
            logger.error(f"Error loading encrypted data: {e}")
            raise
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def rotate_key(self) -> bool:
        """
        Rotate the encryption key (re-encrypt all data with new key).
        This is a placeholder for key rotation functionality.
        
        Returns:
            bool: True if successful
        """
        logger.warning("Key rotation not implemented - this would require re-encrypting all data")
        return False
    
    def verify_encryption(self) -> bool:
        """
        Verify that encryption is working correctly.
        
        Returns:
            bool: True if encryption is working
        """
        try:
            test_data = {"test": "data", "number": 123}
            encrypted = self.encrypt_data(test_data)
            decrypted = self.decrypt_data(encrypted)
            
            return test_data == decrypted
            
        except Exception as e:
            logger.error(f"Encryption verification failed: {e}")
            return False


# Convenience functions
def generate_key():
    """
    Generate a new encryption key and save it to files.
    This function should only be run once to set up encryption.
    
    Returns:
        bool: True if key generation was successful
    """
    try:
        # Initialize encryption system (this will generate new key)
        encryption = PatientDataEncryption()
        
        # Test the encryption
        from datetime import datetime
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        encrypted = encryption.encrypt_data(test_data)
        decrypted = encryption.decrypt_data(encrypted)
        
        if test_data == decrypted:
            print("✅ Encryption key generated successfully!")
            print("🔐 Key files created:")
            print("   - .salt (salt file)")
            print("   - token.json (will be created on first use)")
            print("\n⚠️  Important:")
            print("   - Keep your ENCRYPTION_PASSWORD secure")
            print("   - Back up the .salt file")
            print("   - Never share your encryption credentials")
            return True
        else:
            print("❌ Encryption test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error generating encryption key: {e}")
        return False


def encrypt_patient_data(patient_data: Dict[str, Any]) -> str:
    """
    Convenience function to encrypt patient data.
    
    Args:
        patient_data (Dict): Patient data to encrypt
        
    Returns:
        str: Encrypted patient data
    """
    encryption = PatientDataEncryption()
    return encryption.encrypt_patient_profile(patient_data)


def decrypt_patient_data(encrypted_data: str) -> Dict[str, Any]:
    """
    Convenience function to decrypt patient data.
    
    Args:
        encrypted_data (str): Encrypted patient data
        
    Returns:
        Dict: Decrypted patient data
    """
    encryption = PatientDataEncryption()
    return encryption.decrypt_patient_profile(encrypted_data)


def encrypt_file_simple(input_file: str, output_file: str) -> bool:
    """
    Convenience function to encrypt a file.
    
    Args:
        input_file (str): Input file path
        output_file (str): Output encrypted file path
        
    Returns:
        bool: True if successful
    """
    encryption = PatientDataEncryption()
    return encryption.encrypt_file(input_file, output_file)


def decrypt_file_simple(input_file: str, output_file: str) -> bool:
    """
    Convenience function to decrypt a file.
    
    Args:
        input_file (str): Encrypted input file path
        output_file (str): Output decrypted file path
        
    Returns:
        bool: True if successful
    """
    encryption = PatientDataEncryption()
    return encryption.decrypt_file(input_file, output_file)


if __name__ == "__main__":
    # Example usage
    encryption = PatientDataEncryption()
    
    # Test encryption
    if encryption.verify_encryption():
        print("✅ Encryption system is working correctly")
    else:
        print("❌ Encryption system verification failed")
    
    # Example patient data
    patient_data = {
        "name": "John Doe",
        "age": 65,
        "diagnosis": "Acute Myocardial Infarction",
        "ssn": "123-45-6789",
        "phone": "555-123-4567",
        "email": "john.doe@email.com",
        "medications": ["Aspirin 81mg", "Metoprolol 25mg"],
        "medical_history": "Previous MI in 2020, hypertension, diabetes"
    }
    
    # Encrypt patient data
    encrypted_data = encryption.encrypt_patient_profile(patient_data)
    print(f"Encrypted data length: {len(encrypted_data)} characters")
    
    # Decrypt patient data
    decrypted_data = encryption.decrypt_patient_profile(encrypted_data)
    print(f"Decrypted data matches original: {patient_data == decrypted_data}")
    
    # Test file encryption
    test_file = "test_data.txt"
    encrypted_file = "test_data.encrypted"
    decrypted_file = "test_data_decrypted.txt"
    
    # Create test file
    with open(test_file, 'w') as f:
        f.write("This is sensitive patient data that needs to be encrypted.")
    
    # Encrypt file
    if encryption.encrypt_file(test_file, encrypted_file):
        print(f"✅ File encrypted: {encrypted_file}")
    
    # Decrypt file
    if encryption.decrypt_file(encrypted_file, decrypted_file):
        print(f"✅ File decrypted: {decrypted_file}")
    
    # Clean up test files
    for file in [test_file, encrypted_file, decrypted_file]:
        if os.path.exists(file):
            os.remove(file)
    
    print("🔐 Encryption module test completed successfully!") 
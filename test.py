from config import ENCRYPTED_SMTP_PASS
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv('.env.local')
key = os.getenv('SMTP_KEY').encode()
f = Fernet(key)
password = f.decrypt(ENCRYPTED_SMTP_PASS.encode()).decode()
print("✅ SUCCESS! Your decrypted password:", password)

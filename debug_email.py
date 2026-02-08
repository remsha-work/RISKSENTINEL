from config import ENCRYPTED_SMTP_PASS, SMTP_SERVER, SMTP_PORT, SMTP_USER
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
import smtplib

load_dotenv('.env.local')
key = os.getenv('SMTP_KEY').encode()
f = Fernet(key)
password = f.decrypt(ENCRYPTED_SMTP_PASS.encode()).decode()
print(f"📧 Email: {SMTP_USER}")
print(f"🔑 Password: {password}")

# Test SMTP login
try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, password)
    print("✅ SMTP LOGIN SUCCESS!")
    server.quit()
except Exception as e:
    print(f"❌ SMTP ERROR: {e}")

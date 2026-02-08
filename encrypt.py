from cryptography.fernet import Fernet

# Generate key
key = Fernet.generate_key()
print("🔑 SAVE THIS KEY (copy to notepad):")
print(key.decode())

# YOUR NEW PASSWORD from Gmail
smtp_pass = "rpsy xedr jvrt tkkd"  # NEW password WITH SPACES


# Encrypt it
f = Fernet(key)
encrypted = f.encrypt(smtp_pass.encode())
print("\n🔒 COPY THIS ENCRYPTED STRING:")
print(encrypted.decode())

from werkzeug.security import generate_password_hash

hashed_password = generate_password_hash("changeme")

print(hashed_password)
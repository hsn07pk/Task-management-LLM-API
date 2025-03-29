# extensions.py
from flask_caching import Cache

# Initialize the Cache object with a simple in-memory caching strategy
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})  # Simple in-memory caching

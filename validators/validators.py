# validators.py
from flask import request, jsonify
from jsonschema import validate, ValidationError
from functools import wraps

def validate_json(schema):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No input data provided'}), 400

                validate(instance=data, schema=schema)
                return func(*args, **kwargs)
            except ValidationError as e:
                return jsonify({'error': f'Invalid request data: {e.message}'}), 400
        return wrapper
    return decorator

# validators.py
from flask import request, jsonify
from jsonschema import validate, ValidationError
from functools import wraps

def validate_json(schema):
    """
    Decorator to validate the JSON request data against a given schema.

    This decorator can be applied to Flask view functions to ensure that the
    incoming request contains valid JSON data as per the provided schema. If the 
    request data is invalid or missing, it will return a 400 Bad Request response 
    with an appropriate error message.

    Args:
        schema (dict): The JSON schema that the request data should conform to.

    Returns:
        function: The wrapped view function that validates the JSON request data.
    
    Example:
        @app.route('/some-endpoint', methods=['POST'])
        @validate_json(some_schema)
        def some_view_function():
            # Your code logic here
            pass
    """
    def decorator(func):
        """
        The actual decorator function that wraps the view function.
        
        Args:
            func (function): The Flask view function to be decorated.

        Returns:
            wrapper (function): The wrapped version of the original view function
                                 with added validation logic.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            The wrapper function that handles JSON validation and exception handling.

            It extracts the JSON data from the request, validates it against the 
            provided schema, and either calls the original view function if the data 
            is valid or returns an error response if validation fails.

            Args:
                *args: Variable length arguments passed to the original view function.
                **kwargs: Variable length keyword arguments passed to the original view function.

            Returns:
                Response: Either a valid response from the original view function or a 
                          400 Bad Request error response in case of invalid data.
            """
            try:
                # Attempt to get the JSON data from the request
                data = request.get_json()
                
                # If no data is provided, return an error response
                if not data:
                    return jsonify({'error': 'No input data provided'}), 400

                # Validate the JSON data against the provided schema
                validate(instance=data, schema=schema)
                
                # If validation passes, call the original view function
                return func(*args, **kwargs)
            
            except ValidationError as e:
                # If the validation fails, return a 400 Bad Request with the error message
                return jsonify({'error': f'Invalid request data: {e.message}'}), 400

        return wrapper
    return decorator

from jsonschema import SchemaError, ValidationError
import jsonschema
from flask import jsonify

# Schema definitions
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 3},
        "description": {"type": "string"},
        "priority": {"enum": [1, 2, 3]},
        "status": {"enum": ["pending", "in_progress", "completed"]},
        "project_id": {"type": "string", "format": "uuid"},
        "assignee_id": {"type": "string", "format": "uuid"},
        "deadline": {"type": "string", "format": "date-time"}
    },
    "required": ["title", "project_id"],
    "additionalProperties": False
}

TEAM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 3},
        "description": {"type": "string"},
        "lead_id": {"type": "string", "format": "uuid"}
    },
    "required": ["name"],
    "additionalProperties": False
}

def validate_schema(data, schema):
    try:
        jsonschema.validate(instance=data, schema=schema)
    except ValidationError as e:
        return jsonify({
            "error": "Validation Error",
            "message": e.message
        }), 400
    except SchemaError as e:
        return jsonify({
            "error": "Schema Error",
            "message": "Invalid validation schema"
        }), 500
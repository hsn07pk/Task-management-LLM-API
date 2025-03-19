# schemas.py
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "project_id": {"type": "string", "format": "uuid"},
        "status": {"enum": ["pending", "in_progress", "completed"]}
    },
    "required": ["title", "project_id"]
}

TEAM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "lead_id": {"type": "string", "format": "uuid"},
        "description": {"type": "string"}
    },
    "required": ["name", "lead_id"]
}

TEAM_MEMBERSHIP_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string", "format": "uuid"},
        "role": {"type": "string", "minLength": 1}
    },
    "required": ["user_id", "role"]
}

PROJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "team_id": {"type": "string", "format": "uuid"},
        "category_id": {"type": "string", "format": "uuid"}
    },
    "required": ["title", "team_id"]
}

USER_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "password": {"type": "string", "minLength": 8},
        "role": {"type": "string", "enum": ["admin", "member"]}
    },
    "required": ["username", "email", "password"]
}
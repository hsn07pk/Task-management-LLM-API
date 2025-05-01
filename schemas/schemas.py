# schemas/schemas.py

USER_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 32},
        "email": {"type": "string", "format": "email"},
        "password": {"type": "string", "minLength": 6},
        "role": {"type": "string", "enum": ["admin", "member"], "default": "member"}
    },
    "required": ["username", "email", "password"],
    "additionalProperties": False
}

USER_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 32},
        "email": {"type": "string", "format": "email"},
        "password": {"type": "string", "minLength": 6},
        "role": {"type": "string", "enum": ["admin", "member"]}
    },
    "minProperties": 1,
    "additionalProperties": False
}

PROJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 100},
        "description": {"type": "string"},
        "start_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
        "status": {"type": "string", "enum": ["active", "completed", "archived"], "default": "active"}
    },
    "required": ["name"],
    "additionalProperties": False
}

PROJECT_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 100},
        "description": {"type": "string"},
        "start_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
        "status": {"type": "string", "enum": ["active", "completed", "archived"]}
    },
    "minProperties": 1,
    "additionalProperties": False
}

TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 100},
        "description": {"type": "string"},
        "project_id": {"type": "string"},
        "assignee_id": {"type": "string"},
        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "archived"], "default": "pending"},
        "priority": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
        "due_date": {"type": "string", "format": "date"}
    },
    "required": ["title", "project_id"],
    "additionalProperties": False
}

TASK_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 100},
        "description": {"type": "string"},
        "project_id": {"type": "string"},
        "assignee_id": {"type": "string"},
        "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "archived"]},
        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
        "due_date": {"type": "string", "format": "date"}
    },
    "minProperties": 1,
    "additionalProperties": False
}

TEAM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 100},
        "description": {"type": "string"},
        "lead_id": {"type": "string"}
    },
    "required": ["name", "lead_id"],
    "additionalProperties": False
}

TEAM_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "maxLength": 100},
        "description": {"type": "string"},
        "lead_id": {"type": "string"}
    },
    "minProperties": 1,
    "additionalProperties": False
}

TEAM_MEMBERSHIP_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string"},
        "role": {"type": "string", "enum": ["member", "lead", "admin"]}
    },
    "required": ["user_id", "role"],
    "additionalProperties": False
}

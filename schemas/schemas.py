"""
JSON schemas for request validation in the Flask API.
These schemas are used by the validation decorators to ensure
that incoming request data is properly formatted and contains
all required fields.
"""

# User schemas
USER_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 50},
        "email": {"type": "string", "format": "email", "maxLength": 100},
        "password": {"type": "string", "minLength": 8, "maxLength": 100},
        "full_name": {"type": "string", "maxLength": 100},
        "role": {"type": "string", "enum": ["admin", "member"]},
    },
    "required": ["username", "email", "password"],
    "additionalProperties": False,
}

USER_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string", "minLength": 3, "maxLength": 50},
        "email": {"type": "string", "format": "email", "maxLength": 100},
        "password": {"type": "string", "minLength": 8, "maxLength": 100},
        "full_name": {"type": "string", "maxLength": 100},
        "role": {"type": "string", "enum": ["admin", "member"]},
    },
    "additionalProperties": False,
}

# Project schemas
PROJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 3, "maxLength": 100},
        "description": {"type": "string", "maxLength": 500},
        "start_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
        "status": {
            "type": "string",
            "enum": ["planning", "active", "completed", "on_hold", "cancelled"],
        },
        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
        "team_id": {"type": "string", "format": "uuid"},
        "owner_id": {"type": "string", "format": "uuid"},
    },
    "required": ["title", "status", "priority"],
    "additionalProperties": False,
}

PROJECT_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 3, "maxLength": 100},
        "description": {"type": "string", "maxLength": 500},
        "start_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
        "status": {
            "type": "string",
            "enum": ["planning", "active", "completed", "on_hold", "cancelled"],
        },
        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
        "team_id": {"type": "string", "format": "uuid"},
        "owner_id": {"type": "string", "format": "uuid"},
    },
    "additionalProperties": False,
}

# Task schemas
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 3, "maxLength": 100},
        "description": {"type": "string", "maxLength": 500},
        "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
        "due_date": {"type": "string", "format": "date"},
        "project_id": {"type": "string", "format": "uuid"},
        "assignee_id": {"type": "string", "format": "uuid"},
    },
    "required": ["title", "status", "priority", "project_id"],
    "additionalProperties": False,
}

TASK_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 3, "maxLength": 100},
        "description": {"type": "string", "maxLength": 500},
        "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
        "due_date": {"type": "string", "format": "date"},
        "project_id": {"type": "string", "format": "uuid"},
        "assignee_id": {"type": "string", "format": "uuid"},
    },
    "additionalProperties": False,
}

# Team schemas
TEAM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 3, "maxLength": 100},
        "description": {"type": "string", "maxLength": 500},
        "lead_id": {"type": "string", "format": "uuid"},
    },
    "required": ["name", "lead_id"],
    "additionalProperties": False,
}

TEAM_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 3, "maxLength": 100},
        "description": {"type": "string", "maxLength": 500},
        "lead_id": {"type": "string", "format": "uuid"},
    },
    "additionalProperties": False,
}

TEAM_MEMBERSHIP_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string", "format": "uuid"},
        "role": {
            "type": "string",
            "enum": ["lead", "developer", "tester", "designer", "product_manager"],
        },
    },
    "required": ["user_id", "role"],
    "additionalProperties": False,
}

TEAM_MEMBERSHIP_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {
            "type": "string",
            "enum": ["lead", "developer", "tester", "designer", "product_manager"],
        },
    },
    "required": ["role"],
    "additionalProperties": False,
}

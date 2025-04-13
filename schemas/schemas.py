# TASK_SCHEMA: Defines the schema for a task object.
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1},  # Title must be a non-empty string
        "project_id": {"type": "string", "format": "uuid"},  # Project ID must be in UUID format
        "status": {
            "type": "string",
            "enum": ["pending", "in_progress", "completed"],  # Allowed status values
        },
    },
    "required": ["title", "project_id", "status"],  # All three fields are required
}

# TEAM_SCHEMA: Defines the schema for a team object.
TEAM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},  # Team name must be a non-empty string
        "lead_id": {"type": "string", "format": "uuid"},  # Lead ID must be in UUID format
        "description": {
            "type": "string",
            "minLength": 1,  # Ensure description is at least one character
        },
    },
    "required": ["name", "lead_id"],  # Name and lead_id are mandatory
}

TEAM_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "lead_id": {"type": "string", "format": "uuid"},
        "description": {"type": "string", "minLength": 1},
    },
}


# TEAM_MEMBERSHIP_SCHEMA: Defines the schema for a team membership object.
TEAM_MEMBERSHIP_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string", "format": "uuid"},  # User ID must be in UUID format
        "role": {"type": "string", "minLength": 1},  # Role must be a non-empty string
    },
    "required": ["user_id", "role"],  # user_id and role are mandatory fields
}

# PROJECT_SCHEMA: Defines the schema for a project object.
PROJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1},  # Project title must be a non-empty string
        "description": {
            "type": "string",
            "minLength": 1,  # Ensure description is at least one character
        },
        "team_id": {"type": "string", "format": "uuid"},  # Team ID must be in UUID format
        "category_id": {"type": "string", "format": "uuid"},  # Category ID must be in UUID format
    },
    "required": ["title", "team_id"],  # Required fields
}

PROJECT_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 1},
        "team_id": {"type": "string", "format": "uuid"},
        "category_id": {"type": "string", "format": "uuid"},
    },
}

# USER_SCHEMA: Defines the schema for a user object.
USER_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string", "minLength": 1},  # Username must be a non-empty string
        "email": {"type": "string", "format": "email"},  # Email must be in valid email format
        "password": {
            "type": "string",
            "minLength": 8,  # Password must be at least 8 characters long
        },
        "role": {"type": "string", "enum": ["admin", "member"]},  # Allowed role values
    },
    "required": ["username", "email", "password", "role"],  # Required fields
}

# USER_SCHEMA: Defines the schema to update a user object.
USER_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string", "minLength": 1},
        "email": {"type": "string", "format": "email"},
        "password": {"type": "string", "minLength": 8},
        "role": {"type": "string", "enum": ["admin", "member"]},
    },
    # No "required" field for updates
}

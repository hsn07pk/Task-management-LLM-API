# schemas.py

# TASK_SCHEMA: Defines the schema for a task object.
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string", 
            "minLength": 1,  # Title must be a non-empty string
        },
        "project_id": {
            "type": "string", 
            "format": "uuid"  # Project ID must be in UUID format
        },
        "status": {
            "enum": ["pending", "in_progress", "completed"]  # Status can only be one of these values
        }
    },
    "required": ["title", "project_id"]  # title and project_id are mandatory fields
}

# TEAM_SCHEMA: Defines the schema for a team object.
TEAM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string", 
            "minLength": 1  # Team name must be a non-empty string
        },
        "lead_id": {
            "type": "string", 
            "format": "uuid"  # Lead ID must be in UUID format
        },
        "description": {
            "type": "string"  # Description is optional and should be a string
        }
    },
    "required": ["name", "lead_id"]  # name and lead_id are mandatory fields
}

# TEAM_MEMBERSHIP_SCHEMA: Defines the schema for a team membership object.
TEAM_MEMBERSHIP_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {
            "type": "string", 
            "format": "uuid"  # User ID must be in UUID format
        },
        "role": {
            "type": "string", 
            "minLength": 1  # Role must be a non-empty string
        }
    },
    "required": ["user_id", "role"]  # user_id and role are mandatory fields
}

# PROJECT_SCHEMA: Defines the schema for a project object.
PROJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string"  # Title of the project
        },
        "description": {
            "type": "string"  # Description of the project
        },
        "team_id": {
            "type": "string", 
            "format": "uuid"  # Team ID must be in UUID format
        },
        "category_id": {
            "type": "string", 
            "format": "uuid"  # Category ID must be in UUID format
        }
    },
    "required": ["title", "team_id"]  # title and team_id are mandatory fields
}

# USER_SCHEMA: Defines the schema for a user object.
USER_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {
            "type": "string"  # Username of the user
        },
        "email": {
            "type": "string", 
            "format": "email"  # Email must be in valid email format
        },
        "password": {
            "type": "string", 
            "minLength": 8  # Password must be at least 8 characters long
        },
        "role": {
            "type": "string", 
            "enum": ["admin", "member"]  # Role can only be either "admin" or "member"
        }
    },
    "required": ["username", "email", "password"]  # username, email, and password are mandatory fields
}

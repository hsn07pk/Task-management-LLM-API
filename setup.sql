-- Step 1: Create Tables
CREATE TABLE "USER" (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE TEAM (
    team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lead_id UUID REFERENCES "USER"(user_id)
);

CREATE TABLE CATEGORY (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#64748b'
);

CREATE TABLE PROJECT (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'planning',
    deadline TIMESTAMP,
    team_id UUID REFERENCES TEAM(team_id),
    category_id UUID REFERENCES CATEGORY(category_id)
);

CREATE TABLE TASK (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INT CHECK (priority BETWEEN 1 AND 5) DEFAULT 3,
    deadline TIMESTAMP,
    project_id UUID REFERENCES PROJECT(project_id),
    assignee_id UUID REFERENCES "USER"(user_id)
);

CREATE TABLE TEAM_MEMBERSHIP (
    membership_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES "USER"(user_id),
    team_id UUID REFERENCES TEAM(team_id),
    role VARCHAR(50) DEFAULT 'member'
);

-- Step 2: Insert Dummy Data for Users
INSERT INTO "USER" (username, email, password_hash, role) VALUES
('alice', 'alice@example.com', 'hashed_password_1', 'admin'),
('bob', 'bob@example.com', 'hashed_password_2', 'member'),
('charlie', 'charlie@example.com', 'hashed_password_3', 'member'),
('david', 'david@example.com', 'hashed_password_4', 'admin'),
('eve', 'eve@example.com', 'hashed_password_5', 'member'),
('frank', 'frank@example.com', 'hashed_password_6', 'member'),
('grace', 'grace@example.com', 'hashed_password_7', 'admin'),
('harry', 'harry@example.com', 'hashed_password_8', 'member'),
('isabel', 'isabel@example.com', 'hashed_password_9', 'member'),
('jack', 'jack@example.com', 'hashed_password_10', 'admin'),
('kate', 'kate@example.com', 'hashed_password_11', 'member'),
('leo', 'leo@example.com', 'hashed_password_12', 'member'),
('mia', 'mia@example.com', 'hashed_password_13', 'admin'),
('nathan', 'nathan@example.com', 'hashed_password_14', 'member'),
('olivia', 'olivia@example.com', 'hashed_password_15', 'member'),
('peter', 'peter@example.com', 'hashed_password_16', 'admin'),
('quincy', 'quincy@example.com', 'hashed_password_17', 'member'),
('rachel', 'rachel@example.com', 'hashed_password_18', 'member'),
('steve', 'steve@example.com', 'hashed_password_19', 'admin'),
('tina', 'tina@example.com', 'hashed_password_20', 'member');

-- Step 3: Insert Teams
INSERT INTO TEAM (name, description, lead_id) VALUES
('Development Team', 'Handles software development', (SELECT user_id FROM "USER" WHERE username = 'alice')),
('Marketing Team', 'Handles marketing strategies', (SELECT user_id FROM "USER" WHERE username = 'bob')),
('Design Team', 'Creates UI/UX', (SELECT user_id FROM "USER" WHERE username = 'grace')),
('HR Team', 'Handles employee relations', (SELECT user_id FROM "USER" WHERE username = 'jack')),
('Support Team', 'Manages customer issues', (SELECT user_id FROM "USER" WHERE username = 'mia'));

-- Step 4: Insert Categories
INSERT INTO CATEGORY (name, color) VALUES
('Software', '#FF5733'),
('Marketing', '#33FF57'),
('HR', '#3357FF'),
('Design', '#FF33AA'),
('Support', '#33FFFF');

-- Step 5: Insert Projects
INSERT INTO PROJECT (title, description, status, team_id, category_id) VALUES
('E-commerce Website', 'Building an online store', 'active', (SELECT team_id FROM TEAM WHERE name = 'Development Team'), (SELECT category_id FROM CATEGORY WHERE name = 'Software')),
('Ad Campaign', 'Creating a new marketing campaign', 'planning', (SELECT team_id FROM TEAM WHERE name = 'Marketing Team'), (SELECT category_id FROM CATEGORY WHERE name = 'Marketing')),
('HR Portal', 'Developing an internal HR portal', 'development', (SELECT team_id FROM TEAM WHERE name = 'HR Team'), (SELECT category_id FROM CATEGORY WHERE name = 'HR'));

-- Step 6: Insert Tasks
INSERT INTO TASK (title, description, priority, project_id, assignee_id) VALUES
('Design Homepage', 'Create a responsive homepage', 4, (SELECT project_id FROM PROJECT WHERE title = 'E-commerce Website'), (SELECT user_id FROM "USER" WHERE username = 'alice')),
('Write Blog Post', 'Write a blog post about the campaign', 3, (SELECT project_id FROM PROJECT WHERE title = 'Ad Campaign'), (SELECT user_id FROM "USER" WHERE username = 'bob')),
('HR System Audit', 'Review the HR system logs', 5, (SELECT project_id FROM PROJECT WHERE title = 'HR Portal'), (SELECT user_id FROM "USER" WHERE username = 'jack'));

-- Step 7: Insert Team Memberships
INSERT INTO TEAM_MEMBERSHIP (user_id, team_id, role) VALUES
((SELECT user_id FROM "USER" WHERE username = 'alice'), (SELECT team_id FROM TEAM WHERE name = 'Development Team'), 'lead'),
((SELECT user_id FROM "USER" WHERE username = 'bob'), (SELECT team_id FROM TEAM WHERE name = 'Marketing Team'), 'member'),
((SELECT user_id FROM "USER" WHERE username = 'grace'), (SELECT team_id FROM TEAM WHERE name = 'Design Team'), 'lead'),
((SELECT user_id FROM "USER" WHERE username = 'jack'), (SELECT team_id FROM TEAM WHERE name = 'HR Team'), 'lead'),
((SELECT user_id FROM "USER" WHERE username = 'mia'), (SELECT team_id FROM TEAM WHERE name = 'Support Team'), 'lead');

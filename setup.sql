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
    priority INT CHECK (priority BETWEEN 1 AND 3) DEFAULT 3,
    deadline TIMESTAMP,
    project_id UUID REFERENCES PROJECT(project_id),
    assignee_id UUID REFERENCES "USER"(user_id),
    created_by UUID REFERENCES "USER"(user_id),  -- Add this line
    updated_by UUID REFERENCES "USER"(user_id)   -- Add this line
);


CREATE TABLE TEAM_MEMBERSHIP (
    membership_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES "USER"(user_id),
    team_id UUID REFERENCES TEAM(team_id),
    role VARCHAR(50) DEFAULT 'member'
);

-- Step 2: Insert Dummy Data for Users
INSERT INTO "USER" (username, email, password_hash, role) VALUES
('alice', 'alice@example.com', 'scrypt:32768:8:1$VU4ClwsmdMiXaUxj$0798bb69bfbd57d152f4a08ae8c360929cf09e0364fa31ae6ce09875f79eaca20ee8201e5eb9ddad5d6c02393c9c980c1c6cb9751783c3b42445c3b87085af6e', 'admin'),
('bob', 'bob@example.com', 'scrypt:32768:8:1$eJXP4aVnlSqeEO8P$505d3ab13749a08ecc4ffc60ddd1686af1261578b344a89adfe0c9e23fa7058dbefae90664b2a0832c192a96d1786fe7d04e93fa5e927f8c9b20afb530f901f8', 'member'),
('charlie', 'charlie@example.com', 'scrypt:32768:8:1$8NB00oQJZMtDL8y7$040650a2aa329a01f8c01c122751ec5893575ad31b913128974b5bae0cb30c58ae8897a5aaf5e05c8213fcad28b13043c3f7919a01b0a5ffa3ba067cd31d6078', 'member'),
('david', 'david@example.com', 'scrypt:32768:8:1$p6kUDw8REpwcJFiV$96f7db9b62b21fe19db0a599f7bfcf4c93479ca4d86ae3ed89dfcc3df61645331ee0def7b7685f5eade9c48878d4025f5e075aa06da57e7529d7ec3a346d28c5', 'admin'),
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

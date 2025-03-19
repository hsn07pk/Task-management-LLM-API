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
('eve', 'eve@example.com', 'scrypt:32768:8:1$WAgzLKbZM9mLl6Bq$c70d8ef0b64c8cfdd9d81a32a2ed796aebe9e928a765c8505b6b3b134dfa163cccffe2cebed3325f18c8ea2c29ccc304523aeae2cbe9a126803d8e221ea59f3a', 'member'),
('frank', 'frank@example.com', 'scrypt:32768:8:1$Tq2nX67j1WntK5za$b362fbaa1d805282a047e820887167a311d423f33990567e8a4c002cb5c8bac4b0d3b3e7f31f3e48c17b873d3a1571cbb4b494bb65ac2170f61ec9df04913c97', 'member'),
('grace', 'grace@example.com', 'scrypt:32768:8:1$PlSYkZ2XMt3BmRSM$cbc2047b64c2a175ec8170665631076916fffe40102648ba6db33ce3d9df5d3b3c55776d71137b556dc75b7275afc16e0bc561cc385fcc3f4ca0f818715b5b4b', 'admin'),
('harry', 'harry@example.com', 'scrypt:32768:8:1$Niwzr72kdk9oetJ3$aa07f43599627cdf7fc80b62468c635006373b3e10cc5408ad68c66665e994c75e9dd0f1abb64012ac2f383705f49450cff5e4eef536f42e408b72678f9578f1', 'member'),
('isabel', 'isabel@example.com', 'scrypt:32768:8:1$RB9nZQLVlzlv9Cnt$00480ee8eed4122ab11ce527212669edd0a6a97359bd8990dc727a078721e997180b761cae313468f399e3d213a2484836bddff2c9b12fbeb7d2125eec494863', 'member'),
('jack', 'jack@example.com', 'scrypt:32768:8:1$ujtlcsLfQOao7ExM$b3e3914cc9af5b9790f9539d11e9680ddb104911cc2d8a271712fb8002c71710d73605c5935c256608be99e86c4198f7b367a775492ac1fbed701e00e34c85cd', 'admin'),
('kate', 'kate@example.com', 'scrypt:32768:8:1$QTgsTVL3Oxnfqqfs$dec9bdaab42733547a634aa80c5eab233842265f4f40ee2cbc32a806a6de32d3fc4b48acdf73b9bb7d0c8e2baa768fcfa3ac31130918edff05dcf824a51ac1b3', 'member'),
('leo', 'leo@example.com', 'scrypt:32768:8:1$0Dr5cPxsEDVCa0pw$1043dc6de5e1cddbcab4324079d2f5e2377417f453c9a3e737d0c382bb9b8e0e10b675614366344baee85552b1500ec9c117bf6c698667d382536a19d7d8412f', 'member'),
('mia', 'mia@example.com', 'scrypt:32768:8:1$yVqMy9sqcgNsGIsI$70aa16ade92729d936ad6ddd3fc3a6603d9c2436778ded9e16ae7016bbf51e3f9d0bd853d3d35bf8d77878cca3215416c4f40f131179535ee448267b39535a75', 'admin'),
('nathan', 'nathan@example.com', 'scrypt:32768:8:1$Ltw4UoXF5v3ukKEI$7602a18dd3e1897d1515678610d1e0ebd6b8693a9577e17e5f5eef4f1448ade448ff59b115fd6d7bdc4eef9fa4e2b0d16abf637190127c7f0199ea206ec3119a', 'member'),
('olivia', 'olivia@example.com', 'scrypt:32768:8:1$wIojsDVhwVCKm1R4$f9c7159a1d60583ec745a686a00318642493b48b9383e6eaa90df4b6a41dc5e52415dc53e251824a9d5a15112a61d52f33542310b88dec550bff3965af4019d2', 'member'),
('peter', 'peter@example.com', 'scrypt:32768:8:1$DYrRFqmtGr1HokU5$d128cc45c89335a7da53bf2f9ef84a1f8709c30a43e8c37326eaf172371bd5fd2b33193031d026d6a1c6c16a0c36bd68a02f834270de32881c1027d7a870f08a', 'admin'),
('quincy', 'quincy@example.com', 'scrypt:32768:8:1$TBWWxEwKro5111Rb$f9dbc99e15e78744d521743b3f509ee853c34ec202299a3e5a5916982eec4afe2219d13f5f29b5dbde032a136afb7135cae95a6ba8e6f72d5d1385a059fb17fd', 'member'),
('rachel', 'rachel@example.com', 'scrypt:32768:8:1$SRevr2rs8VFFGvOC$d69977a06d47e73dbd858c8d622018560303c17e5aa9fed801af01f7476dec81410a13a0e2ed101647af35ec32c1c78432f78cfaefb314dc7060c64252c4064e', 'member'),
('steve', 'steve@example.com', 'scrypt:32768:8:1$BLzMhcILsVrcjdMW$2ad9564f42cddb35ccb47440dd3e5eee561cf04b41fc16fefc1530fc09a7ed444ad4705112587a9a7f6c2683f98ff597183cac87ce5d8db6fe3c9d71e3be320a', 'admin'),
('tina', 'tina@example.com', 'scrypt:32768:8:1$SKKKiwZXYpbzJoJJ$09e2d02efcd9399e11f126bb0e543de0311ee294c7b573d395d7f2520a483555f8e3cab7de75602dd40e99dddc390d55d3fe8e35769d401368c265be32b6b31e', 'member');

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

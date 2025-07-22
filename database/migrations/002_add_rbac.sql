-- RBAC tables

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id VARCHAR(50) NOT NULL,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- default data
INSERT INTO roles (name, description) VALUES
    ('admin', 'Administrator with full access'),
    ('basic', 'Basic user with limited access')
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, description) VALUES
    ('view_dashboard', 'View dashboard pages'),
    ('manage_users', 'Manage user accounts'),
    ('edit_settings', 'Edit application settings')
ON CONFLICT (name) DO NOTHING;

-- assign permissions to admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name IN ('view_dashboard', 'manage_users', 'edit_settings')
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- assign basic permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON p.name = 'view_dashboard'
WHERE r.name = 'basic'
ON CONFLICT DO NOTHING;


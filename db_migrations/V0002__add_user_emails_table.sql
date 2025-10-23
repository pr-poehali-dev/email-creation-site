-- Add external_emails table to store additional email addresses for users
CREATE TABLE IF NOT EXISTS user_emails (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(email)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_emails_email ON user_emails(email);
CREATE INDEX IF NOT EXISTS idx_user_emails_user_id ON user_emails(user_id);

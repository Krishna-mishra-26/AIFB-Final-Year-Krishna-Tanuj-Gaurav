CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone_no VARCHAR(15),
    is_premium BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    amount NUMERIC(15, 2) NOT NULL,
    description TEXT,
    category VARCHAR(255),
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(date);

CREATE TABLE categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('income', 'expense')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE INDEX idx_categories_type ON categories(type);

CREATE TABLE budgets (
    budget_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(category_id) ON DELETE SET NULL,
    monthly_limit NUMERIC(15, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_budgets_user_id ON budgets(user_id);
CREATE INDEX idx_budgets_category_id ON budgets(category_id);

CREATE TABLE groups (
    group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_groups_created_by ON groups(created_by);

CREATE TABLE group_members (
    group_member_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_group_members_group_id ON group_members(group_id);
CREATE INDEX idx_group_members_user_id ON group_members(user_id);

CREATE TABLE group_expenses (
    group_expense_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
    payer_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    amount NUMERIC(15, 2) NOT NULL,
    description TEXT,
    category VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_group_expenses_group_id ON group_expenses(group_id);
CREATE INDEX idx_group_expenses_payer_id ON group_expenses(payer_id);

CREATE TABLE insights (
    insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    category VARCHAR(255),
    average_spending NUMERIC(15, 2),
    forecasted_spending NUMERIC(15, 2),
    savings_recommendation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_insights_user_id ON insights(user_id);
CREATE INDEX idx_insights_category ON insights(category);

CREATE TABLE savings_goals (
    savings_goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    goal_name VARCHAR(255) NOT NULL,
    target_amount NUMERIC(15, 2) NOT NULL,
    saved_amount NUMERIC(15, 2) DEFAULT 0,
    deadline DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_savings_goals_user_id ON savings_goals(user_id);
CREATE INDEX idx_savings_goals_status ON savings_goals(status);

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'unread',
    recipients VARCHAR(10) CHECK (recipients IN ('all', 'premium', 'free')) NOT NULL DEFAULT 'all',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_recipients ON notifications(recipients);


CREATE TABLE payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    razorpay_order_id VARCHAR(255) NOT NULL,
    razorpay_payment_id VARCHAR(255),
    amount NUMERIC(15, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);


CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    razorpay_subscription_id VARCHAR(255) NOT NULL,
    plan VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

CREATE TABLE activity_logs (
    activity_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    action VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_timestamp ON activity_logs(timestamp);

CREATE TABLE admin_settings (
    admin_setting_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_name VARCHAR(255) NOT NULL,
    site_description TEXT,
    admin_name VARCHAR(255),
    admin_email VARCHAR(255),
    admin_phone VARCHAR(15),
    admin_avatar VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_admin_settings_created_at ON admin_settings(created_at);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with `updated_at`
DO $$ 
DECLARE 
    table_name TEXT;
BEGIN 
    FOR table_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename IN (
            'users', 'transactions', 'categories', 'budgets', 'groups', 
            'group_members', 'group_expenses', 'settlements', 'insights', 
            'savings_goals', 'notifications', 'payments', 'subscriptions', 
            'activity_logs', 'admin_settings'
        )
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%1$s_updated_at
            BEFORE UPDATE ON %1$s
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', table_name);
    END LOOP;
END $$;

-- Insert a user
INSERT INTO users (email, password, phone_no)
VALUES ('john.doe@example.com', 'password123',  '+1234567890');

-- Insert a transaction
INSERT INTO transactions (user_id, amount, description, category, date)
VALUES (
    (SELECT user_id FROM users WHERE email = 'john.doe@example.com'),
    100.50,
    'Groceries',
    'Food',
    '2023-10-01'
);

-- Insert a category
INSERT INTO categories (user_id, name, type)
VALUES (
    (SELECT user_id FROM users WHERE email = 'john.doe@example.com'),
    'Groceries',
    'expense'
);

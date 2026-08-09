-- VCH Database Schema

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(100),
    avatar VARCHAR(200),
    is_verified BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    referral_code VARCHAR(8) UNIQUE NOT NULL,
    referred_by INTEGER,
    referral_count INTEGER DEFAULT 0,
    agent_level VARCHAR(20) DEFAULT 'none',
    agent_salary_earned FLOAT DEFAULT 0,
    balance FLOAT DEFAULT 0,
    total_deposited FLOAT DEFAULT 0,
    total_withdrawn FLOAT DEFAULT 0,
    total_earned FLOAT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    last_activity DATETIME,
    FOREIGN KEY (referred_by) REFERENCES users(id)
);

-- Vehicles Table
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    brand VARCHAR(50) NOT NULL,
    image VARCHAR(200),
    rental_price FLOAT NOT NULL,
    daily_earning FLOAT NOT NULL,
    rental_period INTEGER DEFAULT 30,
    total_profit FLOAT,
    is_active BOOLEAN DEFAULT 1,
    is_available BOOLEAN DEFAULT 1,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Rentals Table
CREATE TABLE IF NOT EXISTS rentals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rental_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    daily_earning FLOAT NOT NULL,
    total_profit FLOAT NOT NULL,
    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME,
    completed_at DATETIME,
    status VARCHAR(20) DEFAULT 'active',
    days_elapsed INTEGER DEFAULT 0,
    total_earned FLOAT DEFAULT 0,
    last_earning_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    amount FLOAT NOT NULL,
    fee FLOAT DEFAULT 0,
    net_amount FLOAT NOT NULL,
    reference VARCHAR(100),
    description VARCHAR(200),
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Service History Table
CREATE TABLE IF NOT EXISTS service_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    type VARCHAR(20) DEFAULT 'daily_servicing',
    earning FLOAT DEFAULT 50,
    service_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Referral Bonuses Table
CREATE TABLE IF NOT EXISTS referral_bonuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    referred_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    type VARCHAR(20) DEFAULT 'signup_bonus',
    is_paid BOOLEAN DEFAULT 0,
    paid_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES users(id),
    FOREIGN KEY (referred_id) REFERENCES users(id)
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    is_read BOOLEAN DEFAULT 0,
    read_at DATETIME,
    link VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    ip_address VARCHAR(50),
    user_agent VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_referral_code ON users(referral_code);
CREATE INDEX idx_rentals_user_id ON rentals(user_id);
CREATE INDEX idx_rentals_status ON rentals(status);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_service_history_user_id ON service_history(user_id);
CREATE INDEX idx_referral_bonuses_referrer ON referral_bonuses(referrer_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
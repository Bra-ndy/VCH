-- Seed data for VCH Platform

-- Insert Vehicles
INSERT OR IGNORE INTO vehicles (name, brand, rental_price, daily_earning, rental_period, total_profit, sort_order, is_active, is_available) VALUES
('Ferrari', 'Ferrari', 10000, 500, 30, 5000, 1, 1, 1),
('Porsche', 'Porsche', 8000, 400, 30, 4000, 2, 1, 1),
('Jaguar', 'Jaguar', 7000, 350, 30, 3500, 3, 1, 1),
('Mercedes-Benz', 'Mercedes-Benz', 5500, 290, 30, 3200, 4, 1, 1),
('BMW', 'BMW', 4000, 230, 30, 2900, 5, 1, 1),
('Isuzu', 'Isuzu', 3500, 200, 30, 2500, 6, 1, 1),
('Mazda', 'Mazda', 3000, 170, 30, 2100, 7, 1, 1),
('Toyota', 'Toyota', 2500, 150, 30, 2000, 8, 1, 1);

-- Create an admin user (password: admin123)
-- Note: In production, change this password immediately
INSERT OR IGNORE INTO users (user_id, username, email, phone, password_hash, full_name, referral_code, is_verified, is_active, agent_level) 
VALUES ('VCHADMIN1', 'admin', 'admin@vch.com', '254700000001', 'pbkdf2:sha256:260000$WcB8dX5F8d9d6e7f$1234567890abcdef', 'System Admin', 'ADMIN123', 1, 1, 'level2');

-- Insert default settings
-- Note: This is just a placeholder. Actual settings are in config.py
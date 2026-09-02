CREATE DATABASE shopsense_ai;
USE shopsense_ai;
SHOW DATABASES;
CREATE TABLE shops (
    shop_id INT AUTO_INCREMENT PRIMARY KEY,
    shop_name VARCHAR(100) NOT NULL,
    shop_type VARCHAR(50) NOT NULL,
    owner_name VARCHAR(100),
    phone VARCHAR(20),
    address VARCHAR(255),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
SHOW TABLES;
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    cost_price DECIMAL(10,2) NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) DEFAULT 'piece',
    is_active BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (shop_id)
        REFERENCES shops(shop_id)
);
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,
    customer_name VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (shop_id)
        REFERENCES shops(shop_id)
);
CREATE TABLE sales (
    sale_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,
    customer_id INT NULL,
    sale_datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_method ENUM('Cash', 'UPI', 'Card', 'Other') DEFAULT 'Cash',
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (shop_id)
        REFERENCES shops(shop_id),

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);
CREATE TABLE sale_items (
    sale_item_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sale_id BIGINT NOT NULL,
    product_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,

    FOREIGN KEY (sale_id)
        REFERENCES sales(sale_id),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);
CREATE TABLE inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,
    product_id INT NOT NULL,
    current_stock DECIMAL(10,2) NOT NULL DEFAULT 0,
    reorder_level DECIMAL(10,2) DEFAULT 10,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (shop_id)
        REFERENCES shops(shop_id),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    UNIQUE (shop_id, product_id)
);
CREATE TABLE expenses (
    expense_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,
    expense_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,

    FOREIGN KEY (shop_id)
        REFERENCES shops(shop_id)
);
INSERT INTO shops
(shop_name, shop_type, owner_name, phone, address, city)
VALUES
(
    'Sri Vinayaga Tea Shop',
    'Tea Shop',
    'Ravi',
    '9876543210',
    'Main Road',
    'Chennai'
);
INSERT INTO products
(shop_id, product_name, category, cost_price, selling_price, unit)
VALUES
(1, 'Tea', 'Beverage', 7.00, 15.00, 'cup'),

(1, 'Coffee', 'Beverage', 10.00, 20.00, 'cup'),

(1, 'Vada', 'Snacks', 8.00, 15.00, 'piece'),

(1, 'Bajji', 'Snacks', 7.00, 15.00, 'piece'),

(1, 'Samosa', 'Snacks', 8.00, 15.00, 'piece'),

(1, 'Bun', 'Bakery', 10.00, 20.00, 'piece'),

(1, 'Biscuits', 'Snacks', 5.00, 10.00, 'packet'),

(1, 'Fresh Juice', 'Beverage', 20.00, 40.00, 'glass');
INSERT INTO inventory
(shop_id, product_id, current_stock, reorder_level)
VALUES
(1, 1, 200, 50),
(1, 2, 100, 30),
(1, 3, 150, 40),
(1, 4, 100, 30),
(1, 5, 100, 30),
(1, 6, 50, 15),
(1, 7, 80, 20),
(1, 8, 40, 10);
SELECT * FROM shops;
SELECT * FROM products;
SELECT * FROM inventory;
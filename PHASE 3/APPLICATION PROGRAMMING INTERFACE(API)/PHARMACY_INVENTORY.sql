-- TABLE : USER 
CREATE TABLE app_user (
    user_id         SERIAL PRIMARY KEY,
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    dob             DATE NOT NULL,
    role           VARCHAR(20) NOT NULL,
    email          VARCHAR(100) UNIQUE NOT NULL,
    phone          VARCHAR(20),
    address        VARCHAR(200),
    password_hash  VARCHAR(100) NOT NULL, 
    gender         CHAR(1) CHECK (gender IN ('M', 'F', 'O')),
    country        VARCHAR(50),
    reg_date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLE: STOCK_CONTROLLER
CREATE TABLE stock_controller (
    controller_id   SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL UNIQUE, 
    CONSTRAINT fk_controller_user 
        FOREIGN KEY (user_id) 
        REFERENCES app_user(user_id)
);

-- TABLE : SUPPLIER
CREATE TABLE supplier (
    supplier_id     SERIAL PRIMARY KEY,
    sname           VARCHAR(100) NOT NULL,
    email           VARCHAR(100),
    address         VARCHAR(200),
    phone           VARCHAR(20),
    status          VARCHAR(20) DEFAULT 'ACTIVE',
    payment_term    VARCHAR(30),
    reg_number      VARCHAR(50) UNIQUE
);

-- TABLE : PRODUCT
CREATE TABLE product (
    product_id      SERIAL PRIMARY KEY,
    pname           VARCHAR(100) NOT NULL,
    description     TEXT,
    dosage          VARCHAR(50),
    category        VARCHAR(30),
    price           DECIMAL(10,2) NOT NULL,
    supplier_id     INTEGER NOT NULL,
    reorder_qty     INTEGER,
    storage_req     VARCHAR(200),
    CONSTRAINT fk_product_supplier 
        FOREIGN KEY (supplier_id) 
        REFERENCES supplier(supplier_id)
);

-- TABLE : STOCK_BATCH
CREATE TABLE stock_batch (
    batch_id            SERIAL PRIMARY KEY,
    product_id          INTEGER NOT NULL,
    batch_number        VARCHAR(30) UNIQUE NOT NULL,
    manuf_date          DATE,
    expiry_date         DATE NOT NULL,
    storage_conditions  VARCHAR(200),
    quantity            INTEGER DEFAULT 0,
    unit_cost           DECIMAL(10,2),
    controller_id       INTEGER NOT NULL,
    received_date       DATE DEFAULT CURRENT_DATE,
    CONSTRAINT fk_batch_product 
        FOREIGN KEY (product_id) 
        REFERENCES product(product_id),
    CONSTRAINT fk_batch_controller 
        FOREIGN KEY (controller_id) 
        REFERENCES stock_controller(controller_id)
);

-- TABLE : PURCHASE_ORDER
CREATE TABLE purchase_order (
    order_id        SERIAL PRIMARY KEY,
    order_date      DATE DEFAULT CURRENT_DATE,
    supplier_id     INTEGER NOT NULL,
    delivery_date   DATE,
    status          VARCHAR(20) DEFAULT 'PENDING',
    CONSTRAINT fk_po_supplier 
        FOREIGN KEY (supplier_id) 
        REFERENCES supplier(supplier_id)
);

-- TABLE : PURCHASE_ORDER_LINE
CREATE TABLE purchase_order_line (
    order_id         INTEGER NOT NULL,
    product_id       INTEGER NOT NULL,
    quantity_ordered INTEGER NOT NULL,
    unit_cost        DECIMAL(10,2) NOT NULL,
    CONSTRAINT pk_po_line PRIMARY KEY (order_id, product_id),
    CONSTRAINT fk_po_line_order 
        FOREIGN KEY (order_id) 
        REFERENCES purchase_order(order_id),
    CONSTRAINT fk_po_line_product 
        FOREIGN KEY (product_id) 
        REFERENCES product(product_id)
);

-- TABLE : STOCK_CONTROLLER
CREATE TABLE stock_controller (
    controller_id   SERIAL PRIMARY KEY,
    user_id         INTEGER UNIQUE NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE
);

-- TABLE : PURCHASE_ORDER
CREATE TABLE purchase_order (
    order_id        SERIAL PRIMARY KEY,
    supplier_id     INTEGER NOT NULL REFERENCES supplier(supplier_id) ON DELETE RESTRICT,
    order_date      DATE DEFAULT CURRENT_DATE,
    delivery_date   DATE,
    status          VARCHAR(50) DEFAULT 'Pending'   -- Pending, Shipped, Delivered, Cancelled
);

-- SAMPLE DATA

-- Insert Users 
INSERT INTO app_user (first_name, last_name, dob, role, email, phone, address, password_hash, gender, country) VALUES
('John', 'Smith', '1985-05-15', 'Pharmacist', 'john.smith@pharmacy.com', '555-0101', '123 Main St', 'hashed_pwd_1', 'M', 'USA'),
('Jane', 'Doe', '1990-10-20', 'Patient', 'jane.doe@email.com', '555-0102', '456 Oak Ave', 'hashed_pwd_2', 'F', 'USA'),
('Bob', 'Johnson', '1988-03-12', 'Stock_Controller', 'bob.johnson@pharmacy.com', '555-0103', '789 Pine Rd', 'hashed_pwd_3', 'M', 'USA'),
('Alice', 'Brown', '1995-07-08', 'Patient', 'alice.brown@email.com', '555-0104', '321 Elm St', 'hashed_pwd_4', 'F', 'USA'),
('Sarah', 'Wilson', '1982-11-25', 'Pharmacist', 'sarah.wilson@pharmacy.com', '555-0105', '654 Maple Dr', 'hashed_pwd_5', 'F', 'USA');

-- Insert Stock Controllers 
INSERT INTO stock_controller (user_id) 
SELECT user_id FROM app_user WHERE role = 'Stock_Controller';

-- Insert Suppliers
INSERT INTO supplier (sname, email, address, phone, status, payment_term, reg_number) VALUES
('MedSupply Co', 'orders@medsupply.com', '100 Industrial Pkwy', '555-1000', 'ACTIVE', 'Net 30', 'REG001'),
('PharmaDistributors', 'contact@pharmadist.com', '200 Commerce Blvd', '555-2000', 'ACTIVE', 'Net 45', 'REG002');

-- Insert Products
INSERT INTO product (pname, description, dosage, category, price, supplier_id, reorder_qty, storage_req) VALUES
('Amoxicillin 500mg', 'Antibiotic for bacterial infections', '500mg', 'Antibiotic', 25.99, 1, 100, 'Room temperature'),
('Lisinopril 10mg', 'Blood pressure medication', '10mg', 'Cardiovascular', 35.50, 2, 50, 'Room temperature'),
('Atorvastatin 20mg', 'Cholesterol medication', '20mg', 'Cardiovascular', 45.75, 2, 75, 'Room temperature');

-- Insert Stock Batches
INSERT INTO stock_batch (product_id, batch_number, manuf_date, expiry_date, storage_conditions, quantity, unit_cost, controller_id, received_date) VALUES
(1, 'BATCH001', '2024-01-15', '2026-01-15', 'Cool dry place', 500, 15.00, 
    (SELECT controller_id FROM stock_controller LIMIT 1), '2024-02-01'),
(1, 'BATCH002', '2024-03-10', '2026-03-10', 'Cool dry place', 300, 16.00, 
    (SELECT controller_id FROM stock_controller LIMIT 1), '2024-04-01'),
(2, 'BATCH003', '2024-02-20', '2025-12-20', 'Room temperature', 200, 22.00, 
    (SELECT controller_id FROM stock_controller LIMIT 1), '2024-03-15');

-- Insert Purchase Orders
INSERT INTO purchase_order (order_date, supplier_id, delivery_date, status) VALUES
('2024-01-20', 1, '2024-01-30', 'COMPLETED'),
('2024-03-05', 2, '2024-03-15', 'COMPLETED');

-- Insert Purchase Order Lines
INSERT INTO purchase_order_line (order_id, product_id, quantity_ordered, unit_cost) VALUES
(1, 1, 500, 15.00),
(2, 2, 200, 22.00),
(2, 3, 150, 30.00);


CREATE TABLE supplier (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    address TEXT,
    status VARCHAR(50),
    payment_terms VARCHAR(100),
    phone VARCHAR(50),
    registration_number VARCHAR(100) UNIQUE
);


CREATE TABLE allergy (
    allergy_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    allergy_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id) ON DELETE CASCADE
);


INSERT INTO supplier (supplier_name, email, address, status, payment_terms, phone, registration_number) VALUES 
('Twitterbridge', 'gbemlott0@devhub.com', '4047 Marquette Street', 'suspended', 'COD', '523-756-9109', 673774),
('Zoonoodle', 'dstandley1@issuu.com', '45 Leroy Hill', 'inactive', 'COD', '132-703-4733', 539215),
('Skivee', 'kmcgee2@mayoclinic.com', '02 Ridge Oak Place', 'inactive', 'Net 15', '466-683-7814', 269432),
('Kwinu', 'ldicte3@multiply.com', '08 Golf Road', 'inactive', 'COD', '984-351-2731', 988524),
('Gabspot', 'sreiglar4@edublogs.org', '63120 International Drive', 'active', 'Net 30', '479-296-3729', 151385),
('Wikizz', 'kprestedge5@phpbb.com', '3 Toban Circle', 'suspended', 'Net60', '183-189-7569', 454804),
('Quinu', 'lchristophle6@ameblo.jp', '45 Bonner Place', 'suspended', 'Net 30', '466-505-5379', 589775),
('Divape', 'mionesco7@nifty.com', '24 Starling Junction', 'suspended', 'COD', '739-847-2349', 129026),
('Jaloo', 'msheeres8@loc.gov', '6143 Grim Parkway', 'inactive', 'COD', '649-941-9105', 682836),
('Brainsphere', 'bboggs9@xing.com', '319 Scofield Avenue', 'suspended', 'Net 15', '498-135-7780', 316379);


INSERT INTO allergy (patient_id, allergy_name) VALUES 
(1, 'Penicillin'),
(1, 'Peanuts'),
(2, 'Pollen'),
(3, 'Dust mites'),
(4, 'Latex'),
(5, 'Shellfish');
  

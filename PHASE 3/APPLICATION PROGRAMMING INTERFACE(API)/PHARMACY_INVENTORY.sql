--PHARMACY INVENTORY DATABASE: GROUP 10

\c postgres

DROP DATABASE IF EXISTS Pharmacy_Inventory;
CREATE DATABASE Pharmacy_Inventory;

\c Pharmacy_Inventory


-- TABLE : USER 
CREATE TABLE users (
    users_id       BIGSERIAL PRIMARY KEY,
    first_name     VARCHAR(50) NOT NULL,
    last_name      VARCHAR(50) NOT NULL,
    date_of_birth  DATE NOT NULL,
    roles          VARCHAR(20) NOT NULL,
    email          VARCHAR(100) UNIQUE NOT NULL,
    phone          VARCHAR(20),
    home_address        VARCHAR(200),
    password_hash  VARCHAR(100) NOT NULL, 
    gender         CHAR(1) CHECK (gender IN ('M', 'F', 'O')),
    country        VARCHAR(50),
    reg_date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 

--TABLE : PATIENT
CREATE TABLE patient (
    patient_id        BIGSERIAL PRIMARY KEY,
    users_id          INTEGER NOT NULL,
    id_number         VARCHAR(30),
    CONSTRAINT fk_patient_users  FOREIGN KEY (users_id) REFERENCES users(users_id)ON DELETE CASCADE
);

-- TABLE: ALLERGY
CREATE TABLE allergy(
    allergy_id      BIGSERIAL PRIMARY KEY,
    patient_id      INTEGER NOT NULL,
    allergy_name    VARCHAR(50) not null,
    CONSTRAINT fk_allergy_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id) ON DELETE CASCADE

);

--TABLE : PHARMACIST
CREATE TABLE pharmacist(
    pharmacist_id       BIGSERIAL PRIMARY KEY,
    users_id            INTEGER NOT NULL,
    license_number      VARCHAR(30) UNIQUE NOT NULL,
    status              VARCHAR(20) DEFAULT 'ACTIVE',
    CONSTRAINT fk_pharmacist_users FOREIGN KEY (users_id) REFERENCES users(users_id)

);


-- TABLE: STOCK_CONTROLLER
CREATE TABLE stock_controller (
    controller_id   BIGSERIAL PRIMARY KEY,
    users_id        INTEGER NOT NULL UNIQUE, 
    CONSTRAINT fk_controller_users FOREIGN KEY (users_id) REFERENCES users(users_id)
);

-- TABLE : SUPPLIER
CREATE TABLE supplier (
    supplier_id     BIGSERIAL PRIMARY KEY,
    supplier_name           VARCHAR(100) NOT NULL,
    email           VARCHAR(100),
    company_address VARCHAR(200),
    phone           VARCHAR(20),
    status          VARCHAR(20) DEFAULT 'ACTIVE',
    payment_term    VARCHAR(30),
    reg_number      VARCHAR(50) UNIQUE
);

-- TABLE : PRODUCT
CREATE TABLE product (
    product_id      BIGSERIAL PRIMARY KEY,
    product_name    VARCHAR(100) NOT NULL,
    description     TEXT,
    dosage          VARCHAR(50),
    category        VARCHAR(30),
    price           DECIMAL(10,2) NOT NULL,
    supplier_id     INT NOT NULL,
    reorder_qty     INT,
    storage_req     VARCHAR(200),
    CONSTRAINT fk_product_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
);

-- TABLE : STOCK_BATCH
CREATE TABLE stock_batch (
    batch_id            BIGSERIAL PRIMARY KEY,
    product_id          INT NOT NULL,
    batch_number        VARCHAR(30) UNIQUE NOT NULL,
    manuf_date          DATE,
    expiry_date         DATE NOT NULL,
    storage_conditions  VARCHAR(200),
    quantity            INT DEFAULT 0,
    unit_cost           DECIMAL(10,2),
    controller_id       INT NOT NULL,
    received_date       DATE DEFAULT CURRENT_DATE,
    CONSTRAINT fk_batch_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT fk_batch_controller FOREIGN KEY (controller_id) REFERENCES stock_controller(controller_id)
);

-- TABLE : PURCHASE_ORDER
CREATE TABLE purchase_order (
    order_id        SERIAL PRIMARY KEY,
    order_date      DATE DEFAULT CURRENT_DATE,
    supplier_id     INT NOT NULL,
    delivery_date   DATE,
    status          VARCHAR(20) DEFAULT 'PENDING',
    CONSTRAINT fk_po_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
);

-- TABLE : PURCHASE_ORDER_LINE
CREATE TABLE purchase_order_line (
    order_id         INT NOT NULL,
    product_id       INT NOT NULL,
    quantity_ordered INT NOT NULL,
    unit_cost        DECIMAL(10,2) NOT NULL,
    --composite key
    CONSTRAINT pk_po_line PRIMARY KEY (order_id, product_id),
    CONSTRAINT fk_po_line_order FOREIGN KEY (order_id) REFERENCES purchase_order(order_id),
    CONSTRAINT fk_po_line_product FOREIGN KEY (product_id) REFERENCES product(product_id)
);

--TABLE : PRESCRIPTION 
CREATE TABLE prescription (
    prescription_id        BIGSERIAL PRIMARY KEY,
    date_issued            DATE DEFAULT CURRENT_DATE,
    patient_id             INT NOT NULL,
    pharmacist_id          INT NOT NULL,
    doctor_name            VARCHAR(100),
    hospital_name          VARCHAR(100),
    CONSTRAINT fk_prescription_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    CONSTRAINT fk_prescription_pharmacist FOREIGN KEY (pharmacist_id) REFERENCES pharmacist(pharmacist_id)
);

-- TABLE : PRESCRIPTION_LINE
CREATE TABLE prescription_line (
    prescription_id     INT NOT NULL,
    product_id          INT NOT NULL,
    quantity            INT NOT NULL,
    dosage_description  VARCHAR(200),
    -- Composite Primary Key
    CONSTRAINT pk_pres_line PRIMARY KEY (prescription_id, product_id),
    CONSTRAINT fk_pres_line_pres FOREIGN KEY (prescription_id) REFERENCES prescription(prescription_id)ON DELETE CASCADE,
    CONSTRAINT fk_pres_line_product FOREIGN KEY (product_id) REFERENCES product(product_id)
);

-- TABLE : TRANSACTION 
CREATE TABLE sale_transaction (
    transaction_id  BIGSERIAL PRIMARY KEY,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type            VARCHAR(20) NOT NULL, 
    patient_id      INT,
    pharmacist_id   INT NOT NULL,
    CONSTRAINT fk_transaction_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    CONSTRAINT fk_transaction_pharmacist FOREIGN KEY (pharmacist_id) REFERENCES pharmacist(pharmacist_id)
);

-- TABLE 14: SALES_LINE (Triple composite key)
CREATE TABLE sales_line (
    transaction_id  INT NOT NULL,
    product_id      INT NOT NULL,
    batch_id        INT NOT NULL,
    quantity_sold   INT NOT NULL,
    selling_price   DECIMAL(10,2) NOT NULL,
    -- Triple Composite Primary Key
    CONSTRAINT pk_sales_line PRIMARY KEY (transaction_id, product_id, batch_id),
    CONSTRAINT fk_sales_line_transaction FOREIGN KEY (transaction_id) REFERENCES sale_transaction(transaction_id),
    CONSTRAINT fk_sales_line_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT fk_sales_line_batch FOREIGN KEY (batch_id) REFERENCES stock_batch(batch_id),
    CONSTRAINT chk_quantity_sold CHECK (quantity_sold > 0)
);

-- TABLE : CONTROLLED LOG
CREATE TABLE controlled_log (
    log_id          BIGSERIAL PRIMARY KEY,
    log_date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    product_id      INT NOT NULL,
    batch_id        INT NOT NULL,
    pharmacist_id   INT NOT NULL,
    patient_id      INT NOT NULL,
    status          VARCHAR(20),
    action_type     VARCHAR(20) NOT NULL,  
    quantity        INT NOT NULL,
    CONSTRAINT fk_log_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT fk_log_batch FOREIGN KEY (batch_id) REFERENCES stock_batch(batch_id),
    CONSTRAINT fk_log_pharmacist FOREIGN KEY (pharmacist_id) REFERENCES pharmacist(pharmacist_id),
    CONSTRAINT fk_log_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

--INDEXES
CREATE INDEX idx_product_supplier_id ON product(supplier_id);
CREATE INDEX idx_stock_batch_product_id ON stock_batch(product_id);
CREATE INDEX idx_stock_batch_controller_id ON stock_batch(controller_id);
CREATE INDEX idx_stock_batch_expiry ON stock_batch(expiry_date);
CREATE INDEX idx_prescription_patient_id ON prescription(patient_id);
CREATE INDEX idx_prescription_pharmacist_id ON prescription(pharmacist_id);
CREATE INDEX idx_transaction_date ON transaction(transaction_date);
CREATE INDEX idx_transaction_patient_id ON transaction(patient_id);
CREATE INDEX idx_purchase_order_supplier_id ON purchase_order(supplier_id);
CREATE INDEX idx_composite_sales ON sales_line(transaction_id, product_id, batch_id);

--VIEWS
-- View 1: Low stock products (for reordering)
CREATE VIEW low_stock_view AS
SELECT 
    p.product_id,
    p.product_name,
    COALESCE(SUM(sb.quantity), 0) AS current_stock,
    p.reorder_quantity
FROM product p
LEFT JOIN stock_batch sb ON p.product_id = sb.product_id
GROUP BY p.product_id, p.product_name, p.reorder_quantity
HAVING COALESCE(SUM(sb.quantity), 0) <= p.reorder_quantity;

-- View 2: Expiring products (next 30 days)
CREATE VIEW expiring_products_view AS
SELECT 
    p.product_id,
    p.product_name,
    sb.batch_number,
    sb.expiry_date,
    sb.quantity,
    (sb.expiry_date - CURRENT_DATE) AS days_until_expiry
FROM stock_batch sb
JOIN product p ON sb.product_id = p.product_id
WHERE sb.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
ORDER BY sb.expiry_date;

-- View 3: Daily sales summary
CREATE VIEW daily_sales_summary AS
SELECT 
    DATE(t.transaction_date) AS sale_date,
    COUNT(DISTINCT t.transaction_id) AS num_transactions,
    SUM(t.total_amount) AS total_revenue,
    COUNT(DISTINCT t.patient_id) AS unique_customers
FROM transaction t
WHERE t.type = 'sale'
GROUP BY DATE(t.transaction_date)
ORDER BY sale_date DESC;

-- SAMPLE DATA

BEGIN;

-- 1. USERS 
INSERT INTO USERS (first_name, last_name, date_of_birth, roles, email, phone, home_address, password_hash, gender, country, reg_date) VALUES
('John', 'Smith', '1985-03-15', 'PATIENT', 'john.smith@email.com', '555-0101', '123 Main St, Boston, MA 02101', 'hash_pwd_001', 'M', 'USA', '2023-01-15 10:30:00'),
('Emma', 'Johnson', '1990-07-22', 'PATIENT', 'emma.j@email.com', '555-0102', '456 Oak Ave, New York, NY 10001', 'hash_pwd_002', 'F', 'USA', '2023-02-20 14:15:00'),
('Robert', 'Williams', '1978-11-08', 'PHARMACIST', 'robert.williams@pharmacy.com', '555-0103', '789 Pine Rd, Chicago, IL 60601', 'hash_pwd_003', 'M', 'USA', '2022-11-01 09:00:00'),
('Sarah', 'Brown', '1982-05-30', 'PHARMACIST', 'sarah.brown@pharmacy.com', '555-0104', '321 Elm St, Houston, TX 77001', 'hash_pwd_004', 'F', 'USA', '2022-12-10 11:20:00'),
('Michael', 'Davis', '1995-09-12', 'STOCK_CONTROLLER', 'michael.davis@pharmacy.com', '555-0105', '654 Maple Dr, Phoenix, AZ 85001', 'hash_pwd_005', 'M', 'USA', '2023-03-05 08:45:00'),
('Jessica', 'Miller', '1988-12-03', 'STOCK_CONTROLLER', 'jessica.miller@pharmacy.com', '555-0106', '987 Cedar Ln, Philadelphia, PA 19101', 'hash_pwd_006', 'F', 'USA', '2023-01-20 13:10:00'),
('David', 'Wilson', '1975-04-18', 'PATIENT', 'david.wilson@email.com', '555-0107', '147 Birch St, San Antonio, TX 78201', 'hash_pwd_007', 'M', 'USA', '2023-04-10 16:30:00'),
('Lisa', 'Martinez', '1992-08-25', 'PHARMACIST', 'lisa.martinez@pharmacy.com', '555-0108', '258 Spruce Ave, San Diego, CA 92101', 'hash_pwd_008', 'F', 'USA', '2023-02-28 10:00:00'),
('James', 'Anderson', '1980-06-14', 'STOCK_CONTROLLER', 'james.anderson@pharmacy.com', '555-0109', '369 Willow Way, Dallas, TX 75201', 'hash_pwd_009', 'M', 'USA', '2023-01-05 12:15:00'),
('Maria', 'Garcia', '1987-10-02', 'PATIENT', 'maria.garcia@email.com', '555-0110', '741 Ash Ct, San Jose, CA 95101', 'hash_pwd_010', 'F', 'USA', '2023-05-15 09:30:00');

-- 2. PATIENT 
INSERT INTO patient (users_id, id_number) VALUES
(1, 'PAT-001-1985'),
(2, 'PAT-002-1990'),
(7, 'PAT-003-1975'),
(10, 'PAT-004-1987');

-- 3. ALLERGY 
INSERT INTO allergy (patient_id, allergy_name) VALUES
(1, 'Penicillin'),
(1, 'Sulfa Drugs'),
(2, 'Aspirin'),
(2, 'Ibuprofen'),
(3, 'Codeine'),
(3, 'Morphine'),
(4, 'Latex'),
(4, 'Amoxicillin');

-- 4. PHARMACIST 
INSERT INTO pharmacist (users_id, license_number, status) VALUES
(3, 'PHAR-12345-USA', 'ACTIVE'),
(4, 'PHAR-67890-USA', 'ACTIVE'),
(8, 'PHAR-24680-USA', 'ACTIVE');

-- 5. STOCK_CONTROLLER 
INSERT INTO stock_controller (users_id) VALUES
(5),
(6),
(9);

-- 6. SUPPLIER
INSERT INTO supplier (supplier_name, email, company_address, phone, status, payment_term, reg_number) VALUES
('MediSource International', 'orders@medisource.com', '100 Pharma Blvd, Newark, NJ 07101', '800-555-1000', 'ACTIVE', 'Net 30', 'REG-001-ABC'),
('HealthWholesale Corp', 'sales@healthwholesale.com', '200 Medical Dr, Los Angeles, CA 90001', '800-555-2000', 'ACTIVE', 'Net 45', 'REG-002-DEF'),
('Global Pharma Distributors', 'contact@globalpharma.com', '300 Drug St, Miami, FL 33101', '800-555-3000', 'ACTIVE', 'Net 30', 'REG-003-GHI'),
('CareMedical Supply', 'orders@caremedical.com', '400 Health Ave, Seattle, WA 98101', '800-555-4000', 'INACTIVE', 'Net 60', 'REG-004-JKL'),
('Vitalis Pharmaceuticals', 'purchase@vitalis.com', '500 Remedy Rd, Boston, MA 02101', '800-555-5000', 'ACTIVE', 'Net 30', 'REG-005-MNO');

-- 7. PRODUCT
INSERT INTO product (product_name, description, dosage, category, price, supplier_id, reorder_qty, storage_req) VALUES
('Amoxicillin 500mg', 'Antibiotic for bacterial infections', '500mg', 'Antibiotics', 25.99, 1, 100, 'Store at room temperature 20-25°C'),
('Lisinopril 10mg', 'ACE inhibitor for hypertension', '10mg', 'Cardiovascular', 35.50, 2, 50, 'Keep away from moisture'),
('Metformin 850mg', 'Oral diabetes medication', '850mg', 'Endocrinology', 18.75, 1, 75, 'Store in a dry place'),
('Azithromycin 250mg', 'Macrolide antibiotic', '250mg', 'Antibiotics', 42.30, 3, 60, 'Refrigerate at 2-8°C'),
('Omeprazole 20mg', 'Proton pump inhibitor for GERD', '20mg', 'Gastrointestinal', 28.90, 2, 80, 'Store below 30°C'),
('Atorvastatin 40mg', 'Statin for cholesterol', '40mg', 'Cardiovascular', 52.25, 4, 45, 'Protect from light'),
('Amoxiclav 875mg', 'Amoxicillin with Clavulanate', '875mg', 'Antibiotics', 67.50, 1, 40, 'Store at room temperature'),
('Paracetamol 500mg', 'Analgesic and antipyretic', '500mg', 'Pain Relief', 12.99, 5, 200, 'Store in a cool dry place'),
('Ibuprofen 400mg', 'NSAID for pain and inflammation', '400mg', 'Pain Relief', 15.50, 5, 150, 'Keep away from children'),
('Cetirizine 10mg', 'Antihistamine for allergies', '10mg', 'Antihistamines', 22.75, 3, 90, 'Store at room temperature');

-- 8. STOCK_BATCH 
INSERT INTO stock_batch (product_id, batch_number, manuf_date, expiry_date, storage_conditions, quantity, unit_cost, controller_id, received_date) VALUES
(1, 'AMOX-2024-001', '2024-01-15', '2025-12-31', 'Room temperature', 250, 15.50, 1, '2024-01-20'),
(1, 'AMOX-2024-002', '2024-03-10', '2026-02-28', 'Room temperature', 150, 16.00, 1, '2024-03-15'),
(2, 'LIS-2024-001', '2024-02-01', '2025-08-31', 'Dry place', 80, 22.00, 2, '2024-02-05'),
(3, 'MET-2024-001', '2024-01-20', '2025-07-31', 'Dry place', 120, 11.25, 1, '2024-01-25'),
(4, 'AZI-2024-001', '2024-03-01', '2025-09-30', 'Refrigerated', 45, 28.50, 3, '2024-03-10'),
(5, 'OME-2024-001', '2024-02-15', '2025-11-30', 'Room temperature', 95, 19.00, 2, '2024-02-20'),
(6, 'ATO-2024-001', '2024-01-10', '2025-06-30', 'Protected from light', 30, 38.00, 1, '2024-01-15'),
(7, 'AMC-2024-001', '2024-03-05', '2025-12-31', 'Room temperature', 55, 45.00, 3, '2024-03-12'),
(8, 'PAR-2024-001', '2024-02-20', '2026-01-31', 'Cool dry place', 300, 7.50, 2, '2024-02-25'),
(9, 'IBU-2024-001', '2024-01-25', '2025-10-31', 'Room temperature', 200, 9.00, 1, '2024-01-30'),
(10, 'CET-2024-001', '2024-03-15', '2025-12-31', 'Room temperature', 85, 14.00, 3, '2024-03-20'),
(1, 'AMOX-2023-003', '2023-08-10', '2024-12-15', 'Room temperature', 45, 14.75, 1, '2023-08-15'),
(8, 'PAR-2023-002', '2023-09-05', '2024-11-20', 'Cool dry place', 120, 7.00, 2, '2023-09-10'),
(2, 'LIS-2023-002', '2023-10-12', '2024-09-30', 'Dry place', 25, 21.50, 2, '2023-10-15');

-- 9. PURCHASE_ORDER
INSERT INTO purchase_order (order_date, supplier_id, delivery_date, status) VALUES
('2024-01-15', 1, '2024-01-20', 'DELIVERED'),
('2024-02-01', 2, '2024-02-05', 'DELIVERED'),
('2024-03-01', 3, '2024-03-10', 'DELIVERED'),
('2024-04-10', 5, '2024-04-20', 'PENDING'),
('2024-03-20', 1, '2024-03-25', 'DELIVERED'),
('2024-04-05', 4, NULL, 'CANCELLED'),
('2024-05-01', 2, NULL, 'PENDING');

-- 10. PURCHASE_ORDER_LINE 
INSERT INTO purchase_order_line (order_id, product_id, quantity_ordered, unit_cost) VALUES
(1, 1, 500, 15.50),
(1, 3, 200, 11.25),
(2, 2, 150, 22.00),
(2, 5, 200, 19.00),
(3, 4, 100, 28.50),
(3, 7, 80, 45.00),
(4, 8, 400, 7.50),
(4, 9, 300, 9.00),
(5, 1, 300, 16.00),
(5, 10, 120, 14.00),
(6, 6, 60, 38.00),
(7, 2, 100, 23.00);

-- 11. PRESCRIPTION 
INSERT INTO prescription (date_issued, patient_id, pharmacist_id, doctor_name, hospital_name) VALUES
('2024-05-01', 1, 1, 'Dr. Emily Chen', 'Boston General Hospital'),
('2024-05-05', 2, 2, 'Dr. Michael Rodriguez', 'New York Medical Center'),
('2024-05-10', 3, 1, 'Dr. Sarah Wilson', 'Chicago Community Hospital'),
('2024-05-12', 1, 3, 'Dr. James Taylor', 'Boston General Hospital'),
('2024-05-15', 4, 2, 'Dr. Lisa Anderson', 'San Jose Medical Clinic'),
('2024-05-18', 2, 1, 'Dr. Robert Kim', 'New York Medical Center'),
('2024-05-20', 3, 3, 'Dr. Emily Chen', 'Chicago Community Hospital');

-- 12. PRESCRIPTION_LINE 
INSERT INTO prescription_line (prescription_id, product_id, quantity, dosage_description) VALUES
(1, 1, 30, 'Take one capsule three times daily for 10 days'),
(1, 8, 20, 'Take one tablet every 6 hours as needed for pain'),
(2, 2, 90, 'Take one tablet daily with water'),
(2, 5, 30, 'Take one capsule daily before breakfast'),
(3, 3, 60, 'Take one tablet twice daily with meals'),
(4, 4, 12, 'Take two tablets on first day, then one daily for 4 days'),
(4, 7, 20, 'Take one tablet twice daily for 7 days'),
(5, 9, 40, 'Take one tablet every 8 hours as needed'),
(5, 10, 30, 'Take one tablet daily for allergies'),
(6, 1, 28, 'Take one capsule three times daily for 7 days'),
(7, 6, 30, 'Take one tablet daily at bedtime');

-- 13. SALE_TRANSACTION 
INSERT INTO sale_transaction (transaction_date, type, patient_id, pharmacist_id) VALUES
('2024-05-02 10:30:00', 'SALE', 1, 1),
('2024-05-02 14:15:00', 'SALE', 2, 2),
('2024-05-03 11:00:00', 'SALE', NULL, 1),
('2024-05-06 09:45:00', 'SALE', 3, 1),
('2024-05-07 16:20:00', 'SALE', 1, 3),
('2024-05-10 13:30:00', 'SALE', 4, 2),
('2024-05-12 10:15:00', 'SALE', 2, 3),
('2024-05-15 15:00:00', 'SALE', NULL, 1),
('2024-05-16 11:45:00', 'RETURN', 1, 2),
('2024-05-18 09:30:00', 'SALE', 3, 1),
('2024-05-20 14:00:00', 'SALE', 4, 2);

-- 14. SALES_LINE 
INSERT INTO sales_line (transaction_id, product_id, batch_id, quantity_sold, selling_price) VALUES
(1, 1, 1, 30, 25.99),
(1, 8, 9, 20, 12.99),
(2, 2, 3, 90, 35.50),
(2, 5, 6, 30, 28.90),
(3, 8, 9, 15, 12.99),
(4, 3, 4, 60, 18.75),
(5, 4, 5, 12, 42.30),
(5, 7, 8, 20, 67.50),
(6, 9, 10, 40, 15.50),
(6, 10, 11, 30, 22.75),
(7, 1, 2, 28, 26.99),
(8, 8, 13, 10, 12.50),
(9, 1, 2, -5, 26.99),  
(10, 3, 4, 30, 18.75),
(11, 9, 10, 20, 15.50);

--CONTROLLED_LOG 
INSERT INTO controlled_log (log_date, product_id, batch_id, pharmacist_id, patient_id, status, action_type, quantity) VALUES
('2024-05-02 10:35:00', 1, 1, 1, 1, 'COMPLETED', 'DISPENSE', 30),
('2024-05-02 14:20:00', 2, 3, 2, 2, 'COMPLETED', 'DISPENSE', 90),
('2024-05-06 09:50:00', 3, 4, 1, 3, 'COMPLETED', 'DISPENSE', 60),
('2024-05-07 16:25:00', 4, 5, 3, 1, 'COMPLETED', 'DISPENSE', 12),
('2024-05-10 13:35:00', 9, 10, 2, 4, 'COMPLETED', 'DISPENSE', 40),
('2024-05-12 10:20:00', 1, 2, 3, 2, 'VERIFIED', 'DISPENSE', 28),
('2024-05-15 15:05:00', 8, 13, 1, NULL, 'COMPLETED', 'DISPENSE', 10),
('2024-05-16 11:50:00', 1, 2, 2, 1, 'COMPLETED', 'RETURN', 5),
('2024-05-18 09:35:00', 3, 4, 1, 3, 'COMPLETED', 'DISPENSE', 30),
('2024-05-20 14:05:00', 9, 10, 2, 4, 'PENDING', 'DISPENSE', 20);

COMMIT;

--QUERIES--

--QUERIES BASED ON COMPANY INFORMATION REQUIREMENTS 

-- Query 1: Get complete patient prescription history with doctor details
-- Purpose: Track all prescriptions issued to patients including doctor and pharmacist information
SELECT 
    p.prescription_id,
    CONCAT(u.first_name, ' ', u.last_name) AS patient_name,
    p.date_issued,
    p.doctor_name,
    p.hospital_name,
    CONCAT(u2.first_name, ' ', u2.last_name) AS pharmacist_name,
    COUNT(pl.product_id) AS number_of_medications
FROM prescription p
JOIN patient pa ON p.patient_id = pa.patient_id
JOIN users u ON pa.users_id = u.users_id
JOIN pharmacist ph ON p.pharmacist_id = ph.pharmacist_id
JOIN users u2 ON ph.users_id = u2.users_id
JOIN prescription_line pl ON p.prescription_id = pl.prescription_id
GROUP BY p.prescription_id, u.first_name, u.last_name, p.date_issued, 
         p.doctor_name, p.hospital_name, u2.first_name, u2.last_name
ORDER BY p.date_issued DESC;

-- Query 2: Monitor pharmacy sales performance by product category
-- Purpose: Analyze which product categories generate the most revenue
SELECT 
    pr.category,
    COUNT(DISTINCT st.transaction_id) AS number_of_transactions,
    SUM(sl.quantity_sold) AS total_units_sold,
    SUM(sl.quantity_sold * sl.selling_price) AS total_revenue,
    ROUND(AVG(sl.selling_price), 2) AS average_selling_price
FROM product pr
JOIN sales_line sl ON pr.product_id = sl.product_id
JOIN sale_transaction st ON sl.transaction_id = st.transaction_id
WHERE st.type = 'SALE'
GROUP BY pr.category
ORDER BY total_revenue DESC;

-- Query 3: Identify low stock products requiring immediate reordering
-- Purpose: Inventory management - find products below reorder threshold
SELECT 
    pr.product_id,
    pr.product_name,
    COALESCE(SUM(sb.quantity), 0) AS current_stock,
    pr.reorder_qty AS reorder_level,
    sup.sname AS supplier_name,
    sup.phone AS supplier_phone,
    (pr.reorder_qty - COALESCE(SUM(sb.quantity), 0)) AS quantity_to_order
FROM product pr
LEFT JOIN stock_batch sb ON pr.product_id = sb.product_id
JOIN supplier sup ON pr.supplier_id = sup.supplier_id
GROUP BY pr.product_id, pr.product_name, pr.reorder_qty, sup.sname, sup.phone
HAVING COALESCE(SUM(sb.quantity), 0) <= pr.reorder_qty
ORDER BY current_stock ASC;


--QUERY LIMITATIONS - ROWS & COLUMNS 

-- Query 4: Display only top 5 best-selling products with limited columns
-- Purpose: Quick view of best performing products
SELECT 
    pr.product_name,
    SUM(sl.quantity_sold) AS total_sold,
    SUM(sl.quantity_sold * sl.selling_price) AS revenue
FROM product pr
JOIN sales_line sl ON pr.product_id = sl.product_id
GROUP BY pr.product_name
ORDER BY revenue DESC
FETCH FIRST 5 ROWS ONLY;

-- Query 5: Show recent transactions with specific columns only
-- Purpose: Display recent sales without overwhelming detail
SELECT 
    st.transaction_id,
    st.transaction_date,
    CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
    st.total_amount
FROM sale_transaction st
LEFT JOIN patient pa ON st.patient_id = pa.patient_id
LEFT JOIN users u ON pa.users_id = u.users_id
WHERE st.type = 'SALE'
ORDER BY st.transaction_date DESC
LIMIT 10;

-- SORTING OPERATIONS 

-- Query 6: Products sorted by price (descending) and name (ascending)
-- Purpose: Analyze product pricing structure
SELECT 
    product_name,
    category,
    price,
    dosage
FROM product
ORDER BY price DESC, product_name ASC;

-- Query 7: Suppliers sorted by status and company name
-- Purpose: Supplier management overview
SELECT 
    sname AS supplier_name,
    status,
    payment_term,
    phone,
    email
FROM supplier
ORDER BY status DESC, sname ASC;

-- LIKE, AND, OR OPERATORS 

-- Query 8: Search for allergy patients with specific conditions
-- Purpose: Find patients with certain allergies
SELECT 
    CONCAT(u.first_name, ' ', u.last_name) AS patient_name,
    a.allergy_name,
    u.phone,
    u.email
FROM allergy a
JOIN patient p ON a.patient_id = p.patient_id
JOIN users u ON p.users_id = u.users_id
WHERE a.allergy_name LIKE '%cillin%'  -- LIKE operator
   OR a.allergy_name LIKE 'Aspirin'    -- OR operator
   AND u.country = 'USA';               -- AND operator

-- Query 9: Find products with specific price range and name pattern
-- Purpose: Product search with multiple criteria
SELECT 
    product_name,
    price,
    category,
    dosage
FROM product
WHERE price BETWEEN 20.00 AND 50.00
  AND (product_name LIKE '%mycin%' OR product_name LIKE '%pril%')
  AND category = 'Antibiotics'
ORDER BY price;

-- VARIABLES & CHARACTER FUNCTIONS 

-- Query 10: Format patient information using character functions
-- Purpose: Create formatted patient labels for correspondence
DO $$ 
DECLARE 
    v_patient_name VARCHAR(100);
    v_patient_id INT := 1;
    v_formatted_output VARCHAR(500);
BEGIN
    SELECT 
        CONCAT(
            UPPER(SUBSTRING(u.first_name, 1, 1)), 
            LOWER(SUBSTRING(u.first_name, 2)),
            ' ',
            UPPER(u.last_name),
            ' (ID: ',
            LPAD(p.patient_id::VARCHAR, 5, '0'),
            ')'
        )
    INTO v_patient_name
    FROM patient p
    JOIN users u ON p.users_id = u.users_id
    WHERE p.patient_id = v_patient_id;
    
    v_formatted_output := CONCAT(
        'Patient Information: ', v_patient_name,
        CHR(10), 'Record generated: ', TO_CHAR(CURRENT_DATE, 'DD-Month-YYYY')
    );
    
    RAISE NOTICE '%', v_formatted_output;
END $$;

-- Query 11: Format product codes and descriptions
-- Purpose: Standardized product display format
SELECT 
    product_id,
    UPPER(product_name) AS product_name_upper,
    INITCAP(description) AS description_formatted,
    CONCAT('$', TO_CHAR(price, '999.99')) AS price_formatted,
    LENGTH(product_name) AS name_length,
    POSITION('mg' IN dosage) AS mg_position
FROM product
WHERE dosage IS NOT NULL
LIMIT 10;

--ROUNDING/TRUNCATION 

-- Query 12: Sales analysis with rounded values
-- Purpose: Present revenue figures in simplified format
SELECT 
    pr.category,
    COUNT(DISTINCT st.transaction_id) AS transaction_count,
    ROUND(SUM(sl.quantity_sold * sl.selling_price), 0) AS revenue_rounded,
    ROUND(SUM(sl.quantity_sold * sl.selling_price), -2) AS revenue_hundreds,
    TRUNC(AVG(sl.selling_price), 1) AS avg_price_truncated,
    ROUND(AVG(sl.selling_price), 2) AS avg_price_rounded
FROM product pr
JOIN sales_line sl ON pr.product_id = sl.product_id
JOIN sale_transaction st ON sl.transaction_id = st.transaction_id
GROUP BY pr.category;

-- Query 13: Batch cost analysis with rounding
-- Purpose: Analyze inventory costs with different precision levels
SELECT 
    p.product_name,
    sb.batch_number,
    sb.unit_cost,
    ROUND(sb.unit_cost * 1.15, 2) AS retail_price_est,
    TRUNC(sb.unit_cost * 0.9, 2) AS bulk_discount_price,
    ROUND(sb.unit_cost / sb.quantity, 3) AS cost_per_unit
FROM stock_batch sb
JOIN product p ON sb.product_id = p.product_id
WHERE sb.quantity > 0
ORDER BY sb.unit_cost DESC
LIMIT 10;

-- DATE FUNCTIONS 

-- Query 14: Expiry date tracking and alerts
-- Purpose: Monitor product expiry dates and generate alerts
SELECT 
    p.product_name,
    sb.batch_number,
    sb.expiry_date,
    CURRENT_DATE AS today,
    (sb.expiry_date - CURRENT_DATE) AS days_until_expiry,
    EXTRACT(YEAR FROM sb.expiry_date) AS expiry_year,
    EXTRACT(MONTH FROM sb.expiry_date) AS expiry_month,
    TO_CHAR(sb.expiry_date, 'Day, DD Month YYYY') AS expiry_date_formatted,
    CASE 
        WHEN sb.expiry_date - CURRENT_DATE <= 30 THEN 'URGENT - EXPIRING SOON'
        WHEN sb.expiry_date - CURRENT_DATE <= 90 THEN 'Warning - Check expiry'
        ELSE 'OK'
    END AS expiry_status
FROM stock_batch sb
JOIN product p ON sb.product_id = p.product_id
ORDER BY sb.expiry_date ASC;

-- Query 15: Monthly sales trend analysis
-- Purpose: Track sales performance over time
SELECT 
    DATE_TRUNC('month', st.transaction_date) AS sales_month,
    TO_CHAR(st.transaction_date, 'Month YYYY') AS month_name,
    COUNT(DISTINCT st.transaction_id) AS num_transactions,
    SUM(st.total_amount) AS total_sales,
    ROUND(AVG(st.total_amount), 2) AS avg_transaction_value,
    EXTRACT(DOW FROM st.transaction_date) AS day_of_week
FROM sale_transaction st
WHERE st.type = 'SALE'
  AND st.transaction_date >= DATE_TRUNC('year', CURRENT_DATE)
GROUP BY DATE_TRUNC('month', st.transaction_date), 
         TO_CHAR(st.transaction_date, 'Month YYYY'),
         EXTRACT(DOW FROM st.transaction_date)
ORDER BY sales_month DESC;

-- AGGREGATE FUNCTIONS 

-- Query 16: Comprehensive pharmacy performance metrics
-- Purpose: Overall business performance dashboard
SELECT 
    'Total Sales Revenue' AS metric_name,
    SUM(total_amount)::VARCHAR AS value,
    '$' AS unit
FROM sale_transaction WHERE type = 'SALE'
UNION ALL
SELECT 
    'Total Transactions',
    COUNT(*)::VARCHAR,
    ''
FROM sale_transaction WHERE type = 'SALE'
UNION ALL
SELECT 
    'Average Transaction Value',
    ROUND(AVG(total_amount), 2)::VARCHAR,
    '$'
FROM sale_transaction WHERE type = 'SALE'
UNION ALL
SELECT 
    'Total Products in Stock',
    SUM(quantity)::VARCHAR,
    'units'
FROM stock_batch WHERE expiry_date > CURRENT_DATE
UNION ALL
SELECT 
    'Total Patients Served',
    COUNT(DISTINCT patient_id)::VARCHAR,
    ''
FROM sale_transaction WHERE patient_id IS NOT NULL
UNION ALL
SELECT 
    'Unique Products Sold',
    COUNT(DISTINCT product_id)::VARCHAR,
    ''
FROM sales_line
UNION ALL
SELECT 
    'Total Profit (Est.)',
    ROUND(SUM((sl.selling_price - sb.unit_cost) * sl.quantity_sold), 2)::VARCHAR,
    '$'
FROM sales_line sl
JOIN stock_batch sb ON sl.batch_id = sb.batch_id
JOIN sale_transaction st ON sl.transaction_id = st.transaction_id
WHERE st.type = 'SALE';

-- GROUP BY & HAVING CLAUSES 

-- Query 17: Product performance analysis with having clause
-- Purpose: Identify underperforming and overperforming products
SELECT 
    p.product_name,
    p.category,
    COUNT(DISTINCT sl.transaction_id) AS times_sold,
    SUM(sl.quantity_sold) AS total_quantity,
    AVG(sl.selling_price) AS avg_selling_price,
    SUM(sl.quantity_sold * sl.selling_price) AS total_revenue
FROM product p
JOIN sales_line sl ON p.product_id = sl.product_id
GROUP BY p.product_name, p.category
HAVING SUM(sl.quantity_sold * sl.selling_price) > 100  -- Products over $100 revenue
   AND COUNT(DISTINCT sl.transaction_id) >= 2          -- Sold at least twice
ORDER BY total_revenue DESC;

-- Query 18: Supplier performance evaluation
-- Purpose: Evaluate supplier reliability and product range
SELECT 
    sup.sname AS supplier_name,
    COUNT(DISTINCT p.product_id) AS products_supplied,
    SUM(sb.quantity) AS total_inventory,
    AVG(sb.unit_cost) AS avg_cost,
    SUM(sb.quantity * sb.unit_cost) AS inventory_value,
    MAX(p.reorder_qty) AS max_reorder_qty
FROM supplier sup
JOIN product p ON sup.supplier_id = p.supplier_id
JOIN stock_batch sb ON p.product_id = sb.product_id
GROUP BY sup.sname
HAVING COUNT(DISTINCT p.product_id) >= 2  -- Suppliers with at least 2 products
   AND SUM(sb.quantity) > 50               -- Total inventory > 50 units
ORDER BY inventory_value DESC;

-- JOINS EXECUTED CORRECTLY

-- Query 19: Complete patient journey with multiple joins (7 tables)
-- Purpose: Track patient from registration through prescriptions to sales
SELECT 
    -- Patient information
    CONCAT(u.first_name, ' ', u.last_name) AS patient_name,
    u.email,
    u.phone,
    -- Prescription information
    p.prescription_id,
    p.date_issued,
    p.doctor_name,
    -- Pharmacist information
    CONCAT(u_ph.first_name, ' ', u_ph.last_name) AS pharmacist_name,
    ph.license_number,
    -- Medication information
    pr.product_name,
    pr.dosage,
    pl.quantity AS prescribed_quantity,
    pl.dosage_description,
    -- Sales information
    st.transaction_id,
    st.transaction_date,
    sl.quantity_sold,
    sl.selling_price
FROM users u
JOIN patient pa ON u.users_id = pa.users_id
LEFT JOIN prescription p ON pa.patient_id = p.patient_id
LEFT JOIN pharmacist ph ON p.pharmacist_id = ph.pharmacist_id
LEFT JOIN users u_ph ON ph.users_id = u_ph.users_id
LEFT JOIN prescription_line pl ON p.prescription_id = pl.prescription_id
LEFT JOIN product pr ON pl.product_id = pr.product_id
LEFT JOIN sale_transaction st ON pa.patient_id = st.patient_id
LEFT JOIN sales_line sl ON st.transaction_id = sl.transaction_id AND pr.product_id = sl.product_id
WHERE u.first_name = 'John'  -- Specific patient example
ORDER BY p.date_issued DESC NULLS LAST, st.transaction_date DESC NULLS LAST;

-- Query 20: Complete supply chain analysis (6 tables)
-- Purpose: Track products from supplier through inventory to customer
SELECT 
    sup.sname AS supplier_name,
    sup.payment_term,
    p.product_name,
    p.category,
    sb.batch_number,
    sb.quantity AS stock_quantity,
    sb.expiry_date,
    sc_ctrl.first_name || ' ' || sc_ctrl.last_name AS stock_controller,
    COUNT(DISTINCT po.order_id) AS total_orders_placed,
    COUNT(DISTINCT sl.transaction_id) AS times_sold,
    SUM(sl.quantity_sold) AS total_sold
FROM supplier sup
JOIN product p ON sup.supplier_id = p.supplier_id
JOIN stock_batch sb ON p.product_id = sb.product_id
JOIN stock_controller sc ON sb.controller_id = sc.controller_id
JOIN users sc_ctrl ON sc.users_id = sc_ctrl.users_id
LEFT JOIN purchase_order_line pol ON p.product_id = pol.product_id
LEFT JOIN purchase_order po ON pol.order_id = po.order_id
LEFT JOIN sales_line sl ON p.product_id = sl.product_id AND sb.batch_id = sl.batch_id
LEFT JOIN sale_transaction st ON sl.transaction_id = st.transaction_id AND st.type = 'SALE'
GROUP BY sup.sname, sup.payment_term, p.product_name, p.category, 
         sb.batch_number, sb.quantity, sb.expiry_date, sc_ctrl.first_name, sc_ctrl.last_name
HAVING sb.quantity > 0
ORDER BY sup.sname, p.product_name;

-- SUB-QUERIES USED EFFECTIVELY 

-- Query 21: Find top-performing products using subquery
-- Purpose: Identify products that exceed average sales
SELECT 
    product_name,
    category,
    price,
    (SELECT AVG(price) FROM product) AS avg_product_price,
    price - (SELECT AVG(price) FROM product) AS price_difference,
    (SELECT COUNT(*) FROM sales_line sl2 WHERE sl2.product_id = p.product_id) AS times_sold
FROM product p
WHERE price > (SELECT AVG(price) FROM product)
  AND (SELECT SUM(quantity_sold) FROM sales_line sl3 WHERE sl3.product_id = p.product_id) > 
      (SELECT AVG(quantity_sold) FROM sales_line)
ORDER BY price DESC;

-- Query 22: Find patients with above-average spending
-- Purpose: Identify high-value customers for loyalty programs
SELECT 
    CONCAT(u.first_name, ' ', u.last_name) AS patient_name,
    u.email,
    u.phone,
    (SELECT SUM(st2.total_amount) 
     FROM sale_transaction st2 
     WHERE st2.patient_id = pa.patient_id AND st2.type = 'SALE') AS total_spent,
    (SELECT COUNT(*) 
     FROM sale_transaction st3 
     WHERE st3.patient_id = pa.patient_id AND st3.type = 'SALE') AS visit_count,
    (SELECT ROUND(AVG(total_amount), 2) 
     FROM sale_transaction st4 
     WHERE st4.type = 'SALE') AS avg_customer_spending
FROM patient pa
JOIN users u ON pa.users_id = u.users_id
WHERE (SELECT SUM(st2.total_amount) 
       FROM sale_transaction st2 
       WHERE st2.patient_id = pa.patient_id AND st2.type = 'SALE') > 
      (SELECT AVG(total_amount) 
       FROM sale_transaction 
       WHERE type = 'SALE')
ORDER BY total_spent DESC;

-- Query 23: Products with expiring batches (correlated subquery)
-- Purpose: Alert management about products with soon-to-expire batches
SELECT 
    p.product_name,
    p.category,
    (SELECT COUNT(*) 
     FROM stock_batch sb2 
     WHERE sb2.product_id = p.product_id 
       AND sb2.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days') AS batches_expiring_soon,
    (SELECT STRING_AGG(DISTINCT sb3.batch_number, ', ')
     FROM stock_batch sb3 
     WHERE sb3.product_id = p.product_id 
       AND sb3.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days') AS expiring_batches,
    (SELECT MIN(sb4.expiry_date) 
     FROM stock_batch sb4 
     WHERE sb4.product_id = p.product_id) AS earliest_expiry
FROM product p
WHERE EXISTS (
    SELECT 1 
    FROM stock_batch sb 
    WHERE sb.product_id = p.product_id 
      AND sb.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
)
ORDER BY earliest_expiry ASC;

-- Query 24: Complex subquery with multiple conditions
-- Purpose: Comprehensive business intelligence report
SELECT 
    category,
    product_count,
    avg_price,
    total_sales,
    CASE 
        WHEN total_sales > (SELECT AVG(total_sales) FROM (
            SELECT SUM(sl2.quantity_sold * sl2.selling_price) AS total_sales
            FROM product p2
            JOIN sales_line sl2 ON p2.product_id = sl2.product_id
            GROUP BY p2.category
        ) AS category_sales)
        THEN 'ABOVE AVERAGE'
        ELSE 'BELOW AVERAGE'
    END AS category_performance
FROM (
    SELECT 
        p.category,
        COUNT(DISTINCT p.product_id) AS product_count,
        ROUND(AVG(p.price), 2) AS avg_price,
        COALESCE(SUM(sl.quantity_sold * sl.selling_price), 0) AS total_sales
    FROM product p
    LEFT JOIN sales_line sl ON p.product_id = sl.product_id
    LEFT JOIN sale_transaction st ON sl.transaction_id = st.transaction_id AND st.type = 'SALE'
    GROUP BY p.category
) AS category_summary
ORDER BY total_sales DESC;

--EXTRA FUNCTIONALITY DEMONSTRATION 

-- Extra Query 1: Stored Procedure for automatic reorder generation
CREATE OR REPLACE FUNCTION generate_reorder_report()
RETURNS TABLE (
    product_id INT,
    product_name VARCHAR,
    current_stock BIGINT,
    reorder_qty INT,
    suggested_order_qty BIGINT,
    supplier_name VARCHAR,
    urgency_level VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.product_id,
        p.product_name,
        COALESCE(SUM(sb.quantity), 0) AS current_stock,
        p.reorder_qty,
        GREATEST(p.reorder_qty - COALESCE(SUM(sb.quantity), 0), 0) AS suggested_order_qty,
        s.sname AS supplier_name,
        CASE 
            WHEN COALESCE(SUM(sb.quantity), 0) <= p.reorder_qty * 0.5 THEN 'URGENT'
            WHEN COALESCE(SUM(sb.quantity), 0) <= p.reorder_qty THEN 'REORDER NEEDED'
            ELSE 'OK'
        END AS urgency_level
    FROM product p
    LEFT JOIN stock_batch sb ON p.product_id = sb.product_id AND sb.expiry_date > CURRENT_DATE
    JOIN supplier s ON p.supplier_id = s.supplier_id
    GROUP BY p.product_id, p.product_name, p.reorder_qty, s.sname
    HAVING COALESCE(SUM(sb.quantity), 0) <= p.reorder_qty * 1.2
    ORDER BY urgency_level DESC, suggested_order_qty DESC;
END;
$$ LANGUAGE plpgsql;

-- Execute the function
SELECT * FROM generate_reorder_report();

-- Extra Query 2: Trigger to automatically update transaction total
CREATE OR REPLACE FUNCTION update_transaction_total()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sale_transaction
    SET total_amount = (
        SELECT COALESCE(SUM(quantity_sold * selling_price), 0)
        FROM sales_line
        WHERE transaction_id = NEW.transaction_id
    )
    WHERE transaction_id = NEW.transaction_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS trg_update_transaction_total ON sales_line;
CREATE TRIGGER trg_update_transaction_total
AFTER INSERT OR UPDATE OR DELETE ON sales_line
FOR EACH ROW
EXECUTE FUNCTION update_transaction_total();

-- Extra Query 3: Window functions for ranking and analytics
SELECT 
    p.product_name,
    p.category,
    EXTRACT(MONTH FROM st.transaction_date) AS month,
    SUM(sl.quantity_sold) AS monthly_sales,
    RANK() OVER (PARTITION BY p.category ORDER BY SUM(sl.quantity_sold) DESC) AS rank_in_category,
    SUM(SUM(sl.quantity_sold)) OVER (PARTITION BY p.category ORDER BY EXTRACT(MONTH FROM st.transaction_date)) AS cumulative_sales,
    LAG(SUM(sl.quantity_sold)) OVER (PARTITION BY p.product_id ORDER BY EXTRACT(MONTH FROM st.transaction_date)) AS previous_month_sales,
    CASE 
        WHEN LAG(SUM(sl.quantity_sold)) OVER (PARTITION BY p.product_id ORDER BY EXTRACT(MONTH FROM st.transaction_date)) IS NOT NULL
        THEN ROUND(((SUM(sl.quantity_sold) - LAG(SUM(sl.quantity_sold)) OVER (PARTITION BY p.product_id ORDER BY EXTRACT(MONTH FROM st.transaction_date))) * 100.0 / 
                    LAG(SUM(sl.quantity_sold)) OVER (PARTITION BY p.product_id ORDER BY EXTRACT(MONTH FROM st.transaction_date))), 2)
        ELSE NULL
    END AS growth_percentage
FROM product p
JOIN sales_line sl ON p.product_id = sl.product_id
JOIN sale_transaction st ON sl.transaction_id = st.transaction_id
WHERE st.type = 'SALE'
  AND st.transaction_date >= DATE_TRUNC('year', CURRENT_DATE)
GROUP BY p.product_name, p.category, EXTRACT(MONTH FROM st.transaction_date)
ORDER BY p.category, month;

-- Extra Query 4: Recursive query for organizational hierarchy
WITH RECURSIVE user_hierarchy AS (
    -- Base case: stock controllers (top level)
    SELECT 
        u.users_id,
        u.first_name,
        u.last_name,
        u.roles,
        1 AS level,
        u.first_name || ' ' || u.last_name AS hierarchy_path
    FROM users u
    WHERE u.roles = 'STOCK_CONTROLLER'
    
    UNION ALL
    
    -- Recursive case: find related users (example - patients linked to pharmacists)
    SELECT 
        u.users_id,
        u.first_name,
        u.last_name,
        u.roles,
        uh.level + 1,
        uh.hierarchy_path || ' -> ' || u.first_name || ' ' || u.last_name
    FROM users u
    CROSS JOIN user_hierarchy uh
    WHERE u.roles IN ('PATIENT', 'PHARMACIST')
      AND u.users_id NOT IN (SELECT users_id FROM user_hierarchy)
    LIMIT 10
)
SELECT * FROM user_hierarchy ORDER BY level, hierarchy_path;




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




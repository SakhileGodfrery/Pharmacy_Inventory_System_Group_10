SELECT 
    sb.BATCH_ID,
    sb.batch_number,
    p.product_name,
    sb.quantity,
    sb.expiry_date
FROM "STOCK BATCH" sb
INNER JOIN PRODUCT p ON sb.PRODUCT_ID = p.PRODUCT_ID;

SELECT 
    pr.PRESCRIPTION_ID,
    pr.date_issued,
    pr.doctor_name,
    u.first_name AS patient_first_name,
    u.last_name AS patient_last_name,
    ph.license_number,
    phu.first_name AS pharmacist_first_name,
    phu.last_name AS pharmacist_last_name
FROM PRESCRIPTION pr
INNER JOIN PATIENT pa ON pr.PATIENT_ID = pa.PATIENT_ID
INNER JOIN USER u ON pa.USER_ID = u.USER_ID
INNER JOIN PHARMACIST ph ON pr.PHARMACIST_ID = ph.PHARMACIST_ID
INNER JOIN USER phu ON ph.USER_ID = phu.USER_ID;

SELECT 
    p.PRODUCT_ID,
    p.product_name,
    sb.BATCH_ID,
    sb.batch_number,
    sb.quantity,
    sb.expiry_date
FROM PRODUCT p
LEFT JOIN "STOCK BATCH" sb ON p.PRODUCT_ID = sb.PRODUCT_ID;

SELECT 
    p.PRODUCT_ID,
    p.product_name,
    SUM(sl.quantity_sold) AS total_quantity_sold,
    SUM(sl.quantity_sold * sl.selling_price) AS total_revenue
FROM PRODUCT p
INNER JOIN "SALES LINE" sl ON p.PRODUCT_ID = sl.PRODUCT_ID
INNER JOIN TRANSACTION t ON sl.TRANSACTION_ID = t.TRANSACTION_ID
GROUP BY p.PRODUCT_ID, p.product_name
ORDER BY total_revenue DESC;

SELECT 
    s.supplier_name,
    po.ORDER_ID,
    po.order_date,
    po.status,
    p.product_name,
    pol.quantity_ordered,
    po.unit_cost
FROM SUPPLIER s
INNER JOIN "PURCHASE ORDER" po ON s.SUPPLIER_ID = po.SUPPLIER_ID
INNER JOIN "PURCHASE ORDER LINE" pol ON po.ORDER_ID = pol.ORDER_ID
INNER JOIN PRODUCT p ON pol.PRODUCT_ID = p.PRODUCT_ID;

SELECT 
    cl.LOG_ID,
    cl.log_date,
    p.product_name,
    u.first_name AS pharmacist_name,
    pa_u.first_name AS patient_name,
    cl.quantity,
    cl.action_type,
    cl.status
FROM "CONTROLLED LOG" cl
INNER JOIN PRODUCT p ON cl.PRODUCT_ID = p.PRODUCT_ID
INNER JOIN PHARMACIST ph ON cl.PHARMACIST_ID = ph.PHARMACIST_ID
INNER JOIN USER u ON ph.USER_ID = u.USER_ID
INNER JOIN PATIENT pa ON cl.PATIENT_ID = pa.PATIENT_ID
INNER JOIN USER pa_u ON pa.USER_ID = pa_u.USER_ID;

SELECT 
    t.TRANSACTION_ID,
    t.transaction_date,
    t.type,
    pu.first_name AS patient_name,
    phu.first_name AS pharmacist_name,
    p.product_name,
    sl.quantity_sold,
    sl.selling_price
FROM TRANSACTION t
INNER JOIN PATIENT pa ON t.PATIENT_ID = pa.PATIENT_ID
INNER JOIN USER pu ON pa.USER_ID = pu.USER_ID
INNER JOIN PHARMACIST ph ON t.PHARMACIST_ID = ph.PHARMACIST_ID
INNER JOIN USER phu ON ph.USER_ID = phu.USER_ID
INNER JOIN "SALES LINE" sl ON t.TRANSACTION_ID = sl.TRANSACTION_ID
INNER JOIN PRODUCT p ON sl.PRODUCT_ID = p.PRODUCT_ID;

SELECT 
    p.PRODUCT_ID,
    p.product_name,
    p.reorder_quantity AS reorder_level,
    COALESCE(SUM(sb.quantity), 0) AS total_stock_on_hand,
    CASE 
        WHEN COALESCE(SUM(sb.quantity), 0) <= p.reorder_quantity THEN 'ORDER NOW'
        WHEN COALESCE(SUM(sb.quantity), 0) <= p.reorder_quantity * 1.5 THEN 'ORDER SOON'
        WHEN COALESCE(SUM(sb.quantity), 0) = 0 THEN 'OUT OF STOCK'
        ELSE 'OK'
    END AS stock_status
FROM PRODUCT p
LEFT JOIN "STOCK BATCH" sb ON p.PRODUCT_ID = sb.PRODUCT_ID
GROUP BY p.PRODUCT_ID, p.product_name, p.reorder_quantity
HAVING COALESCE(SUM(sb.quantity), 0) <= p.reorder_quantity * 1.5
ORDER BY total_stock_on_hand ASC;


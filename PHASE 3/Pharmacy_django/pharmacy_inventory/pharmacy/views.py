from django.db import connection
from django.shortcuts import render

# ---------- Helper to convert cursor results to list of dicts ----------
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# ---------- Main Pages ----------
def dashboard(request):
    with connection.cursor() as cursor:
        # Low stock view
        cursor.execute("SELECT * FROM low_stock_view;")
        low_stock = dictfetchall(cursor)
        low_stock_count = len(low_stock)

        # Expiring products view
        cursor.execute("SELECT * FROM expiring_products_view;")
        expiring = dictfetchall(cursor)

        # Total products count (for KPI card)
        cursor.execute("SELECT COUNT(*) FROM product;")
        total_products = cursor.fetchone()[0]

        # Order status counts from purchase_order table
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'DELIVERED' THEN 1 END) as delivered,
                COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) as cancelled,
                COUNT(CASE WHEN status = 'SHIPPED' THEN 1 END) as shipped
            FROM purchase_order;
        """)
        row = cursor.fetchone()
        pending_orders = row[0] if row else 0
        delivered_orders = row[1] if row else 0
        cancelled_orders = row[2] if row else 0
        in_courier = row[3] if row else 0
        complete_orders = delivered_orders   # as per design
        returned_orders = 0                  # optional, if you have a 'RETURNED' status

        # Recent orders (using sale_transaction as customer orders)
        cursor.execute("""
            SELECT 
                st.transaction_id as order_id,
                COALESCE(CONCAT(u.first_name, ' ', u.last_name), 'Walk-in') as customer,
                st.transaction_date as order_date,
                CASE 
                    WHEN st.type = 'SALE' THEN 'Delivered'
                    ELSE 'Pending'
                END as status,
                st.total_amount as total
            FROM sale_transaction st
            LEFT JOIN patient p ON st.patient_id = p.patient_id
            LEFT JOIN users u ON p.users_id = u.users_id
            ORDER BY st.transaction_date DESC
            LIMIT 5
        """)
        recent_orders = dictfetchall(cursor)

        # Optional: Real data for order trend chart (last 30 days)
        cursor.execute("""
            SELECT DATE(transaction_date) as day, COUNT(*) as orders
            FROM sale_transaction
            WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY day
            ORDER BY day;
        """)
        trend_data = dictfetchall(cursor)
        # Prepare labels and values for chart
        trend_labels = [item['day'].strftime('%Y-%m-%d') for item in trend_data] if trend_data else []
        trend_counts = [item['orders'] for item in trend_data] if trend_data else []

    context = {
        'low_stock': low_stock,
        'expiring': expiring,
        'low_stock_count': low_stock_count,
        'total_products': total_products,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'in_courier': in_courier,
        'complete_orders': complete_orders,
        'returned_orders': returned_orders,
        'recent_orders': recent_orders,
        'trend_labels': trend_labels,
        'trend_counts': trend_counts,
    }
    return render(request, 'inventory/dashboard.html', context)


def product_list(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.category, p.price,
                   s.supplier_name
            FROM product p
            JOIN supplier s ON p.supplier_id = s.supplier_id
            ORDER BY p.product_name
        """)
        products = dictfetchall(cursor)
    return render(request, 'inventory/product_list.html', {'products': products})


def batch_list(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT sb.batch_id, sb.batch_number, p.product_name,
                   sb.quantity, sb.expiry_date,
                   CONCAT(u.first_name, ' ', u.last_name) AS controller_name
            FROM stock_batch sb
            JOIN product p ON sb.product_id = p.product_id
            JOIN stock_controller sc ON sb.controller_id = sc.controller_id
            JOIN users u ON sc.users_id = u.users_id
            ORDER BY sb.expiry_date
        """)
        batches = dictfetchall(cursor)
    return render(request, 'inventory/batch_list.html', {'batches': batches})


# ---------- Query 1: Patient prescription history ----------
def query_patient_prescription_history(request):
    with connection.cursor() as cursor:
        cursor.execute("""
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
            ORDER BY p.date_issued DESC
        """)
        results = dictfetchall(cursor)
    return render(request, 'inventory/query1.html', {'results': results})


# ---------- Query 2: Sales by category ----------
def query_sales_by_category(request):
    with connection.cursor() as cursor:
        cursor.execute("""
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
            ORDER BY total_revenue DESC
        """)
        results = dictfetchall(cursor)
    return render(request, 'inventory/query2.html', {'results': results})


# ---------- Query 3: Low stock products needing reorder ----------
def query_low_stock_products(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                pr.product_id,
                pr.product_name,
                COALESCE(SUM(sb.quantity), 0) AS current_stock,
                pr.reorder_qty AS reorder_level,
                sup.supplier_name,
                sup.phone AS supplier_phone,
                (pr.reorder_qty - COALESCE(SUM(sb.quantity), 0)) AS quantity_to_order
            FROM product pr
            LEFT JOIN stock_batch sb ON pr.product_id = sb.product_id
            JOIN supplier sup ON pr.supplier_id = sup.supplier_id
            GROUP BY pr.product_id, pr.product_name, pr.reorder_qty, sup.supplier_name, sup.phone
            HAVING COALESCE(SUM(sb.quantity), 0) <= pr.reorder_qty
            ORDER BY current_stock ASC
        """)
        results = dictfetchall(cursor)
    return render(request, 'inventory/query3.html', {'results': results})


# ---------- Query 4: Top 5 best-selling products ----------
def query_top5_products(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                pr.product_name,
                SUM(sl.quantity_sold) AS total_sold,
                SUM(sl.quantity_sold * sl.selling_price) AS revenue
            FROM product pr
            JOIN sales_line sl ON pr.product_id = sl.product_id
            GROUP BY pr.product_name
            ORDER BY revenue DESC
            FETCH FIRST 5 ROWS ONLY
        """)
        results = dictfetchall(cursor)
    return render(request, 'inventory/query4.html', {'results': results})


# ---------- Query 12: Rounding/truncation report ----------
def query_rounding_report(request):
    with connection.cursor() as cursor:
        cursor.execute("""
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
            GROUP BY pr.category
        """)
        results = dictfetchall(cursor)
    return render(request, 'inventory/query12.html', {'results': results})


# ---------- Query 14: Expiry date alerts ----------
def query_expiry_alerts(request):
    with connection.cursor() as cursor:
        cursor.execute("""
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
            ORDER BY sb.expiry_date ASC
        """)
        results = dictfetchall(cursor)
    return render(request, 'inventory/query14.html', {'results': results})


# ---------- Query 19: Patient journey (7-table join) ----------
def query_patient_journey(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                CONCAT(u.first_name, ' ', u.last_name) AS patient_name,
                u.email,
                u.phone,
                p.prescription_id,
                p.date_issued,
                p.doctor_name,
                CONCAT(u_ph.first_name, ' ', u_ph.last_name) AS pharmacist_name,
                ph.license_number,
                pr.product_name,
                pr.dosage,
                pl.quantity AS prescribed_quantity,
                pl.dosage_description,
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
            WHERE u.first_name = 'John'
            ORDER BY p.date_issued DESC NULLS LAST, st.transaction_date DESC NULLS LAST
        """)
        results = dictfetchall(cursor)
    return render(request, 'inventory/query19.html', {'results': results})


# ---------- Query 21: Top products using subquery ----------
def query_top_products_subquery(request):
    with connection.cursor() as cursor:
        cursor.execute("""
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
            ORDER BY price DESC
        """)
        results = dictfetchall(cursor)
    return render(request, 'inventory/query21.html', {'results': results})


# ---------- Extra: Stored procedure reorder report ----------
def reorder_report(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM generate_reorder_report();")
        report = dictfetchall(cursor)
    return render(request, 'inventory/reorder_report.html', {'report': report})
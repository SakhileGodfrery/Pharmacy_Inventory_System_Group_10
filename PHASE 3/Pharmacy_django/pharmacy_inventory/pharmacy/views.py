from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .forms import RegistrationForm, AddRecordForm, QueryForm, UpdateRecordForm
from .db import (execute_query, get_table_names, get_table_data, 
                 get_table_columns, get_primary_key, get_foreign_keys,
                 validate_table_name, get_db_connection)
from django.db import connection
import json
import logging
import re

logger = logging.getLogger(__name__)

# ==================== Custom authentication (raw SQL) ====================
def login_view(request):
    if request.session.get('user_id'):
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT users_id, first_name, last_name, roles, email
                FROM users
                WHERE email = %s AND password_hash = %s
            """, [email, password])
            user = cursor.fetchone()
        if user:
            request.session['user_id'] = user[0]
            request.session['user_name'] = f"{user[1]} {user[2]}"
            request.session['user_role'] = user[3]
            request.session['user_email'] = user[4]
            messages.success(request, f'Welcome back, {user[1]}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'login.html')

def register_view(request):
    if request.session.get('user_id'):
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            date_of_birth = form.cleaned_data['date_of_birth']
            phone = form.cleaned_data.get('phone', '')
            address = form.cleaned_data.get('address', '')
            gender = form.cleaned_data.get('gender', '')
            country = form.cleaned_data.get('country', '')
            password = form.cleaned_data['password1']
            
            if not date_of_birth:
                messages.error(request, 'Date of birth is required.')
                return render(request, 'register.html', {'form': form})
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO users 
                        (first_name, last_name, email, date_of_birth, phone, home_address, 
                         gender, country, password_hash, roles, reg_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'PATIENT', NOW())
                    """, [first_name, last_name, email, date_of_birth, phone, address,
                          gender, country, password])
                messages.success(request, 'Registration successful. Please log in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Registration error: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    request.session.flush()
    messages.info(request, 'You have been logged out.')
    return redirect('login')

def dashboard(request):
    if not request.session.get('user_id'):
        return redirect('login')
    context = {
        'user_name': request.session.get('user_name'),
        'user_role': request.session.get('user_role'),
    }
    return render(request, 'dashboard.html', context)

# ==================== Pre‑defined SQL Queries ====================
PREDEFINED_QUERIES = {
    '1': """
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
        LIMIT 50
    """,
    '2': """
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
    """,
    '3': """
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
    """,
    '4': """
        SELECT 
            pr.product_name,
            SUM(sl.quantity_sold) AS total_sold,
            SUM(sl.quantity_sold * sl.selling_price) AS revenue
        FROM product pr
        JOIN sales_line sl ON pr.product_id = sl.product_id
        GROUP BY pr.product_name
        ORDER BY revenue DESC
        FETCH FIRST 5 ROWS ONLY
    """,
    '5': """
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
        LIMIT 10
    """,
    '6': """
        SELECT 
            product_name,
            category,
            price,
            dosage
        FROM product
        ORDER BY price DESC, product_name ASC
        LIMIT 50
    """,
    '7': """
        SELECT 
            supplier_name,
            status,
            payment_term,
            phone,
            email
        FROM supplier
        ORDER BY status DESC, supplier_name ASC
    """,
    '8': """
        SELECT 
            CONCAT(u.first_name, ' ', u.last_name) AS patient_name,
            a.allergy_name,
            u.phone,
            u.email
        FROM allergy a
        JOIN patient p ON a.patient_id = p.patient_id
        JOIN users u ON p.users_id = u.users_id
        WHERE a.allergy_name LIKE '%%cillin%%' 
           OR a.allergy_name = 'Aspirin'
        LIMIT 30
    """,
    '9': """
        SELECT 
            product_name,
            price,
            category,
            dosage
        FROM product
        WHERE price BETWEEN 20.00 AND 50.00
          AND (product_name LIKE '%%mycin%%' OR product_name LIKE '%%pril%%')
        ORDER BY price
        LIMIT 30
    """,
    '10': """
        SELECT 
            p.product_name,
            sb.batch_number,
            sb.expiry_date,
            CURRENT_DATE AS today,
            (sb.expiry_date - CURRENT_DATE) AS days_until_expiry,
            CASE 
                WHEN sb.expiry_date - CURRENT_DATE <= 30 THEN 'URGENT - EXPIRING SOON'
                WHEN sb.expiry_date - CURRENT_DATE <= 90 THEN 'Warning - Check expiry'
                ELSE 'OK'
            END AS expiry_status
        FROM stock_batch sb
        JOIN product p ON sb.product_id = p.product_id
        WHERE sb.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
        ORDER BY sb.expiry_date ASC
        LIMIT 50
    """,
    '11': """
        SELECT 
            DATE_TRUNC('month', st.transaction_date) AS sales_month,
            TO_CHAR(st.transaction_date, 'Month YYYY') AS month_name,
            COUNT(DISTINCT st.transaction_id) AS num_transactions,
            SUM(st.total_amount) AS total_sales,
            ROUND(AVG(st.total_amount), 2) AS avg_transaction_value
        FROM sale_transaction st
        WHERE st.type = 'SALE'
          AND st.transaction_date >= DATE_TRUNC('year', CURRENT_DATE)
        GROUP BY DATE_TRUNC('month', st.transaction_date), 
                 TO_CHAR(st.transaction_date, 'Month YYYY')
        ORDER BY sales_month DESC
    """,
    '12': """
        SELECT 'Total Sales Revenue' AS metric_name, SUM(total_amount)::VARCHAR AS value, 'USD' AS unit
        FROM sale_transaction WHERE type = 'SALE'
        UNION ALL
        SELECT 'Total Transactions', COUNT(*)::VARCHAR, ''
        FROM sale_transaction WHERE type = 'SALE'
        UNION ALL
        SELECT 'Average Transaction Value', ROUND(AVG(total_amount), 2)::VARCHAR, 'USD'
        FROM sale_transaction WHERE type = 'SALE'
        UNION ALL
        SELECT 'Total Products in Stock', SUM(quantity)::VARCHAR, 'units'
        FROM stock_batch WHERE expiry_date > CURRENT_DATE
        UNION ALL
        SELECT 'Total Patients Served', COUNT(DISTINCT patient_id)::VARCHAR, ''
        FROM sale_transaction WHERE patient_id IS NOT NULL
        UNION ALL
        SELECT 'Unique Products Sold', COUNT(DISTINCT product_id)::VARCHAR, ''
        FROM sales_line
    """,
    '13': """
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
        HAVING SUM(sl.quantity_sold * sl.selling_price) > 100
           AND COUNT(DISTINCT sl.transaction_id) >= 2
        ORDER BY total_revenue DESC
        LIMIT 30
    """,
    '14': """
        SELECT 
            sup.supplier_name,
            COUNT(DISTINCT p.product_id) AS products_supplied,
            SUM(sb.quantity) AS total_inventory,
            AVG(sb.unit_cost) AS avg_cost,
            SUM(sb.quantity * sb.unit_cost) AS inventory_value
        FROM supplier sup
        JOIN product p ON sup.supplier_id = p.supplier_id
        JOIN stock_batch sb ON p.product_id = sb.product_id
        GROUP BY sup.supplier_name
        HAVING COUNT(DISTINCT p.product_id) >= 2
           AND SUM(sb.quantity) > 50
        ORDER BY inventory_value DESC
    """,
    '15': """
        SELECT 
            CONCAT(u.first_name, ' ', u.last_name) AS patient_name,
            u.email,
            u.phone,
            p.prescription_id,
            p.date_issued,
            p.doctor_name,
            pr.product_name,
            pl.quantity AS prescribed_quantity
        FROM users u
        JOIN patient pa ON u.users_id = pa.users_id
        LEFT JOIN prescription p ON pa.patient_id = p.patient_id
        LEFT JOIN prescription_line pl ON p.prescription_id = pl.prescription_id
        LEFT JOIN product pr ON pl.product_id = pr.product_id
        WHERE u.first_name = 'John'
        ORDER BY p.date_issued DESC NULLS LAST
        LIMIT 30
    """,
    '16': """
        SELECT 
            sup.supplier_name,
            p.product_name,
            sb.batch_number,
            sb.quantity AS stock_quantity,
            sb.expiry_date,
            SUM(sl.quantity_sold) AS total_sold
        FROM supplier sup
        JOIN product p ON sup.supplier_id = p.supplier_id
        JOIN stock_batch sb ON p.product_id = sb.product_id
        LEFT JOIN sales_line sl ON p.product_id = sl.product_id AND sb.batch_id = sl.batch_id
        GROUP BY sup.supplier_name, p.product_name, sb.batch_number, sb.quantity, sb.expiry_date
        HAVING sb.quantity > 0
        ORDER BY sup.supplier_name, p.product_name
        LIMIT 50
    """,
    '17': """
        SELECT 
            product_name,
            category,
            price,
            (SELECT AVG(price) FROM product) AS avg_product_price,
            (SELECT COUNT(*) FROM sales_line sl2 WHERE sl2.product_id = p.product_id) AS times_sold
        FROM product p
        WHERE price > (SELECT AVG(price) FROM product)
        ORDER BY price DESC
        LIMIT 30
    """,
    '18': """
        SELECT 
            CONCAT(u.first_name, ' ', u.last_name) AS patient_name,
            u.email,
            u.phone,
            COALESCE(SUM(st.total_amount), 0) AS total_spent,
            COUNT(st.transaction_id) AS visit_count
        FROM patient pa
        JOIN users u ON pa.users_id = u.users_id
        LEFT JOIN sale_transaction st ON pa.patient_id = st.patient_id AND st.type = 'SALE'
        GROUP BY u.first_name, u.last_name, u.email, u.phone
        HAVING COALESCE(SUM(st.total_amount), 0) > (SELECT AVG(total_amount) FROM sale_transaction WHERE type = 'SALE')
        ORDER BY total_spent DESC
        LIMIT 30
    """,
    '19': """
        SELECT 
            p.product_name,
            p.category,
            STRING_AGG(DISTINCT sb.batch_number, ', ') AS expiring_batches,
            MIN(sb.expiry_date) AS earliest_expiry
        FROM product p
        JOIN stock_batch sb ON p.product_id = sb.product_id
        WHERE sb.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
        GROUP BY p.product_name, p.category
        ORDER BY earliest_expiry ASC
        LIMIT 30
    """
}

# ==================== Helper functions ====================
def is_safe_query(sql):
    """Check if SQL query is safe (only SELECT statements)"""
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith('SELECT'):
        return False, "Only SELECT queries are allowed"
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
                         'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False, f"Dangerous keyword '{keyword}' not allowed"
    return True, "OK"

# ==================== Views (data, queries, CRUD, API) ====================
def view_data(request):
    if not request.session.get('user_id'):
        return redirect('login')
    tables = get_table_names()
    selected_table = request.GET.get('table', '')
    page = request.GET.get('page', 1)
    table_data = []
    columns = []
    total_count = 0
    
    if selected_table and tables:
        try:
            validate_table_name(selected_table)
            count_sql = f'SELECT COUNT(*) FROM "{selected_table}"'
            total_count_result = execute_query(count_sql, fetch_one=True)
            total_count = total_count_result[0] if total_count_result else 0
            per_page = 50
            offset = (int(page) - 1) * per_page
            table_data = get_table_data(selected_table, limit=per_page, offset=offset)
            columns_info = get_table_columns(selected_table)
            columns = [col[0] for col in columns_info]
            paginator = Paginator(range(total_count), per_page)
            page_obj = paginator.get_page(page)
        except Exception as e:
            messages.error(request, f'Error loading table: {e}')
            page_obj = None
    else:
        page_obj = None
    
    context = {
        'tables': tables,
        'selected_table': selected_table,
        'table_data': table_data,
        'columns': columns,
        'table_name': selected_table,
        'page_obj': page_obj,
        'total_count': total_count,
    }
    return render(request, 'view_data.html', context)

def run_queries(request):
    if not request.session.get('user_id'):
        return redirect('login')
    results = None
    columns = None
    error = None
    executed_query = None
    
    if request.method == 'POST':
        selected_query = request.POST.get('selected_query')
        custom_sql = request.POST.get('custom_sql', '')
        if selected_query == '20' and custom_sql:
            is_safe, message = is_safe_query(custom_sql)
            if not is_safe:
                error = message
            else:
                sql = custom_sql
                executed_query = sql
        elif selected_query and selected_query in PREDEFINED_QUERIES:
            sql = PREDEFINED_QUERIES[selected_query]
            executed_query = sql
        else:
            error = "Invalid query selection"
        
        if not error and executed_query:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(executed_query)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()
                    messages.success(request, f'Query executed successfully. {len(results)} rows returned.')
                else:
                    messages.info(request, 'Query executed successfully but returned no results.')
                cursor.close()
                conn.close()
            except Exception as e:
                error = str(e)
                messages.error(request, f'Query error: {e}')
    
    context = {
        'predefined_queries': PREDEFINED_QUERIES,
        'results': results,
        'columns': columns,
        'error': error,
        'executed_query': executed_query,
    }
    return render(request, 'run_queries.html', context)

def add_record(request):
    if not request.session.get('user_id'):
        return redirect('login')
    tables = get_table_names()
    if request.method == 'POST':
        table_name = request.POST.get('table_name')
        try:
            validate_table_name(table_name)
            record_data = {}
            for key, value in request.POST.items():
                if key not in ['csrfmiddlewaretoken', 'table_name'] and value.strip():
                    if value.isdigit():
                        record_data[key] = int(value)
                    else:
                        try:
                            record_data[key] = float(value)
                        except ValueError:
                            record_data[key] = value
            if not record_data:
                messages.error(request, 'Please provide at least one field value')
                return redirect(f'{request.path}?table={table_name}')
            columns = list(record_data.keys())
            placeholders = ['%s'] * len(columns)
            values = [record_data[col] for col in columns]
            sql = f'INSERT INTO "{table_name}" ({", ".join(columns)}) VALUES ({", ".join(placeholders)})'
            rows_affected = execute_query(sql, values)
            if rows_affected > 0:
                messages.success(request, f'Record added successfully to {table_name}!')
            else:
                messages.error(request, 'Failed to insert record')
        except Exception as e:
            messages.error(request, f'Error adding record: {e}')
        return redirect(f'{request.path}?table={table_name}')
    
    selected_table = request.GET.get('table', '')
    columns_info = []
    fk_relations = []
    pk_column = None
    fk_options = {}
    
    if selected_table:
        try:
            validate_table_name(selected_table)
            columns_info = get_table_columns(selected_table)
            fk_relations = get_foreign_keys(selected_table)
            pk_column = get_primary_key(selected_table)
            
            # For each foreign key, fetch options from the referenced table
            for fk in fk_relations:
                fk_column = fk[0]
                ref_table = fk[1]
                ref_pk = get_primary_key(ref_table)
                # Find a suitable display column
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{ref_table}' 
                        AND (column_name LIKE '%name' OR column_name = 'first_name' OR column_name = 'supplier_name' OR column_name = 'product_name')
                        LIMIT 1
                    """)
                    display_col = cursor.fetchone()
                    if display_col:
                        display_col = display_col[0]
                    else:
                        # fallback to first column
                        cursor.execute(f"""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = '{ref_table}' 
                            ORDER BY ordinal_position LIMIT 1
                        """)
                        display_col = cursor.fetchone()[0]
                # Fetch options
                options_sql = f'SELECT "{ref_pk}", "{display_col}" FROM "{ref_table}" ORDER BY "{display_col}"'
                options = execute_query(options_sql, fetch_all=True)
                fk_options[fk_column] = options
        except Exception as e:
            messages.error(request, f'Error loading columns: {e}')
    
    context = {
        'tables': tables,
        'selected_table': selected_table,
        'columns_info': columns_info,
        'fk_relations': fk_relations,
        'pk_column': pk_column,
        'fk_options': fk_options,
    }
    return render(request, 'add_record.html', context)

def update_record(request):
    if not request.session.get('user_id'):
        return redirect('login')
    tables = get_table_names()
    result = None
    error = None
    
    if request.method == 'POST':
        table_name = request.POST.get('table_name')
        record_id = request.POST.get('record_id')
        try:
            validate_table_name(table_name)
            pk_column = get_primary_key(table_name)
            if not pk_column:
                raise ValueError(f"No primary key found for table {table_name}")
            update_data = {}
            for key, value in request.POST.items():
                if key not in ['csrfmiddlewaretoken', 'table_name', 'record_id'] and value.strip():
                    if value.isdigit():
                        update_data[key] = int(value)
                    else:
                        try:
                            update_data[key] = float(value)
                        except ValueError:
                            update_data[key] = value
            if not update_data:
                raise ValueError("Please provide at least one field to update")
            set_clauses = [f'"{col}" = %s' for col in update_data.keys()]
            values = list(update_data.values())
            values.append(record_id)
            sql = f'UPDATE "{table_name}" SET {", ".join(set_clauses)} WHERE "{pk_column}" = %s'
            rows_affected = execute_query(sql, values)
            if rows_affected > 0:
                result = f'Successfully updated {rows_affected} record(s) in {table_name}'
                messages.success(request, result)
            else:
                error = f'No record found with {pk_column} = {record_id}'
        except Exception as e:
            error = str(e)
            messages.error(request, f'Error updating record: {e}')
    
    record_data = None
    selected_table = request.GET.get('table', '')
    record_id = request.GET.get('id', '')
    if selected_table and record_id:
        try:
            validate_table_name(selected_table)
            pk_column = get_primary_key(selected_table)
            if pk_column:
                sql = f'SELECT * FROM "{selected_table}" WHERE "{pk_column}" = %s'
                record_data_raw = execute_query(sql, [record_id], fetch_one=True)
                if record_data_raw:
                    columns_info = get_table_columns(selected_table)
                    record_data = {}
                    for i, col in enumerate(columns_info):
                        record_data[col[0]] = record_data_raw[i] if i < len(record_data_raw) else None
        except Exception as e:
            messages.error(request, f'Error loading record: {e}')
    
    context = {
        'tables': tables,
        'selected_table': selected_table,
        'record_id': record_id,
        'record_data': record_data,
        'result': result,
        'error': error,
    }
    return render(request, 'update_record.html', context)

@csrf_exempt
def api_get_table_schema(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    if request.method == 'GET':
        table_name = request.GET.get('table', '')
        if table_name:
            try:
                columns = get_table_columns(table_name)
                schema = []
                for col in columns:
                    col_name = col[0]
                    data_type = col[1]
                    is_nullable = col[2]
                    if col_name.endswith('_id') and 'serial' in data_type.lower():
                        continue
                    schema.append({
                        'name': col_name,
                        'type': data_type,
                        'required': is_nullable == 'NO'
                    })
                return JsonResponse({'success': True, 'schema': schema})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def api_get_record(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    if request.method == 'GET':
        table_name = request.GET.get('table', '')
        record_id = request.GET.get('id', '')
        if table_name and record_id:
            try:
                # Try to infer primary key column
                pk_column = get_primary_key(table_name)
                if not pk_column:
                    # fallback
                    pk_column = f"{table_name[:-1]}_id" if table_name.endswith('s') else 'id'
                sql = f'SELECT * FROM "{table_name}" WHERE "{pk_column}" = %s'
                result = execute_query(sql, [record_id], fetch_one=True)
                if result:
                    columns = get_table_columns(table_name)
                    record_dict = {}
                    for i, col in enumerate(columns):
                        record_dict[col[0]] = result[i] if i < len(result) else None
                    return JsonResponse({'success': True, 'record': record_dict})
                else:
                    return JsonResponse({'success': False, 'error': 'Record not found'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def api_update_record(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_name = data.get('table_name')
            record_id = data.get('record_id')
            update_data = data.get('update_data', {})
            if not table_name or not record_id or not update_data:
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            pk_column = get_primary_key(table_name)
            if not pk_column:
                raise ValueError(f"No primary key found for {table_name}")
            set_clauses = [f'"{col}" = %s' for col in update_data.keys()]
            values = list(update_data.values())
            values.append(record_id)
            sql = f'UPDATE "{table_name}" SET {", ".join(set_clauses)} WHERE "{pk_column}" = %s'
            rows_affected = execute_query(sql, values)
            if rows_affected > 0:
                return JsonResponse({'success': True, 'message': f'Updated {rows_affected} record(s)'})
            else:
                return JsonResponse({'success': False, 'error': 'No record found or no changes made'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
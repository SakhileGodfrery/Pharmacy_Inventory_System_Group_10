<<<<<<< HEAD
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .forms import RegistrationForm, LoginForm, QueryForm, UpdateRecordForm
from .db import (execute_query, get_table_names, get_table_data, 
                 get_table_columns, get_primary_key, get_foreign_keys,
                 validate_table_name,get_db_connection)
import json
import logging
import re

# Create your views here.

logger = logging.getLogger(__name__)

# Pre-defined SQL Queries from the original file
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

# Authentication Views
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to the Pharmacy System.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard(request):
    """Main dashboard view"""
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard.html', context)

def is_safe_query(sql):
    """Check if SQL query is safe (only SELECT statements)"""
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith('SELECT'):
        return False, "Only SELECT queries are allowed"
    
    # Block dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
                         'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False, f"Dangerous keyword '{keyword}' not allowed"
    
    return True, "OK"

@login_required
def view_data(request):
    """View database tables with pagination"""
    tables = get_table_names()
    selected_table = request.GET.get('table', '')
    page = request.GET.get('page', 1)
    table_data = []
    columns = []
    total_count = 0
    
    if selected_table and tables:
        try:
            # Get total count
            validate_table_name(selected_table)
            count_sql = f'SELECT COUNT(*) FROM "{selected_table}"'
            total_count_result = execute_query(count_sql, fetch_one=True)
            total_count = total_count_result[0] if total_count_result else 0
            
            # Get paginated data
            per_page = 50
            offset = (int(page) - 1) * per_page
            table_data = get_table_data(selected_table, limit=per_page, offset=offset)
            columns_info = get_table_columns(selected_table)
            columns = [col[0] for col in columns_info]
            
            # Create paginator
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

@login_required
def run_queries(request):
    """Run pre-defined or custom SQL queries"""
    results = None
    columns = None
    error = None
    executed_query = None
    
    if request.method == 'POST':
        selected_query = request.POST.get('selected_query')
        custom_sql = request.POST.get('custom_sql', '')
        
        if selected_query == '20' and custom_sql:
            # Validate custom SQL for safety
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

@login_required
def add_record(request):
    """Add a new record to a table"""
    tables = get_table_names()
    
    if request.method == 'POST':
        table_name = request.POST.get('table_name')
        
        try:
            validate_table_name(table_name)
            columns_info = get_table_columns(table_name)
            fk_relations = get_foreign_keys(table_name)
            
            # Build record data from POST
            record_data = {}
            for key, value in request.POST.items():
                if key not in ['csrfmiddlewaretoken', 'table_name'] and value.strip():
                    # Check if this is a foreign key
                    is_fk = any(fk[0] == key for fk in fk_relations)
                    
                    # Convert value types
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
            
            # Build INSERT query
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
    
    # GET request - show form
    selected_table = request.GET.get('table', '')
    columns_info = []
    fk_relations = []
    pk_column = None
    
    if selected_table:
        try:
            validate_table_name(selected_table)
            columns_info = get_table_columns(selected_table)
            fk_relations = get_foreign_keys(selected_table)
            pk_column = get_primary_key(selected_table)
        except Exception as e:
            messages.error(request, f'Error loading columns: {e}')
    
    context = {
        'tables': tables,
        'selected_table': selected_table,
        'columns_info': columns_info,
        'fk_relations': fk_relations,
        'pk_column': pk_column,
    }
    return render(request, 'add_record.html', context)

@login_required
def update_record(request):
    """Update an existing record"""
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
            
            # Build update data from POST
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
            
            # Build UPDATE query
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
    
    # Get existing record data for display
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

@login_required
@csrf_exempt
def api_get_table_schema(request):
    """API endpoint to get table schema for dynamic form generation"""
    if request.method == 'GET':
        table_name = request.GET.get('table', '')
        if table_name:
            try:
                columns = get_table_columns(table_name)
                # Exclude auto-increment columns (serial/bigserial)
                schema = []
                for col in columns:
                    col_name = col[0]
                    data_type = col[1]
                    is_nullable = col[2]
                    # Skip primary key columns for insert
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

@login_required
@csrf_exempt
def api_get_record(request):
    """API endpoint to get a record for editing"""
    if request.method == 'GET':
        table_name = request.GET.get('table', '')
        record_id = request.GET.get('id', '')
        
        if table_name and record_id:
            try:
                pk_column = f"{table_name[:-1]}_id" if table_name.endswith('s') else 'id'
                sql = f"SELECT * FROM {table_name} WHERE {pk_column} = %s"
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

@login_required
@csrf_exempt
def api_update_record(request):
    """API endpoint to update a record"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_name = data.get('table_name')
            record_id = data.get('record_id')
            update_data = data.get('update_data', {})
            
            if not table_name or not record_id or not update_data:
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            # Get primary key column
            columns_info = get_table_columns(table_name)
            pk_column = None
            
            # Try to find primary key column
            for col in columns_info:
                col_name = col[0]
                if col_name == 'id' or col_name == f"{table_name[:-1]}_id" or col_name == f"{table_name}_id":
                    pk_column = col_name
                    break
            
            if not pk_column:
                pk_column = columns_info[0][0]  # Use first column as fallback
            
            # Build UPDATE query
            set_clauses = [f"{col} = %s" for col in update_data.keys()]
            values = list(update_data.values())
            values.append(record_id)
            
            sql = f'UPDATE "{table_name}" SET {", ".join(set_clauses)} WHERE {pk_column} = %s'
            
            rows_affected = execute_query(sql, values)
            
            if rows_affected > 0:
                return JsonResponse({'success': True, 'message': f'Updated {rows_affected} record(s)'})
            else:
                return JsonResponse({'success': False, 'error': 'No record found or no changes made'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
=======
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
>>>>>>> master

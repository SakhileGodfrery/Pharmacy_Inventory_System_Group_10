<<<<<<< HEAD
from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda request: redirect('dashboard' if request.user.is_authenticated else 'login'), name='root'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('view-data/', views.view_data, name='view_data'),
    path('run-queries/', views.run_queries, name='run_queries'),
    path('add-record/', views.add_record, name='add_record'),
    path('update-record/', views.update_record, name='update_record'),
    
    # API endpoints
    path('api/table-schema/', views.api_get_table_schema, name='api_table_schema'),
    path('api/get-record/', views.api_get_record, name='api_get_record'),
=======
from django.urls import path  # type: ignore[import]
from . import views

urlpatterns = [
    # Main pages
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('batches/', views.batch_list, name='batch_list'),
    path('reorder/', views.reorder_report, name='reorder_report'),

    # Queries from your SQL file (select important ones)
    path('query1/', views.query_patient_prescription_history, name='query1'),
    path('query2/', views.query_sales_by_category, name='query2'),
    path('query3/', views.query_low_stock_products, name='query3'),
    path('query4/', views.query_top5_products, name='query4'),
    path('query12/', views.query_rounding_report, name='query12'),
    path('query14/', views.query_expiry_alerts, name='query14'),
    path('query19/', views.query_patient_journey, name='query19'),
    path('query21/', views.query_top_products_subquery, name='query21'),
>>>>>>> master
]
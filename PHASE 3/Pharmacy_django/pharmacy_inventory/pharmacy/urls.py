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
]
from django.urls import path
from django.shortcuts import redirect
from . import views

def root_redirect(request):
    return redirect('dashboard' if request.session.get('user_id') else 'login')

urlpatterns = [
    path('', root_redirect, name='root'),
    
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
]
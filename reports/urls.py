from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profit-analysis/', views.profit_analysis, name='profit_analysis'),
    path('inventory-status/', views.inventory_status, name='inventory_status'),
    path('sales-summary/', views.sales_summary, name='sales_summary'),
    path('payment-status/', views.payment_status, name='payment_status'),
    path('export/', views.export_report, name='export_report'),
    path('ajax/chart-data/', views.ajax_chart_data, name='ajax_chart_data'),
]
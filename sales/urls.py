from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='list'),
    path('create/', views.sale_create, name='create'),
    path('<int:pk>/', views.sale_detail, name='detail'),
    path('<int:pk>/edit/', views.sale_edit, name='edit'),
    path('<int:pk>/finalize/', views.sale_finalize, name='finalize'),
    path('<int:pk>/create-invoice/', views.sale_create_invoice, name='create_invoice'),
    path('invoice/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:pk>/print/', views.invoice_print, name='invoice_print'),
    path('ajax/vehicle-details/', views.ajax_vehicle_details, name='ajax_vehicle_details'),
    path('ajax/calculate-margin/', views.ajax_calculate_margin, name='ajax_calculate_margin'),
    path('ajax/quick-sale/', views.quick_sale, name='quick_sale'),
]
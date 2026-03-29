from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='list'),
    path('create/', views.payment_create, name='create'),
    path('<int:pk>/', views.payment_detail, name='detail'),
    path('<int:pk>/edit/', views.payment_edit, name='edit'),
    path('outstanding/', views.outstanding_invoices, name='outstanding'),
    path('quick-payment/<int:invoice_id>/', views.quick_payment, name='quick_payment'),
    path('reminder/<int:invoice_id>/', views.payment_reminder_create, name='create_reminder'),
    path('payment-plan/<int:invoice_id>/', views.payment_plan_create, name='create_payment_plan'),
    path('payment-plan/detail/<int:pk>/', views.payment_plan_detail, name='payment_plan_detail'),
    path('installment/<int:installment_id>/payment/', views.installment_payment, name='installment_payment'),
    path('ajax/invoice-balance/', views.ajax_invoice_balance, name='ajax_invoice_balance'),
]
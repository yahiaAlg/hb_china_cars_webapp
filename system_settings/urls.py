from django.urls import path
from . import views

app_name = 'system_settings'

urlpatterns = [
    path('', views.system_status, name='system_status'),
    path('configuration/', views.system_configuration, name='configuration'),
    path('exchange-rates/', views.exchange_rates, name='exchange_rates'),
    path('exchange-rates/create/', views.exchange_rate_create, name='exchange_rate_create'),
    path('exchange-rates/<int:pk>/edit/', views.exchange_rate_edit, name='exchange_rate_edit'),
    path('tax-rates/', views.tax_rates, name='tax_rates'),
    path('tax-rates/create/', views.tax_rate_create, name='tax_rate_create'),
    path('tax-rates/<int:pk>/edit/', views.tax_rate_edit, name='tax_rate_edit'),
    path('user-preferences/', views.user_preferences, name='user_preferences'),
    path('system-logs/', views.system_logs, name='system_logs'),
    path('system-logs/clear/', views.clear_old_logs, name='clear_old_logs'),
    path('ajax/latest-rate/', views.ajax_latest_exchange_rate, name='ajax_latest_rate'),
]
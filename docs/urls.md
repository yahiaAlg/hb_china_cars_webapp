# Django URLs Compilation

This document contains all URL patterns from all Django apps in the project.

---

# Customers App

## customers/urls.py

```
python
from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customer_list, name='list'),
    path('create/', views.customer_create, name='create'),
    path('<int:pk>/', views.customer_detail, name='detail'),
    path('<int:pk>/edit/', views.customer_edit, name='edit'),
    path('<int:pk>/add-note/', views.customer_add_note, name='add_note'),
    path('<int:pk>/toggle-status/', views.customer_toggle_status, name='toggle_status'),
    path('ajax/search/', views.customer_ajax_search, name='ajax_search'),
    path('ajax/quick-create/', views.customer_quick_create, name='quick_create'),
]
```

---

# Commissions App

## commissions/urls.py

```
python
from django.urls import path
from . import views

app_name = 'commissions'

urlpatterns = [
    path('my-commission/', views.my_commission, name='my_commission'),
    path('overview/', views.commission_overview, name='overview'),
    path('trader-performance/', views.trader_performance, name='trader_performance'),
    path('tiers/', views.commission_tiers, name='tiers'),
    path('tiers/create/', views.commission_tier_create, name='tier_create'),
    path('tiers/<int:pk>/edit/', views.commission_tier_edit, name='tier_edit'),
    path('adjustment/<int:summary_id>/', views.commission_adjustment_create, name='create_adjustment'),
    path('payment/<int:summary_id>/', views.commission_payment_create, name='create_payment'),
    path('close-period/<int:year>/<int:month>/', views.close_commission_period, name='close_period'),
    path('approve/<int:summary_id>/', views.approve_commission, name='approve_commission'),
    path('ajax/calculation/', views.ajax_commission_calculation, name='ajax_calculation'),
]
```

---

# Core App

## core/urls.py

```
python
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
```

---

# Inventory App

## inventory/urls.py

```
python
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.vehicle_list, name='list'),
    path('create/', views.vehicle_create, name='create'),
    path('<int:pk>/', views.vehicle_detail, name='detail'),
    path('<int:pk>/edit/', views.vehicle_edit, name='edit'),
    path('<int:pk>/reserve/', views.vehicle_reserve, name='reserve'),
    path('<int:pk>/release-reservation/', views.vehicle_release_reservation, name='release_reservation'),
    path('<int:pk>/add-photo/', views.vehicle_add_photo, name='add_photo'),
    path('alerts/', views.stock_alerts, name='alerts'),
    path('alerts/<int:pk>/resolve/', views.resolve_alert, name='resolve_alert'),
]
```

---

# Payments App

## payments/urls.py

```
python
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
```

---

# Purchases App

## purchases/urls.py

```
python
from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.purchase_list, name='list'),
    path('create/', views.purchase_create, name='create'),
    path('<int:pk>/', views.purchase_detail, name='detail'),
    path('<int:pk>/add-freight/', views.purchase_add_freight, name='add_freight'),
    path('<int:pk>/add-customs/', views.purchase_add_customs, name='add_customs'),
    path('<int:pk>/edit-freight/', views.purchase_edit_freight, name='edit_freight'),
    path('<int:pk>/edit-customs/', views.purchase_edit_customs, name='edit_customs'),
    path('ajax/calculate-customs/', views.ajax_calculate_customs, name='ajax_calculate_customs'),
    path('customs/<int:pk>/mark-cleared/', views.customs_mark_cleared, name='mark_cleared'),
]
```

---

# Reports App

## reports/urls.py

```
python
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
```

---

# Sales App

## sales/urls.py

```
python
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
```

---

# Suppliers App

## suppliers/urls.py

```
python
from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.supplier_list, name='list'),
    path('create/', views.supplier_create, name='create'),
    path('<int:pk>/', views.supplier_detail, name='detail'),
    path('<int:pk>/edit/', views.supplier_edit, name='edit'),
    path('<int:pk>/toggle-status/', views.supplier_toggle_status, name='toggle_status'),
    path('ajax/search/', views.supplier_ajax_search, name='ajax_search'),
]
```

---

# System Settings App

## system_settings/urls.py

```
python
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
```

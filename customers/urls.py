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
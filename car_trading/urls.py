"""
URL Configuration for car_trading project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('purchases/', include('purchases.urls')),
    path('inventory/', include('inventory.urls')),
    path('customers/', include('customers.urls')),
    path('sales/', include('sales.urls')),
    path('payments/', include('payments.urls')),
    path('commissions/', include('commissions.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', include('system_settings.urls')),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin
admin.site.site_header = "Bureau Auto Trading - Administration"
admin.site.site_title = "Bureau Auto Trading Admin"
admin.site.index_title = "Système de Gestion"
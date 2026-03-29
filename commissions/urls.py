from django.urls import path
from . import views

app_name = "commissions"

urlpatterns = [
    path("", views.commission_index, name="index"),  # ← add this
    path("my-commission/", views.my_commission, name="my_commission"),
    path("overview/", views.commission_overview, name="overview"),
    path("trader-performance/", views.trader_performance, name="trader_performance"),
    path("tiers/", views.commission_tiers, name="tiers"),
    path("tiers/create/", views.commission_tier_create, name="tier_create"),
    path("tiers/<int:pk>/edit/", views.commission_tier_edit, name="tier_edit"),
    path(
        "adjustment/<int:summary_id>/",
        views.commission_adjustment_create,
        name="create_adjustment",
    ),
    path(
        "payment/<int:summary_id>/",
        views.commission_payment_create,
        name="create_payment",
    ),
    path(
        "close-period/<int:year>/<int:month>/",
        views.close_commission_period,
        name="close_period",
    ),
    path(
        "approve/<int:summary_id>/", views.approve_commission, name="approve_commission"
    ),
    path(
        "ajax/calculation/", views.ajax_commission_calculation, name="ajax_calculation"
    ),
]

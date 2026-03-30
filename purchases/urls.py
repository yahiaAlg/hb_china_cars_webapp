from django.urls import path
from . import views

app_name = "purchases"

urlpatterns = [
    # ── List / CRUD ────────────────────────────────────────────────────────────
    path("", views.purchase_list, name="list"),
    path("create/", views.purchase_create, name="create"),
    path("<int:pk>/", views.purchase_detail, name="detail"),
    path("<int:pk>/edit/", views.purchase_edit, name="edit"),
    path("<int:pk>/delete/", views.purchase_delete, name="delete"),
    # ── Container-level freight & customs ─────────────────────────────────────
    path("<int:pk>/add-freight/", views.purchase_add_freight, name="add_freight"),
    path("<int:pk>/edit-freight/", views.purchase_edit_freight, name="edit_freight"),
    path("<int:pk>/add-customs/", views.purchase_add_customs, name="add_customs"),
    path("<int:pk>/edit-customs/", views.purchase_edit_customs, name="edit_customs"),
    # ── Per-vehicle freight ────────────────────────────────────────────────────
    path(
        "<int:purchase_pk>/items/<int:item_pk>/add-freight/",
        views.line_item_add_freight,
        name="line_item_add_freight",
    ),
    path(
        "<int:purchase_pk>/items/<int:item_pk>/edit-freight/",
        views.line_item_edit_freight,
        name="line_item_edit_freight",
    ),
    # ── Per-vehicle customs ────────────────────────────────────────────────────
    path(
        "<int:purchase_pk>/items/<int:item_pk>/add-customs/",
        views.line_item_add_customs,
        name="line_item_add_customs",
    ),
    path(
        "<int:purchase_pk>/items/<int:item_pk>/edit-customs/",
        views.line_item_edit_customs,
        name="line_item_edit_customs",
    ),
    # ── AJAX & status actions ──────────────────────────────────────────────────
    path(
        "ajax/calculate-customs/",
        views.ajax_calculate_customs,
        name="ajax_calculate_customs",
    ),
    path(
        "customs/<int:pk>/mark-cleared/",
        views.customs_mark_cleared,
        name="mark_cleared",
    ),
    path(
        "line-item-customs/<int:pk>/mark-cleared/",
        views.line_item_customs_mark_cleared,
        name="line_item_mark_cleared",
    ),
    path(
        "<int:pk>/mark-arrived/",
        views.purchase_mark_arrived,
        name="mark_arrived",
    ),
]

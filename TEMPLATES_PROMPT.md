# Django Template Conversion - AI Instructions

## Project Context

You are converting static HTML templates to dynamic Django templates for an Algerian car trading inventory management system (HB China Cars). The system tracks:

- Vehicle purchases from Chinese suppliers (FOB pricing, freight, customs)
- Inventory management with status tracking
- Sales to Algerian customers
- Invoices and payment plans
- Trader commissions
- Financial reporting

**Tech Stack:** Django 4.2+, Bootstrap 5, Chart.js, Python 3.8+

## Required Files Per Request

User will provide these files for each template conversion:

### Always Required:

1. **Static HTML file** - The template to convert
2. **Related models.py** - Models used by this template
3. **populate_db.py** - Shows data structure and relationships

### When Applicable:

4. **Associated CSS files** - For styling reference
5. **JavaScript files** - For interactive elements
6. **Current views.py** - Existing view patterns
7. **URLs.py** - Current routing structure

## Conversion Rules

### 1. Template Structure

```django
{% extends 'base.html' %}
{% load static %}
{% load humanize %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/page.css' %}" />
{% endblock %}

{% block title %}Page Title{% endblock %}

{% block content %}
<!-- Dynamic content here -->
{% endblock %}

{% block extra_js %}
<!-- Page-specific JS -->
{% endblock %}
```

### 2. View Function Requirements

**Fetch real data** - No placeholders:

```python
@login_required
def view_name(request):
    # Query models
    items = Model.objects.filter(...)

    # Calculate metrics
    total = sum(item.field for item in items)

    # Compare periods for % change
    current = Model.objects.filter(date__gte=this_month)
    last = Model.objects.filter(date__gte=last_month, date__lt=this_month)
    change = ((current - last) / last) * 100 if last else 0

    # Prepare chart data
    chart_labels = json.dumps(['Jan', 'Feb'])
    chart_values = json.dumps([100, 200])

    context = {'items': items, 'total': total}
    return render(request, 'app/template.html', context)
```

### 3. Data Fetching Patterns

**Single object:**

```python
vehicle = Vehicle.objects.get(id=pk)
```

**Lists with filters:**

```python
vehicles = Vehicle.objects.filter(status='available').order_by('-created_at')
```

**Aggregations:**

```python
from django.db.models import Sum, Count, Avg
total_revenue = Sale.objects.aggregate(total=Sum('sale_price'))['total']
```

**Related data:**

```python
# Forward FK
vehicle.vehicle_purchase.supplier.name

# Reverse FK
customer.sale_set.filter(is_finalized=True)
```

**Calculated properties:**

```python
# Use model properties
vehicle.landed_cost  # Auto-calculates purchase + freight + customs
sale.margin_percentage  # (sale_price - cost) / cost * 100
```

### 4. Chart.js Integration

**Views.py:**

```python
import json

labels = [item.month for item in data]
values = [float(item.total) for item in data]

context = {
    'chart_labels': json.dumps(labels),
    'chart_data': json.dumps(values)
}
```

**Template:**

```javascript
const chart = new Chart(ctx, {
    data: {
        labels: {{ chart_labels|safe }},
        datasets: [{ data: {{ chart_data|safe }} }]
    }
});
```

### 5. URL Patterns

**Static links → Django URLs:**

```django
<a href="{% url 'app:view_name' %}">Link</a>
<a href="{% url 'app:detail' pk=item.id %}">Detail</a>
<a href="{% url 'app:edit' item.id %}">Edit</a>
```

**URL config:**

```python
app_name = 'app'
urlpatterns = [
    path('', views.list_view, name='list'),
    path('<int:pk>/', views.detail_view, name='detail'),
    path('create/', views.create_view, name='create'),
]
```

### 6. Template Patterns

**Loops:**

```django
{% for item in items %}
    <tr>
        <td>{{ item.name }}</td>
        <td>{{ item.price|floatformat:0 }} DA</td>
    </tr>
{% empty %}
    <tr><td colspan="2">No items found</td></tr>
{% endfor %}
```

**Conditionals:**

```django
{% if item.status == 'available' %}
    <span class="badge badge-success">Available</span>
{% elif item.status == 'sold' %}
    <span class="badge badge-secondary">Sold</span>
{% endif %}
```

**Number formatting:**

```django
{{ value|floatformat:0 }}           {# 1234567 #}
{{ value|floatformat:2 }}           {# 1234567.89 #}
{{ value|intcomma }}                {# 1,234,567 #}
{{ percentage|floatformat:1 }}%     {# 15.5% #}
```

**Dates:**

```django
{{ date|date:"d/m/Y" }}             {# 13/02/2026 #}
{{ datetime|date:"d/m/Y H:i" }}     {# 13/02/2026 14:30 #}
```

### 7. Role-Based Access

```python
# View level
@login_required
@role_required(['manager', 'finance'])
def sensitive_view(request):
    pass

# Template level
{% if user.userprofile.is_manager %}
    <button>Delete</button>
{% endif %}
```

### 8. Critical Requirements

**Always:**

- Use actual model data, never hardcoded values
- Calculate metrics dynamically
- Include month-over-month comparisons for metrics
- Sort lists logically (recent first, alphabetical, etc.)
- Handle empty states (`{% empty %}`)
- Add `@login_required` to all views
- Use `json.dumps()` for Chart.js data
- Include `|safe` filter for JSON in templates

**Never:**

- Use placeholder text like "Lorem ipsum"
- Leave hardcoded numbers in templates
- Use `|map` filter (Django doesn't have it)
- Forget to import models in views
- Skip error handling for missing data

## Output Format

For each conversion, provide:

1. **views.py** - Complete function with queries
2. **template.html** - Full Django template
3. **urls.py** - URL patterns
4. **Brief README** - Key features and data sources

## Model Reference

Key models and their relationships:

```
Supplier → Purchase → Vehicle → Sale → Invoice → Payment
                  ↓        ↓       ↓
            FreightCost  Customer  Commission
            CustomsDecl
```

Common calculations:

- `Vehicle.landed_cost` = purchase + freight + customs
- `Sale.margin_amount` = sale_price - landed_cost
- `Sale.commission_amount` = margin \* commission_rate
- `Invoice.balance_due` = total_ttc - amount_paid

## Request Format

When user requests conversion, they'll say:

```
Template: customers.html
Purpose: List all customers with sales stats
Features: filtering, search, create button
Models: Customer, Sale, Invoice
```

# Car Reselling SaaS - Django Web Application

## Project Overview

This is a comprehensive Car Reselling Management System built with Django for the Algerian automobile market. It handles the complete lifecycle of vehicle trading including purchases, inventory management, sales, commissions, payments, and reporting.

---

## Project Structure

```
car_reselling_webapp/
├── car_trading/                 # Main Django project settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py             # Django configuration
│   ├── urls.py                 # Main URL routing
│   └── wsgi.py
├── commissions/                # Commission management app
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py               # CommissionTierForm, CommissionAdjustmentForm, etc.
│   ├── models.py              # CommissionTier, CommissionPeriod, CommissionSummary, etc.
│   ├── urls.py
│   └── views.py               # my_commission, commission_overview, trader_performance
├── core/                      # Core functionality app
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── decorators.py          # @trader_required, @manager_required
│   ├── models.py              # UserProfile, Currency, ExchangeRate, BaseModel
│   ├── signals.py
│   ├── urls.py
│   ├── utils.py
│   └── views.py               # index, dashboard
├── customers/                 # Customer management app
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py               # CustomerForm, CustomerSearchForm, QuickCustomerForm
│   ├── models.py              # Customer, CustomerNote
│   ├── urls.py
│   └── views.py               # customer_list, customer_create, customer_detail, etc.
├── inventory/                 # Vehicle inventory management
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py               # VehicleForm, VehicleSearchForm, ReservationForm
│   ├── models.py              # Vehicle, VehiclePhoto, StockAlert
│   ├── urls.py
│   └── views.py               # vehicle_list, vehicle_detail, vehicle_reserve
├── payments/                  # Payment tracking and management
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py               # PaymentForm, QuickPaymentForm, PaymentReminderForm
│   ├── models.py              # Payment, PaymentReminder, PaymentPlan
│   ├── urls.py
│   └── views.py               # payment_list, payment_create, outstanding_invoices
├── purchases/                 # Vehicle purchases and imports
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py               # PurchaseForm, FreightCostForm, CustomsDeclarationForm
│   ├── models.py              # Purchase, FreightCost, CustomsDeclaration
│   ├── urls.py
│   └── views.py               # purchase_list, purchase_detail, customs management
├── reports/                   # Reporting and analytics
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py               # ProfitAnalysisForm, InventoryStatusForm, etc.
│   ├── models.py
│   ├── urls.py
│   └── views.py               # profit_analysis, inventory_status, sales_summary
├── sales/                     # Sales management
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py               # SaleForm, InvoiceForm, SaleSearchForm
│   ├── models.py              # Sale, Invoice
│   ├── urls.py
│   └── views.py               # sale_list, sale_create, invoice_detail
├── suppliers/                 # Supplier management
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py               # SupplierForm, SupplierSearchForm
│   ├── models.py              # Supplier
│   ├── urls.py
│   └── views.py               # supplier_list, supplier_detail
├── system_settings/           # System configuration
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py               # SystemConfigurationForm, ExchangeRateForm
│   ├── models.py              # SystemConfiguration, ExchangeRateHistory, etc.
│   ├── urls.py
│   └── views.py               # system_configuration, exchange_rates, system_logs
├── frontend/                  # Static frontend templates
├── static/                    # Static files (CSS, JS, images)
├── templates/                 # Django templates
└── manage.py                  # Django management script
```

---

## Template Structure

Based on the `render()` function calls in the views, here is the complete template structure:

### Base Template

```
templates/
└── base.html                  # Main base template
```

### Customers App Templates

```
templates/customers/
├── list.html                  # Customer list view
├── detail.html                 # Customer detail with purchase history
├── form.html                  # Customer create/edit form
└── quick_form.html            # Quick customer creation modal
```

### Commissions App Templates

```
templates/commissions/
├── my_commission.html         # Trader's commission view
├── overview.html              # Commission overview
├── trader_performance.html    # Trader performance comparison
├── tiers.html                # Commission tiers management
├── tier_form.html             # Create/edit commission tier
├── adjustment_form.html      # Create commission adjustment
└── payment_form.html         # Create commission payment
```

### Core App Templates

```
templates/core/
├── index.html                # Home/landing page
└── dashboard.html            # Main dashboard with metrics
```

### Inventory App Templates

```
templates/inventory/
├── list.html                 # Vehicle inventory list
├── detail.html               # Vehicle detail view
├── form.html                 # Vehicle create/edit form
├── photo_form.html           # Add vehicle photos
└── alerts.html               # Stock alerts management
```

### Payments App Templates

```
templates/payments/
├── list.html                 # Payment list
├── detail.html               # Payment detail
├── form.html                 # Payment create/edit
├── outstanding.html          # Outstanding invoices report
├── quick_payment_form.html   # Quick payment entry
├── reminder_form.html       # Payment reminder
├── payment_plan_form.html   # Create payment plan
└── payment_plan_detail.html # Payment plan installments
```

### Purchases App Templates

```
templates/purchases/
├── list.html                 # Purchase list
├── detail.html               # Purchase detail with costs
├── form.html                 # Purchase create form
├── freight_form.html         # Add/edit freight costs
└── customs_form.html        # Customs declaration form
```

### Reports App Templates

```
templates/reports/
├── dashboard.html            # Reports dashboard
├── profit_analysis.html     # Profit analysis report
├── inventory_status.html    # Inventory status report
├── sales_summary.html       # Sales summary report
├── payment_status.html     # Payment status report
├── export.html             # Export options
└── pdf_export.html         # PDF export template
```

### Sales App Templates

```
templates/sales/
├── list.html                # Sales list
├── detail.html              # Sale detail view
├── form.html                # Sale create/edit form
├── invoice_detail.html      # Invoice detail
├── invoice_print.html      # Print-ready invoice
└── quick_sale.html         # Quick sale modal
```

### Suppliers App Templates

```
templates/suppliers/
├── list.html                # Supplier list
├── detail.html              # Supplier detail
└── form.html                # Supplier create/edit form
```

### System Settings Templates

```
templates/system_settings/
├── configuration.html       # System configuration
├── exchange_rates.html     # Exchange rates management
├── exchange_rate_form.html # Create/edit exchange rate
├── tax_rates.html          # Tax rates management
├── tax_rate_form.html      # Create/edit tax rate
├── user_preferences.html   # User preferences
├── system_logs.html        # System logs viewer
└── system_status.html      # System status dashboard
```

### Registration Templates

```
templates/registration/
└── login.html              # Login page
```

---

## Information System Flow

### 1. Purchase Flow (Vehicle Acquisition)

```
Supplier → Purchase → Freight Cost → Customs Declaration → Vehicle Inventory
```

1. Create supplier record (Suppliers app)
2. Create purchase order (Purchases app)
3. Add freight/logistics costs (Purchases app)
4. Process customs declaration (Purchases app)
5. Vehicle becomes available in inventory (Inventory app)

### 2. Sales Flow (Vehicle Sale)

```
Customer → Sale → Invoice → Payment → Commission
```

1. Create/edit customer (Customers app)
2. Create sale transaction (Sales app)
3. Generate invoice (Sales app)
4. Record payment (Payments app)
5. Calculate and pay commission (Commissions app)

### 3. Reporting Flow

```
Dashboard → Various Reports → Export
```

1. View dashboard with KPIs (Core app)
2. Generate profit analysis (Reports app)
3. Check inventory status (Reports app)
4. Review sales summary (Reports app)
5. Monitor payment status (Reports app)
6. Export reports to PDF/Excel

---

## User Roles

| Role    | Description      | Permissions                       |
| ------- | ---------------- | --------------------------------- |
| Manager | Administrator    | Full access to all features       |
| Trader  | Salesperson      | Sales, customers, own commissions |
| Finance | Accounting staff | Purchases, payments, invoices     |
| Auditor | Read-only        | View all reports and data         |

---

## Key Features

### Customer Management

- Individual and company customer types
- Algerian wilaya (province) selection
- NIF/Tax ID for companies
- Customer notes and interaction history
- Outstanding balance tracking

### Vehicle Inventory

- VIN/Chassis number tracking
- Status management (In Transit → At Customs → Available → Reserved → Sold)
- Photo documentation
- Automatic stock alerts for slow-moving vehicles
- Reservation system for traders

### Purchase Management

- Supplier management
- FOB price in multiple currencies
- Freight cost tracking
- Customs duty and tax calculation
- Complete landed cost calculation

### Sales Management

- Vehicle assignment to traders
- Margin calculation
- Commission calculation
- Invoice generation
- Payment tracking

### Commission System

- Performance-based tier system
- Monthly commission periods
- Manual adjustments
- Payment tracking

### Payment System

- Multiple payment methods
- Payment reminders
- Installment plans
- Outstanding balance tracking

### Reports & Analytics

- Profit analysis by period, trader, customer
- Inventory status and valuation
- Sales summaries
- Payment status reports
- Export to PDF/Excel

---

## Technology Stack

- **Backend**: Django 4.x
- **Database**: SQLite (default) / PostgreSQL (production)
- **Frontend**: HTML5, CSS3, JavaScript
- **Forms**: Django Forms + Crispy Forms
- **Templates**: Django Template Language
- **Charts**: Chart.js

---

## URL Routing Summary

| App             | URL Prefix    | Key Endpoints                  |
| --------------- | ------------- | ------------------------------ |
| core            | /             | index, dashboard               |
| customers       | /customers/   | list, create, detail, edit     |
| commissions     | /commissions/ | overview, tiers, my-commission |
| inventory       | /inventory/   | list, detail, alerts           |
| payments        | /payments/    | list, outstanding, create      |
| purchases       | /purchases/   | list, detail, create           |
| reports         | /reports/     | profit-analysis, sales-summary |
| sales           | /sales/       | list, detail, create-invoice   |
| suppliers       | /suppliers/   | list, detail, create           |
| system_settings | /settings/    | configuration, exchange-rates  |

---

## Quick Start

1. Install dependencies:

```
bash
pip install -r requirements.txt
```

2. Run migrations:

```
bash
python manage.py migrate
```

3. Create superuser:

```
bash
python manage.py createsuperuser
```

4. Run development server:

```
bash
python manage.py runserver
```

5. Access the application at `http://localhost:8000`

---

## License

This project is proprietary software for Bureau de Commerce Automobile Algérien.

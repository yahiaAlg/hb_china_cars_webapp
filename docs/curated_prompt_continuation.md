# Django Template Continuation Prompt

Create the remaining Django templates for the Car Reselling SaaS application using Bootstrap 5, ChartJS, and custom CSS/JS with elegant open-source icon libraries (use Phosphor Icons or Remix Icon for consistent, modern iconography throughout the UI - include via CDN jsDelivr). Apply the EXISTING design system from base.css: CSS Variables include colors (--primary-navy: #1e3a5f, --primary-red: #dc2626, --accent-blue: #3b82f6, --success-green: #10b981, --warning-yellow: #f59e0b, --danger-red: #ef4444, --gray-50 to --gray-900 scale), border-radius (8px standard, 4px small, 12px large), shadows (--shadow-sm, --shadow, --shadow-md, --shadow-lg, --shadow-xl); Typography uses Montserrat font family at 14px base; Components include: navbar (fixed top, #1e3a5f background, 64px height), sidebar (fixed left, #f8f9fa background, 250px width), buttons (btn-primary #1e3a5f, btn-danger #dc2626, btn-success #10b981, btn-secondary with gray border), cards (white background, 12px border-radius, shadow), forms (form-input with focus state #1e3a5f border), alerts (info blue, warning yellow, error red, success green), badges, tables (thead #1e3a5f background). Create responsive HTML templates with Bootstrap 5 components.

## MISSING TEMPLATES TO CREATE:

### commissions/ (7 templates - ALL MISSING)

- **my_commission.html**: Trader's personal commission view with period selector, sales list, commission calculation breakdown, payout status
- **overview.html**: Manager view of all traders' commissions with period summary, filtering, bulk actions
- **trader_performance.html**: Performance comparison between traders with charts, statistics tables
- **tiers.html**: Commission tier configuration list with CRUD operations
- **tier_form.html**: Create/edit commission tier form
- **adjustment_form.html**: Form to add commission adjustments with trader selection, amount, reason
- **payment_form.html**: Commission payment recording form with payment method, reference, notes

### payments/ (6 templates missing, 2 exist)

- **detail.html**: Payment detail view with payment info, associated invoice, timeline
- **form.html**: Payment creation/editing form with amount, method, date, reference
- **quick_payment_form.html**: Simplified payment form for quick payment recording from invoice detail
- **reminder_form.html**: Form to create payment reminders with due date, message
- **payment_plan_form.html**: Create payment plan with installment configuration
- **payment_plan_detail.html**: Payment plan detail view with installment schedule, payment status tracking

### purchases/ (5 templates - ALL MISSING)

- **list.html**: Purchase list with filters (supplier, date, status), search, pagination
- **detail.html**: Purchase detail with vehicle info, costs breakdown (freight, customs, total)
- **form.html**: Purchase creation/editing form with supplier, vehicle, costs
- **freight_form.html**: Add/edit freight costs for a purchase
- **customs_form.html**: Customs declaration form with CIF calculation

### reports/ (6 templates missing, 1 exists)

- **profit_analysis.html**: Profit analysis by vehicle, period, trader with charts
- **inventory_status.html**: Current inventory status with value calculations, aging
- **sales_summary.html**: Sales summary by period, trader, vehicle with export options
- **payment_status.html**: Payment status overview with aging analysis
- **export.html**: Export center for CSV, Excel, PDF generation
- **pdf_export.html**: PDF report generation and download

### system_settings/ (6 templates - ALL MISSING)

- **configuration.html**: System configuration settings form
- **exchange_rates.html**: Exchange rate management with history, charts
- **tax_rates.html**: Tax rate configuration and history
- **user_preferences.html**: User preferences and profile settings
- **system_logs.html**: System activity logs with filtering
- **system_status.html**: System health status, version info, cache management

## EXISTING TEMPLATES (DO NOT RECREATE):

- base.html ✓
- core/index.html ✓
- core/dashboard.html ✓
- customers/detail.html, form.html, list.html, quick_form.html ✓
- inventory/alerts.html, detail.html, form.html, list.html ✓
- payments/list.html, outstanding.html ✓
- reports/dashboard.html ✓
- sales/detail.html, form.html, invoice_detail.html, invoice_print.html, list.html ✓
- suppliers/detail.html, form.html, list.html ✓
- registration/login.html ✓

## DJANGO APP CONTEXT:

Use the models from: commissions, payments, purchases, reports, system_settings apps
Use the views from: commissions/views.py, payments/views.py, purchases/views.py, reports/views.py, system_settings/views.py
Use the forms from: commissions/forms.py, payments/forms.py, purchases/forms.py, reports/forms.py, system_settings/forms.py
Use the URLs from: commissions/urls.py, payments/urls.py, purchases/urls.py, reports/urls.py, system_settings/urls.py

## DESIGN SYSTEM:

Follow the exact colors, typography, spacing, and components from static/css/base.css

Include proper Django template inheritance from base.html, use {% url %} for routing, {% csrf_token %} in forms, and follow the French/Arabic bilingual interface requirements as indicated by the model verbose_name fields.

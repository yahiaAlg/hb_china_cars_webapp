# HB China Cars — Design System Specification
> Version 1.0 — Auto Trading Platform (Django / Bootstrap 5)

---

## 1. Design Philosophy

**Aesthetic direction:** Industrial Minimalism — dark, dense, data-forward. Every element earns its space. No decorative filler, no gradients for the sake of it. The interface feels like a professional trading terminal: high information density, tight spacing, sharp contrasts, amber as the single warm accent against a cold slate palette.

**Core principles:**
- Dark-first. No light mode.
- Data is the hero — typography and spacing serve readability above all.
- One accent color only (`--accent: #f0a500`). Used sparingly and with intent.
- Borders over shadows for separation. Shadows only on elevated interactive states.
- Animations are subtle, fast (150–350ms), and purposeful — never decorative.

---

## 2. Color Palette

### Base Surfaces (darkest → lightest)
| Token | Hex | Usage |
|---|---|---|
| `--bg-base` | `#0d0f12` | Page background |
| `--bg-surface` | `#13161b` | Cards, sidebar, topbar |
| `--bg-raised` | `#1b1f27` | Nested cards, dropdown menus, inputs |
| `--bg-hover` | `#21262f` | Row/item hover state |

### Borders
| Token | Value | Usage |
|---|---|---|
| `--border` | `rgba(255,255,255,.07)` | Default dividers, card edges |
| `--border-strong` | `rgba(255,255,255,.13)` | Focused inputs, hovered cards |

### Accent (Amber)
| Token | Value | Usage |
|---|---|---|
| `--accent` | `#f0a500` | Primary CTA, active nav, icons, badges |
| `--accent-dim` | `rgba(240,165,0,.15)` | Accent backgrounds, highlights |
| `--accent-glow` | `rgba(240,165,0,.35)` | Focus rings, glow effects |

### Text
| Token | Hex | Usage |
|---|---|---|
| `--text-primary` | `#eef0f4` | Headings, values, primary content |
| `--text-secondary` | `#8a909e` | Body text, table cells, descriptions |
| `--text-muted` | `#545966` | Labels, timestamps, placeholders |

### Semantic Colors
| Role | Hex | Alpha bg | Usage |
|---|---|---|---|
| Success | `#22c55e` / display `#4ade80` | `rgba(34,197,94,.12)` | Positive deltas, finalized, pills |
| Danger | `#ef4444` / display `#f87171` | `rgba(239,68,68,.12)` | Errors, overdue, high alerts |
| Warning | `#f0a500` / display `#fbbf24` | `rgba(240,165,0,.15)` | Caution, pending |
| Info | `#38bdf8` / display `#7dd3fc` | `rgba(56,189,248,.12)` | Neutral info, in-transit |

### Chart / Data Visualization Color Sequence
Used in order for multi-series charts, doughnuts, and bar charts:
```
#f0a500  (amber)
#38bdf8  (sky blue)
#4ade80  (green)
#c4b5fd  (violet)
#fb923c  (orange)
#5eead4  (teal)
#f9a8d4  (pink)
#a5b4fc  (indigo)
#f87171  (red)
```

### Icon Background Variants (utility classes)
```css
.ic-amber  → rgba(240,165,0,.15)  / #fbbf24
.ic-blue   → rgba(56,189,248,.12) / #7dd3fc
.ic-green  → rgba(34,197,94,.12)  / #4ade80
.ic-purple → rgba(167,139,250,.12)/ #c4b5fd
.ic-red    → rgba(239,68,68,.12)  / #f87171
.ic-teal   → rgba(45,212,191,.12) / #5eead4
.ic-orange → rgba(251,146,60,.12) / #fb923c
.ic-pink   → rgba(244,114,182,.12)/ #f9a8d4
.ic-indigo → rgba(99,102,241,.12) / #a5b4fc
```

---

## 3. Typography

### Font Stack
| Role | Family | Weights | Usage |
|---|---|---|---|
| Display / UI | **Syne** (Google Fonts) | 400, 600, 700, 800 | All headings, nav labels, metric values, card titles, buttons |
| Body / Data | **DM Sans** (Google Fonts) | 300, 400, 500 | Body text, table cells, descriptions, form inputs |

```html
<!-- Required in <head> -->
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap" rel="stylesheet">
```

### Type Scale
| Element | Font | Size | Weight | Letter-spacing | Color |
|---|---|---|---|---|---|
| Page heading (H1) | Syne | 24px | 800 | `-0.025em` | `--text-primary` |
| Card / section title | Syne | 14–15px | 700 | `-0.01em` | `--text-primary` |
| Metric value (large) | Syne | 26px | 800 | none | `--text-primary` |
| Metric value (small) | Syne | 20px | 800 | none | `--text-primary` |
| Nav link label | DM Sans | 13.5px | 400 | none | `--text-secondary` |
| Body / table cell | DM Sans | 13–14px | 400 | none | `--text-secondary` |
| Section eyebrow | DM Sans | 10.5px | 600 | `0.1em` | `--text-muted` |
| Table header | DM Sans | 10.5px | 600 | `0.07em` | `--text-muted` |
| Badge / pill | DM Sans | 11px | 500 | `0.02em` | varies |
| Caption / timestamp | DM Sans | 11–12px | 400 | none | `--text-muted` |

All headings use `letter-spacing: -0.02em` to -0.03em (tighter tracking = more editorial).

---

## 4. Spacing & Layout

### CSS Variables
```css
--sidebar-w:    240px;   /* expanded */
--sidebar-w-sm: 68px;    /* collapsed */
--topbar-h:     60px;
```

### Border Radius
| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | `6px` | Buttons, inputs, icon boxes, nav links |
| `--radius-md` | `10px` | Dropdowns, toasts, form fields, pipeline items |
| `--radius-lg` | `16px` | Cards, chart panels, main containers |

### Page Padding
- Desktop page body: `28px 32px`
- Mobile page body: `20px 16px`
- Card internal padding: `18–22px 20px`
- Table cell padding: `13px 14px`

### Grid System
- Use Bootstrap 5's `row / col-*` for responsive column grids.
- Custom module grids use CSS `grid` with `auto-fill, minmax(200px, 1fr)`.
- Two-column content splits: `col-xl-8 / col-xl-4` or `col-xl-5 / col-xl-7`.
- Gap between cards: `14–20px` (`gap: 14px` or `g-3` / `g-4` in Bootstrap).

---

## 5. Component Library

### Cards
```css
/* Standard card */
background: var(--bg-surface);
border: 1px solid var(--border);
border-radius: var(--radius-lg);

/* On hover: */
border-color: var(--border-strong);
transform: translateY(-1px);          /* subtle lift */
/* Optional accent top line on hover */
::after { height: 2px; background: var(--accent); top: 0; }
```

### Metric Cards
- Icon box: 38–44px square, rounded `var(--radius-sm)`, uses `.ic-*` color variant.
- Eyebrow label: 10.5–11px, uppercase, `--text-muted`.
- Value: Syne 800, 20–26px.
- Delta badge: pill with up/down arrow icon, semantic color bg at 12% opacity.

### Pills / Badges
```css
/* Base */
display: inline-flex; align-items: center; gap: 4px;
padding: 3px 9px; border-radius: 20px;
font-size: 11px; font-weight: 500;

/* Variants */
.pill-success → bg rgba(34,197,94,.12),  color #4ade80
.pill-danger  → bg rgba(239,68,68,.12),  color #f87171
.pill-warning → bg rgba(240,165,0,.15),  color #fbbf24
.pill-info    → bg rgba(56,189,248,.12), color #7dd3fc
.pill-neutral → bg var(--bg-hover),      color var(--text-secondary)
```

### Tables
```css
/* Header row */
font-size: 10.5px; font-weight: 600; letter-spacing: 0.07em;
text-transform: uppercase; color: var(--text-muted);
border-bottom: 1px solid var(--border);

/* Data cells */
font-size: 13px; color: var(--text-secondary);
padding: 13px 14px;
border-bottom: 1px solid var(--border);

/* Row hover */
background: var(--bg-hover);
```

### Buttons
```css
/* Primary (accent) */
background: var(--accent); color: #0d0f12;
font-family: Syne; font-weight: 700; font-size: 14px;
border-radius: var(--radius-md); padding: 11px 20px;
transition: opacity .18s, transform .12s;
:hover { opacity: .9 }
:active { transform: scale(.99) }

/* Ghost / outline */
background: transparent;
border: 1px solid var(--border);
color: var(--text-secondary);
:hover { background: var(--bg-hover); border-color: var(--border-strong); color: var(--text-primary); }

/* Danger */
background: rgba(239,68,68,.15);
border: 1px solid rgba(239,68,68,.3);
color: #f87171;
```

### Form Inputs
```css
background: var(--bg-surface);
border: 1px solid var(--border);
border-radius: var(--radius-md);
color: var(--text-primary);
font-family: 'DM Sans', sans-serif; font-size: 14px;
padding: 11px 13px 11px 40px;  /* 40px left = icon space */

:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(240,165,0,.15);
  outline: none;
}
::placeholder { color: var(--text-muted); }
```
- Left icon: `position: absolute; left: 13px;` — use Bootstrap Icon, color `--text-muted`, transitions to `--accent` on focus.
- Labels: 12px, weight 500, `--text-secondary`, `letter-spacing: .03em`, block display above input.
- Error messages: 12px, `#f87171`, flex row with `bi-x-circle` icon.

### Navigation (Sidebar)
- Width: 240px expanded / 68px collapsed. Toggle persists in `localStorage`.
- Active link: `color: var(--accent)`, `background: var(--accent-dim)`, left `3px` amber bar `::before`.
- Collapsed state: `.nav-link-label`, `.brand-text`, `.user-info` all `opacity: 0`.
- Section labels: 9.5px, uppercase, `--text-muted`, hidden opacity on collapse.

### Alerts / Toasts
```css
background: var(--bg-raised);
border: 1px solid var(--border-strong);
border-radius: var(--radius-md);
padding: 12px 16px;
box-shadow: 0 8px 32px rgba(0,0,0,.4);
/* Left border accent by type: */
border-left: 3px solid var(--success / --danger / --warning / --info);
```
Auto-dismiss after 4000ms with fade + translateX transition.

---

## 6. Iconography

**Library:** Bootstrap Icons 1.11.3  
**CDN:** `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css`  
**Usage:** `<i class="bi bi-{icon-name}"></i>`

### Icon Size Conventions
| Context | Size |
|---|---|
| Sidebar nav | `16px` (via `font-size`) |
| Metric card icon box | `17–20px` |
| Form field prefix | `15px` |
| Topbar action buttons | `15px` |
| Table action icons | `14px` |
| Inline body text | `13–14px` |

### Standard Icon Mapping
| Module / Concept | Icon class |
|---|---|
| Dashboard | `bi-speedometer2` |
| Inventory / Vehicles | `bi-boxes` |
| Purchases / Imports | `bi-truck` |
| Sales | `bi-receipt` |
| Customers | `bi-people` |
| Suppliers | `bi-building` |
| Payments | `bi-credit-card` |
| Commissions | `bi-percent` |
| Reports | `bi-bar-chart-line` |
| Settings | `bi-sliders` |
| Alert / Notification | `bi-bell` |
| Export | `bi-file-earmark-bar-graph` |
| Manager role | `bi-shield-check` |
| Trader role | `bi-person-badge` |
| Finance role | `bi-calculator` |
| Auditor role | `bi-eye` |
| Success / Check | `bi-check-circle` |
| Error | `bi-exclamation-circle` |
| Warning | `bi-exclamation-triangle` |
| Info | `bi-info-circle` |
| Add / Create | `bi-plus-lg` |
| Edit | `bi-pencil` |
| Delete | `bi-trash` |
| Search | `bi-search` |
| Filter | `bi-funnel` |
| Download / Export | `bi-download` |
| Print | `bi-printer` |
| External link | `bi-arrow-up-right` |
| Back / Previous | `bi-arrow-left` |
| Chevron right | `bi-chevron-right` |
| Calendar | `bi-calendar3` |
| Currency / Money | `bi-currency-dollar` |
| Margin / Profit | `bi-piggy-bank` |
| Revenue trend | `bi-graph-up-arrow` |
| Outstanding | `bi-hourglass-split` |
| Vehicle / Car | `bi-car-front-fill` |
| Lock / Password | `bi-lock` |
| User / Login | `bi-person` |
| Sign out | `bi-box-arrow-left` |
| Sign in | `bi-box-arrow-in-right` |
| Layout sidebar | `bi-layout-sidebar` |
| Sidebar toggle | `bi-layout-sidebar` |
| Photo | `bi-image` |
| Attach / Upload | `bi-paperclip` |
| Phone | `bi-telephone` |
| Email | `bi-envelope` |
| Location | `bi-geo-alt` |
| Tag / Label | `bi-tag` |

---

## 7. Data Visualization (Chart.js 4)

**Library:** Chart.js 4.4.3  
**CDN:** `https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js`

### Global Defaults (apply once in base.html)
```js
Chart.defaults.color = '#8a909e';
Chart.defaults.borderColor = 'rgba(255,255,255,0.07)';
Chart.defaults.font.family = "'DM Sans', sans-serif";
```

### Tooltip Standard Config
```js
tooltip: {
  backgroundColor: '#1b1f27',
  borderColor: 'rgba(255,255,255,.13)',
  borderWidth: 1,
  titleColor: '#eef0f4',
  bodyColor: '#8a909e',
  padding: 10,
  cornerRadius: 8,
}
```

### Grid Lines
```js
grid: {
  color: 'rgba(255,255,255,0.05)',
  drawBorder: false
}
ticks: { color: '#545966', font: { size: 10.5 } }
```

### Chart Types & Patterns
| Chart Type | Use Case | Key Config |
|---|---|---|
| Area line | Revenue trends over time | `fill: true`, gradient fill from accent→transparent, `tension: 0.45`, `borderColor: #f0a500` |
| Horizontal bar | Trader performance / rankings | `indexAxis: 'y'`, `borderRadius: 6`, `borderSkipped: false`, multi-color from palette |
| Doughnut | Distribution / split | `cutout: '68%'`, `borderColor: #13161b`, `borderWidth: 3`, legend below |
| Vertical bar | Monthly comparisons | `borderRadius: 6`, `borderSkipped: false` |

### Area Chart Gradient Recipe
```js
const gradient = ctx.createLinearGradient(0, 0, 0, chartHeight);
gradient.addColorStop(0, 'rgba(240,165,0,0.25)');
gradient.addColorStop(1, 'rgba(240,165,0,0)');
// then: backgroundColor: gradient
```

---

## 8. Animation Conventions

| Pattern | Values |
|---|---|
| Default transition | `0.18s ease` |
| Card hover lift | `transform: translateY(-2px)` |
| Page entry | `fadeIn` — `opacity 0→1`, `translateY(10px → 0)`, `0.35s ease` |
| Staggered list entry | `animation-delay: nth-child * 40ms` (cap at ~400ms) |
| Toast slide-in | `translateX(20px → 0)`, `0.2s ease` |
| Toast dismiss | `opacity → 0`, `translateX(20px)`, `0.3s ease` |
| Sidebar collapse | `width` transition `0.18s ease` |

```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0); }
}
```

---

## 9. Template Architecture

### Inheritance Chain
```
base.html
├── registration/login.html   (standalone — no base)
├── core/index.html           (extends base)
├── core/dashboard.html       (extends base)
├── {app}/list.html           (extends base)
├── {app}/detail.html         (extends base)
├── {app}/form.html           (extends base)
└── {app}/...
```

### Blocks Available in base.html
| Block | Purpose |
|---|---|
| `{% block title %}` | `<title>` tag content (no suffix) |
| `{% block nav_{name} %}` | Inject `active` to highlight sidebar link |
| `{% block page_title %}` | Topbar breadcrumb main text |
| `{% block page_sub_text %}` | Topbar subtitle (date, count, etc.) |
| `{% block extra_css %}` | Page-specific `<style>` inside base `<style>` tag |
| `{% block content %}` | Main page body inside `.page-body` |
| `{% block extra_js %}` | Page-specific scripts before `</body>` |

### Available Nav Block Names
`nav_index`, `nav_dashboard`, `nav_inventory`, `nav_purchases`, `nav_sales`, `nav_customers`, `nav_suppliers`, `nav_payments`, `nav_commissions`, `nav_reports`, `nav_settings`

### Context Variables Always Available (from context processor)
- `request.user` — full auth user
- `request.user.userprofile` — UserProfile with `.role`, `.is_manager`, `.is_trader`, `.is_finance`, `.is_auditor`
- `app_name` — `"HB China Cars"`

---

## 10. Reusable HTML Snippets

### Section Eyebrow Label
```html
<div class="section-eyebrow">Section Title</div>
<!-- CSS: 10.5px, uppercase, letter-spacing .1em, --text-muted, font-weight 600 -->
```

### Section Header with Link
```html
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
  <span style="font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--text-muted);font-weight:600;">Section</span>
  <a href="/path/" style="font-size:12px;color:var(--accent);display:flex;align-items:center;gap:4px;">
    View all <i class="bi bi-arrow-right"></i>
  </a>
</div>
```

### Metric Card Shell
```html
<div class="metric-card">
  <div class="metric-icon ic-{color}"><i class="bi bi-{icon}"></i></div>
  <div class="metric-label">LABEL</div>
  <div class="metric-value">VALUE</div>
  <span class="metric-delta up|down|neutral">
    <i class="bi bi-arrow-up-right|arrow-down-right|dash"></i> text
  </span>
</div>
```

### Empty State
```html
<div style="text-align:center;padding:48px 20px;color:var(--text-muted);">
  <i class="bi bi-{icon}" style="font-size:32px;display:block;margin-bottom:12px;color:var(--border-strong);"></i>
  <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:var(--text-secondary);margin-bottom:6px;">No items found</div>
  <div style="font-size:13px;">Descriptive message here.</div>
  <a href="/create/" class="btn-primary" style="margin-top:16px;display:inline-flex;">
    <i class="bi bi-plus-lg"></i> Create first
  </a>
</div>
```

### Confirmation / Danger Zone Box
```html
<div style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.2);border-radius:var(--radius-md);padding:16px 18px;">
  <div style="font-family:'Syne',sans-serif;font-weight:700;color:#f87171;margin-bottom:4px;">
    <i class="bi bi-exclamation-triangle me-1"></i> Danger Zone
  </div>
  <p style="font-size:13px;color:var(--text-secondary);margin:0 0 12px;">Warning message.</p>
  <button class="btn-danger">Destructive Action</button>
</div>
```

---

## 11. Django-Specific Rules

- **Never** use Django filters that don't exist: no `|split`, no `|math`, no `|add` with floats.
- Time/date comparisons → always do in JavaScript (`new Date().getHours()`), not Django template tags.
- Animation delay sequences → use explicit `:nth-child(n)` CSS, never a `{% for %}` loop to generate CSS strings.
- All monetary values: format with `|floatformat:0` and append `DA` as text.
- Percentages: `|floatformat:1` with `%`.
- Dates: `|date:"M j, Y"` for short, `|date:"l, N j, Y"` for long.
- `{% csrf_token %}` in every POST form, no exceptions.
- Use `{% url 'app_name:view_name' %}` for all internal links.
- Guard all `userprofile` accesses with `{% if request.user.userprofile %}`.

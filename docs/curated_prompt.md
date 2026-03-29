Here's the standard prompt to feed — along with which files to attach:

---

**Prompt:**

> Using the attached `DESIGN_SYSTEM.md` as the strict visual specification and `base.html`, `dashboard.html`, `index.html`, `login.html` as live reference implementations, build all remaining Django templates for the `{APP_NAME}` app — specifically: `{list of templates}` — extending `base.html`, using Bootstrap 5 + Bootstrap Icons 1.11.3 + Chart.js 4 where needed, following every token, component pattern, spacing rule, and Django-specific constraint defined in the design system exactly, with no deviation in color, typography, or component structure.

**Files to attach every time:**
| File | Why |
|---|---|
| `DESIGN_SYSTEM.md` | The spec — tokens, components, rules |
| `base.html` | The shell being extended |
| `dashboard.html` | Most complete reference (charts, tables, metrics, alerts) |
| `index.html` | Card grid + animation reference |
| The relevant app's `views.py` | So the AI knows exact context variables |
| The relevant app's `models.py` | So it knows field names and relationships |
| `urls.md` (or the app's `urls.py`) | So `{% url %}` tags are correct |

**Swap `{APP_NAME}` and the template list** per batch — do one app at a time (e.g. `inventory` → `list.html, detail.html, form.html, alerts.html`) for best coherence.
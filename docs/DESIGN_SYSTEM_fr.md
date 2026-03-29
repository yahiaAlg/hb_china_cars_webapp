# HB China Cars — Spécification du Système de Design
> Version 2.0 — Plateforme de Commerce Auto (Django / Bootstrap 5)
> **Migration v1 → v2 :** Thème clair · Interface en français · Mobile-first responsive

---

## 0. Journal des modifications (v1 → v2)

| Domaine | v1 (Sombre) | v2 (Clair) |
|---|---|---|
| Thème global | Dark-first, fonds `#0d0f12` | Light-first, fonds `#f3f4f6` |
| Accent | `#f0a500` (amber vif) | `#d97706` (amber-600, meilleur contraste WCAG sur blanc) |
| Textes | `#eef0f4 / #8a909e / #545966` | `#111827 / #4b5563 / #9ca3af` |
| Bordures | `rgba(255,255,255,.07/.13)` | `rgba(0,0,0,.08/.15)` |
| Ombres | Pas d'ombres (dark masque) | Tokens `--shadow-sm/md/lg` (élévation douce) |
| Langue de l'interface | Anglais | Français (labels, messages, tooltips) |
| Responsive | Règle unique `@media (max-width:768px)` | Mobile-first : 3 points de rupture (mobile / tablette / bureau) |
| Sidebar mobile | `transform: translateX(-100%)` | Overlay avec `backdrop-filter: blur(2px)` + classe `mobile-open` |
| Sidebar tablette | Non défini | Réduite automatiquement (68px) entre 769px–1024px |
| Cibles tactiles | Non garanties | `min-height: 44px` sur tous les éléments interactifs |
| Chart.js couleurs | Fonds sombres dans les tooltips | Tooltips blancs avec bordures légères |
| Badges sémantiques | Couleurs display vives sur fond sombre | Couleurs texte saturées sur fond clair à 10% |

---

## 1. Philosophie de design

**Direction esthétique :** Minimalisme professionnel — clair, dense, orienté données. Chaque élément justifie sa présence. Pas de remplissage décoratif. L'interface fonctionne comme un terminal de trading professionnel : densité d'information élevée, espacement serré, contrastes clairs, l'ambre comme seul accent chaud sur une palette neutre.

**Principes fondamentaux :**
- **Clair en priorité.** Fond blanc/gris clair. Pas de mode sombre.
- **La donnée est la vedette** — typographie et espacement au service de la lisibilité avant tout.
- **Une seule couleur d'accent** (`--accent: #d97706`). Utilisée avec parcimonie et intention.
- **Ombres douces** pour la séparation et l'élévation (remplacent les bordures sur fond sombre).
- **Animations subtiles**, rapides (150–350ms), intentionnelles — jamais décoratives.
- **Interface en français** — tous les labels, messages, placeholders, et validations.
- **Mobile d'abord** — chaque composant conçu pour mobile puis étendu au bureau.

---

## 2. Palette de couleurs

### Surfaces de base (du plus clair au plus foncé)
| Token | Valeur Hex | Usage |
|---|---|---|
| `--bg-base` | `#f3f4f6` | Fond de page |
| `--bg-surface` | `#ffffff` | Cartes, barre latérale, barre supérieure |
| `--bg-raised` | `#f9fafb` | Cartes imbriquées, menus déroulants, champs de saisie |
| `--bg-hover` | `#f1f5f9` | État de survol des lignes / éléments |

### Bordures
| Token | Valeur | Usage |
|---|---|---|
| `--border` | `rgba(0,0,0,.08)` | Séparateurs par défaut, bords de cartes |
| `--border-strong` | `rgba(0,0,0,.15)` | Champs focalisés, cartes survolées |

### Accent (Ambre)
| Token | Valeur | Usage |
|---|---|---|
| `--accent` | `#d97706` | CTA principal, nav active, icônes, badges |
| `--accent-dim` | `rgba(217,119,6,.10)` | Fonds accent, mise en évidence |
| `--accent-glow` | `rgba(217,119,6,.25)` | Anneau de focus, effets de lueur |

### Textes
| Token | Hex | Usage |
|---|---|---|
| `--text-primary` | `#111827` | Titres, valeurs, contenu principal |
| `--text-secondary` | `#4b5563` | Corps de texte, cellules de tableau, descriptions |
| `--text-muted` | `#9ca3af` | Labels, horodatages, placeholders |

### Ombres (nouveauté v2)
| Token | Valeur | Usage |
|---|---|---|
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.04)` | Cartes au repos, barre supérieure |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04)` | Survol de cartes, éléments soulevés |
| `--shadow-lg` | `0 10px 30px rgba(0,0,0,.10), 0 4px 8px rgba(0,0,0,.05)` | Menus déroulants, toasts, modales |

### Couleurs sémantiques
| Rôle | Hex texte | Fond alpha | Usage |
|---|---|---|---|
| Succès | `#16a34a` | `rgba(22,163,74,.10)` | Deltas positifs, finalisé, badges |
| Danger | `#dc2626` | `rgba(220,38,38,.10)` | Erreurs, retards, alertes élevées |
| Avertissement | `#d97706` | `rgba(217,119,6,.12)` | Prudence, en attente |
| Info | `#0284c7` | `rgba(2,132,199,.10)` | Info neutre, en transit |

> **Note v2 :** Les couleurs display vives de v1 (`#4ade80`, `#f87171`, etc.) ne sont **plus utilisées** pour le texte des badges — elles manquent de contraste sur fond blanc. Utilisez les valeurs de la colonne "Hex texte" ci-dessus.

### Séquence de couleurs pour les graphiques
Utilisées dans l'ordre pour les graphiques multi-séries, donuts et barres :
```
#d97706  (amber — accent principal)
#0284c7  (bleu ciel)
#16a34a  (vert)
#7c3aed  (violet)
#ea580c  (orange)
#0d9488  (sarcelle)
#db2777  (rose)
#4f46e5  (indigo)
#dc2626  (rouge)
```

### Variantes de fond pour icônes (classes utilitaires)
```css
.ic-amber  → background: rgba(217,119,6,.12);  color: #d97706;
.ic-blue   → background: rgba(2,132,199,.10);  color: #0284c7;
.ic-green  → background: rgba(22,163,74,.10);  color: #16a34a;
.ic-purple → background: rgba(124,58,237,.10); color: #7c3aed;
.ic-red    → background: rgba(220,38,38,.10);  color: #dc2626;
.ic-teal   → background: rgba(13,148,136,.10); color: #0d9488;
.ic-orange → background: rgba(234,88,12,.10);  color: #ea580c;
.ic-pink   → background: rgba(219,39,119,.10); color: #db2777;
.ic-indigo → background: rgba(79,70,229,.10);  color: #4f46e5;
```

---

## 3. Typographie

### Pile de polices
| Rôle | Famille | Graisses | Usage |
|---|---|---|---|
| Affichage / Interface | **Syne** (Google Fonts) | 400, 600, 700, 800 | Tous les titres, labels de navigation, valeurs métriques, titres de cartes, boutons |
| Corps / Données | **DM Sans** (Google Fonts) | 300, 400, 500 | Corps de texte, cellules de tableau, descriptions, champs de formulaire |

```html
<!-- Requis dans le <head> -->
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap" rel="stylesheet">
```

### Échelle typographique
| Élément | Police | Taille | Graisse | Espacement lettres | Couleur |
|---|---|---|---|---|---|
| Titre de page (H1) | Syne | `clamp(18px,4vw,24px)` | 800 | `-0.025em` | `--text-primary` |
| Titre de carte / section | Syne | 14–15px | 700 | `-0.01em` | `--text-primary` |
| Valeur métrique (grande) | Syne | 26px | 800 | aucun | `--text-primary` |
| Valeur métrique (petite) | Syne | 20px | 800 | aucun | `--text-primary` |
| Label de lien nav | DM Sans | 13.5px | 400 | aucun | `--text-secondary` |
| Corps / cellule tableau | DM Sans | 13–14px | 400 | aucun | `--text-secondary` |
| Mention de section | DM Sans | 10.5px | 600 | `0.1em` | `--text-muted` |
| En-tête de tableau | DM Sans | 10.5px | 600 | `0.07em` | `--text-muted` |
| Badge / étiquette | DM Sans | 11px | 500 | `0.02em` | variable |
| Légende / horodatage | DM Sans | 11–12px | 400 | aucun | `--text-muted` |

> **Note v2 :** Utiliser `clamp()` sur les titres de pages pour une adaptation fluide mobile→bureau.

---

## 4. Espacement et mise en page

### Variables CSS
```css
--sidebar-w:    240px;   /* étendue */
--sidebar-w-sm: 68px;    /* réduite */
--topbar-h:     60px;
```

### Rayons de bordure
| Token | Valeur | Usage |
|---|---|---|
| `--radius-sm` | `6px` | Boutons, champs, boîtes d'icônes, liens de nav |
| `--radius-md` | `10px` | Menus déroulants, toasts, éléments de pipeline |
| `--radius-lg` | `16px` | Cartes, panneaux graphiques, conteneurs principaux |

### Rembourrage de page (mobile-first)
| Contexte | Valeur |
|---|---|
| Bureau (≥ 1025px) | `28px 32px` |
| Tablette (769px–1024px) | `20px 24px` |
| Mobile (≤ 768px) | `16px` |
| Très petit mobile (≤ 480px) | `12px` |
| Rembourrage interne des cartes | `18–22px 20px` |
| Rembourrage des cellules de tableau | `13px 14px` |

### Système de grille
- Utiliser le système `row / col-*` de Bootstrap 5 pour les grilles de colonnes responsives.
- Grilles de modules personnalisées : CSS `grid` avec `auto-fill, minmax(180px, 1fr)`.
- Partages en deux colonnes : `col-xl-8 / col-xl-4` ou `col-xl-5 / col-xl-7`.
- Espacement entre cartes : `12–20px` (`gap: 12px` ou `g-3` / `g-4` en Bootstrap).
- **Mobile :** les grilles de modules passent à `repeat(2, 1fr)` sous 768px, `1fr` sous 400px.

---

## 5. Bibliothèque de composants

### Cartes
```css
/* Carte standard */
background: var(--bg-surface);
border: 1px solid var(--border);
border-radius: var(--radius-lg);
box-shadow: var(--shadow-sm);

/* Au survol : */
border-color: var(--border-strong);
transform: translateY(-1px);
box-shadow: var(--shadow-md);

/* Ligne d'accent en haut au survol */
::after { height: 2px; background: var(--accent); top: 0; opacity: 0→1 }
```

### Cartes métriques
- Boîte d'icône : carré 38–44px, arrondi `var(--radius-sm)`, utilise la variante de couleur `.ic-*`.
- Label en mention : 10.5–11px, majuscules, `--text-muted`.
- Valeur : Syne 800, 20–26px.
- Badge delta : étiquette avec icône flèche haut/bas, fond sémantique à **10%** d'opacité.

### Étiquettes / Badges
```css
/* Base */
display: inline-flex; align-items: center; gap: 4px;
padding: 3px 9px; border-radius: 20px;
font-size: 11px; font-weight: 500;

/* Variantes v2 (thème clair) */
.pill-success → bg rgba(22,163,74,.10),   color #16a34a
.pill-danger  → bg rgba(220,38,38,.10),   color #dc2626
.pill-warning → bg rgba(217,119,6,.12),   color #d97706
.pill-info    → bg rgba(2,132,199,.10),   color #0284c7
.pill-neutral → bg var(--bg-hover),       color var(--text-secondary)
```

### Tableaux
```css
/* Fond de l'en-tête */
background: var(--bg-raised);   /* ← nouveauté v2 */
font-size: 10.5px; font-weight: 600; letter-spacing: 0.07em;
text-transform: uppercase; color: var(--text-muted);
border-bottom: 1px solid var(--border);

/* Cellules de données */
font-size: 13px; color: var(--text-secondary);
padding: 13px 14px;
border-bottom: 1px solid var(--border);

/* Survol de ligne */
background: var(--bg-hover);

/* Défilement mobile */
.table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
```

### Boutons
```css
/* Primaire (accent) */
background: var(--accent); color: #ffffff;   /* ← blanc sur fond clair, pas #0d0f12 */
font-family: Syne; font-weight: 700; font-size: 14px;
border-radius: var(--radius-md); padding: 11px 20px;
min-height: 44px;   /* cible tactile */
transition: opacity .18s, transform .12s;
:hover { opacity: .9 }
:active { transform: scale(.99) }

/* Fantôme / contour */
background: transparent;
border: 1px solid var(--border);
color: var(--text-secondary);
min-height: 44px;
:hover { background: var(--bg-hover); border-color: var(--border-strong); color: var(--text-primary); }

/* Danger */
background: rgba(220,38,38,.10);
border: 1px solid rgba(220,38,38,.25);
color: #dc2626;
min-height: 44px;
```

### Champs de formulaire
```css
background: var(--bg-surface);
border: 1px solid var(--border);
border-radius: var(--radius-md);
color: var(--text-primary);
font-family: 'DM Sans', sans-serif; font-size: 14px;
padding: 11px 13px 11px 40px;  /* 40px gauche = espace pour l'icône */
min-height: 44px;               /* cible tactile */

:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(217,119,6,.15);
  outline: none;
}
::placeholder { color: var(--text-muted); }
```
- Icône gauche : `position: absolute; left: 13px;` — Bootstrap Icon, couleur `--text-muted`, transition vers `--accent` au focus.
- Labels : 12px, graisse 500, `--text-secondary`, `letter-spacing: .03em`, affichage bloc au-dessus du champ.
- Messages d'erreur : 12px, `var(--danger)` = `#dc2626`, ligne flex avec icône `bi-x-circle`.

### Navigation (barre latérale)

**Comportement selon la taille d'écran :**

| Contexte | Largeur | Comportement |
|---|---|---|
| Bureau (≥ 1025px) | 240px étendue / 68px réduite | Basculement via bouton, état dans `localStorage` |
| Tablette (769px–1024px) | 68px par défaut | Automatiquement réduite, sans overlay |
| Mobile (≤ 768px) | Hors écran (`translateX(-100%)`) | Ouverture via overlay `.sidebar-backdrop` |

```css
/* Overlay mobile */
.sidebar-backdrop {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,.35);
  backdrop-filter: blur(2px);
  z-index: 199;
}
.sidebar-backdrop.visible { display: block; }

/* Barre latérale mobile ouverte */
.sidebar.mobile-open { transform: translateX(0); box-shadow: var(--shadow-lg); }
```

**Logique JS pour la bascule :**
```js
const isMobile = () => window.innerWidth <= 768;
// Mobile → basculer .mobile-open + .visible sur l'overlay
// Bureau/tablette → basculer .collapsed + sauvegarder dans localStorage
```

- Lien actif : `color: var(--accent)`, `background: var(--accent-dim)`, barre gauche ambre 3px via `::before`.
- État réduit : `.nav-link-label`, `.brand-text`, `.user-info` tous `opacity: 0`.
- Labels de section : 9.5px, majuscules, `--text-muted`, masqués par opacité en état réduit.
- **Tous les éléments de nav** : `min-height: 44px` pour cibles tactiles.

### Alertes / Toasts
```css
background: var(--bg-surface);          /* ← blanc en v2, pas bg-raised sombre */
border: 1px solid var(--border-strong);
border-radius: var(--radius-md);
padding: 12px 16px;
box-shadow: var(--shadow-lg);           /* ← shadow token, pas valeur codée en dur */
/* Bordure gauche d'accentuation par type : */
border-left: 3px solid var(--success / --danger / --warning / --info);
```
Fermeture automatique après 4000ms avec transition opacité + translateX.

---

## 6. Iconographie

**Bibliothèque :** Bootstrap Icons 1.11.3
**CDN :** `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css`
**Usage :** `<i class="bi bi-{nom-icone}"></i>`

### Conventions de taille
| Contexte | Taille |
|---|---|
| Nav barre latérale | `16px` |
| Boîte d'icône de carte métrique | `17–20px` |
| Préfixe de champ de formulaire | `15px` |
| Boutons d'action barre supérieure | `15px` |
| Icônes d'action de tableau | `14px` |
| Texte de corps en ligne | `13–14px` |

### Correspondances d'icônes standard
| Module / Concept | Classe d'icône |
|---|---|
| Tableau de bord | `bi-speedometer2` |
| Inventaire / Véhicules | `bi-boxes` |
| Achats / Imports | `bi-truck` |
| Ventes | `bi-receipt` |
| Clients | `bi-people` |
| Fournisseurs | `bi-building` |
| Paiements | `bi-credit-card` |
| Commissions | `bi-percent` |
| Rapports | `bi-bar-chart-line` |
| Paramètres | `bi-sliders` |
| Alerte / Notification | `bi-bell` |
| Export | `bi-file-earmark-bar-graph` |
| Rôle Gestionnaire | `bi-shield-check` |
| Rôle Trader | `bi-person-badge` |
| Rôle Finance | `bi-calculator` |
| Rôle Auditeur | `bi-eye` |
| Succès / Validé | `bi-check-circle` |
| Erreur | `bi-exclamation-circle` |
| Avertissement | `bi-exclamation-triangle` |
| Info | `bi-info-circle` |
| Ajouter / Créer | `bi-plus-lg` |
| Modifier | `bi-pencil` |
| Supprimer | `bi-trash` |
| Rechercher | `bi-search` |
| Filtrer | `bi-funnel` |
| Télécharger / Exporter | `bi-download` |
| Imprimer | `bi-printer` |
| Lien externe | `bi-arrow-up-right` |
| Retour / Précédent | `bi-arrow-left` |
| Chevron droit | `bi-chevron-right` |
| Calendrier | `bi-calendar3` |
| Devise / Argent | `bi-currency-dollar` |
| Marge / Profit | `bi-piggy-bank` |
| Tendance revenus | `bi-graph-up-arrow` |
| Impayés | `bi-hourglass-split` |
| Véhicule / Voiture | `bi-car-front-fill` |
| Verrouillage / Mot de passe | `bi-lock` |
| Utilisateur / Connexion | `bi-person` |
| Déconnexion | `bi-box-arrow-left` |
| Connexion | `bi-box-arrow-in-right` |
| Basculer barre latérale | `bi-layout-sidebar` |
| Photo | `bi-image` |
| Joindre / Téléverser | `bi-paperclip` |
| Téléphone | `bi-telephone` |
| E-mail | `bi-envelope` |
| Localisation | `bi-geo-alt` |
| Étiquette | `bi-tag` |

---

## 7. Visualisation de données (Chart.js 4)

**Bibliothèque :** Chart.js 4.4.3
**CDN :** `https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js`

### Valeurs par défaut globales (définies une fois dans base.html)
```js
/* v2 — thème clair */
Chart.defaults.color = '#6b7280';
Chart.defaults.borderColor = 'rgba(0,0,0,0.07)';
Chart.defaults.font.family = "'DM Sans', sans-serif";
```

### Configuration standard des tooltips (v2)
```js
tooltip: {
  backgroundColor: '#ffffff',
  borderColor: 'rgba(0,0,0,.12)',
  borderWidth: 1,
  titleColor: '#111827',
  bodyColor: '#4b5563',
  padding: 10,
  cornerRadius: 8,
}
```

### Lignes de grille (v2)
```js
grid: {
  color: 'rgba(0,0,0,0.05)',
  drawBorder: false
}
ticks: { color: '#9ca3af', font: { size: 10.5 } }
```

### Types de graphiques et paramètres
| Type | Cas d'usage | Configuration clé |
|---|---|---|
| Courbe en aires | Tendances de revenus dans le temps | `fill: true`, dégradé `rgba(217,119,6,.20)→transparent`, `tension: 0.45`, `borderColor: #d97706`, `pointBorderColor: '#ffffff'` |
| Barres horizontales | Performance traders / classements | `indexAxis: 'y'`, `borderRadius: 6`, `borderSkipped: false`, couleurs de la palette avec `+'22'` pour fond transparent |
| Donut | Distribution / répartition | `cutout: '68%'`, `borderColor: '#ffffff'`, `borderWidth: 2`, légende en bas |
| Barres verticales | Comparaisons mensuelles | `borderRadius: 6`, `borderSkipped: false` |

### Recette pour le dégradé de graphique en aires (v2)
```js
const gradient = ctx.createLinearGradient(0, 0, 0, chartHeight);
gradient.addColorStop(0, 'rgba(217,119,6,0.20)');  /* ← accent v2 */
gradient.addColorStop(1, 'rgba(217,119,6,0)');
// puis : backgroundColor: gradient
```

### Astuce pour les couleurs de barres (v2)
```js
// Fond semi-transparent + bordure solide pour look propre sur fond blanc
backgroundColor: COLORS.slice(0, n).map(c => c + '22'),
borderColor: COLORS.slice(0, n),
borderWidth: 1.5,
```

---

## 8. Conventions d'animation

| Modèle | Valeurs |
|---|---|
| Transition par défaut | `0.18s ease` |
| Survol de carte — élévation | `transform: translateY(-2px)` |
| Entrée de page | `fadeIn` — `opacity 0→1`, `translateY(10px → 0)`, `0.35s ease` |
| Entrée de liste décalée | `animation-delay: nth-child × 40ms` (plafonner à ~400ms) |
| Glissement du toast | `translateX(20px → 0)`, `0.2s ease` |
| Fermeture du toast | `opacity → 0`, `translateX(20px)`, `0.3s ease` |
| Réduction barre latérale | transition `width` `0.18s ease` |
| Ouverture mobile | transition `transform` `0.18s ease` |

```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0); }
}
```

---

## 9. Architecture des templates

### Chaîne d'héritage
```
base.html
├── registration/login.html   (autonome — n'étend pas base)
├── core/index.html           (étend base)
├── core/dashboard.html       (étend base)
├── {app}/list.html           (étend base)
├── {app}/detail.html         (étend base)
├── {app}/form.html           (étend base)
└── {app}/...
```

### Blocs disponibles dans base.html
| Bloc | Rôle |
|---|---|
| `{% block title %}` | Contenu de la balise `<title>` (sans suffixe) |
| `{% block nav_{nom} %}` | Injecter `active` pour mettre en évidence le lien de la barre latérale |
| `{% block page_title %}` | Texte principal du fil d'Ariane dans la barre supérieure |
| `{% block page_sub_text %}` | Sous-titre de la barre supérieure (date, compte, etc.) |
| `{% block extra_css %}` | `<style>` spécifique à la page à l'intérieur de la balise `<style>` de base |
| `{% block content %}` | Corps principal de la page à l'intérieur de `.page-body` |
| `{% block extra_js %}` | Scripts spécifiques à la page avant `</body>` |

### Noms des blocs de navigation disponibles
`nav_index`, `nav_dashboard`, `nav_inventory`, `nav_purchases`, `nav_sales`, `nav_customers`, `nav_suppliers`, `nav_payments`, `nav_commissions`, `nav_reports`, `nav_settings`

### Variables de contexte toujours disponibles (depuis le processeur de contexte)
- `request.user` — utilisateur Auth complet
- `request.user.userprofile` — UserProfile avec `.role`, `.is_manager`, `.is_trader`, `.is_finance`, `.is_auditor`
- `app_name` — `"HB China Cars"`

---

## 10. Points de rupture responsives (Mobile-First)

```css
/* ── Mobile : style de base — aucun media query ── */

/* ── Tablette (769px–1024px) ── */
@media (min-width: 769px) and (max-width: 1024px) { ... }

/* ── Bureau (≥ 1025px) ── */
@media (min-width: 1025px) { ... }

/* ── Petits mobiles (≤ 480px) ── */
@media (max-width: 480px) { ... }
```

### Comportements responsifs standard
| Composant | Mobile (≤ 768px) | Tablette (769–1024px) | Bureau (≥ 1025px) |
|---|---|---|---|
| Barre latérale | Overlay hors écran | Réduite 68px, sans labels | 240px ou 68px selon préférence |
| Rembourrage de page | `16px` | `20px 24px` | `28px 32px` |
| Grille de modules | `repeat(2, 1fr)` | `repeat(3, 1fr)` | `repeat(auto-fill, minmax(180px,1fr))` |
| Grille pipeline | `repeat(2, 1fr)` | `repeat(2, 1fr)` | `repeat(4, 1fr)` |
| Division deux colonnes | `1fr` (empilé) | `1fr` (empilé) | `col-xl-8 / col-xl-4` |
| Tableaux | Défilement horizontal (`overflow-x: auto`) | Défilement si nécessaire | Pleine largeur |
| Graphiques | Hauteur réduite `160–180px` | `200px` | `200–240px` |
| Topbar | `padding: 0 16px` | `padding: 0 20px` | `padding: 0 24px` |

### Cibles tactiles
Tous les éléments interactifs doivent avoir `min-height: 44px` et `min-width: 44px` sur mobile :
```css
.nav-link, .user-card, .topbar-btn, .topbar-toggle,
button, .btn-primary, input, select, textarea { min-height: 44px; }
```

---

## 11. Extraits HTML réutilisables

### Mention de section
```html
<div class="section-eyebrow">Titre de section</div>
<!-- CSS : 10.5px, majuscules, letter-spacing .1em, --text-muted, font-weight 600 -->
```

### En-tête de section avec lien
```html
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px;">
  <span style="font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--text-muted);font-weight:600;">Section</span>
  <a href="/chemin/" class="section-link">
    Tout voir <i class="bi bi-arrow-right"></i>
  </a>
</div>
```

### Coque de carte métrique
```html
<div class="metric-card">
  <div class="metric-icon ic-{couleur}"><i class="bi bi-{icone}"></i></div>
  <div class="metric-label">ÉTIQUETTE</div>
  <div class="metric-value">VALEUR</div>
  <span class="metric-delta up|down|neutral">
    <i class="bi bi-arrow-up-right|arrow-down-right|dash"></i> texte
  </span>
</div>
```

### État vide
```html
<div style="text-align:center;padding:48px 20px;color:var(--text-muted);">
  <i class="bi bi-{icone}" style="font-size:32px;display:block;margin-bottom:12px;color:var(--border-strong);"></i>
  <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:var(--text-secondary);margin-bottom:6px;">Aucun élément trouvé</div>
  <div style="font-size:13px;">Message descriptif ici.</div>
  <a href="/creer/" class="btn-primary" style="margin-top:16px;display:inline-flex;align-items:center;gap:8px;min-height:44px;">
    <i class="bi bi-plus-lg"></i> Créer le premier
  </a>
</div>
```

### Zone de danger / Confirmation
```html
<div style="background:rgba(220,38,38,.07);border:1px solid rgba(220,38,38,.20);border-radius:var(--radius-md);padding:16px 18px;">
  <div style="font-family:'Syne',sans-serif;font-weight:700;color:#dc2626;margin-bottom:4px;">
    <i class="bi bi-exclamation-triangle me-1"></i> Zone dangereuse
  </div>
  <p style="font-size:13px;color:var(--text-secondary);margin:0 0 12px;">Message d'avertissement.</p>
  <button class="btn-danger">Action destructrice</button>
</div>
```

### Bannière de rôle
```html
<div class="role-banner">
  <div class="role-banner-icon">
    <i class="bi bi-shield-check"></i>  {# Adapter selon le rôle #}
  </div>
  <div class="role-banner-text">
    Connecté en tant que <strong>{{ request.user.userprofile.get_role_display }}</strong>.
    {# Message contextuel selon les permissions #}
  </div>
</div>
```

### Carte de module (grille d'accueil)
```html
<a href="{% url 'app:view' %}" class="module-card">
  <div class="module-card-icon ic-{couleur}"><i class="bi bi-{icone}"></i></div>
  <div class="module-card-title">Titre du module</div>
  <div class="module-card-desc">Description courte</div>
  <i class="bi bi-arrow-up-right module-card-arrow"></i>
</a>
```

### Carte de graphique
```html
<div class="chart-card">
  <div class="chart-card-head">
    <div>
      <div class="chart-card-title">Titre du graphique</div>
      <div class="chart-card-subtitle">Description ou période</div>
    </div>
    {# Légende optionnelle ou badge ici #}
  </div>
  <div class="chart-card-body">
    <div class="chart-wrap" style="height:220px;">
      <canvas id="monGraphique"></canvas>
    </div>
  </div>
</div>
```

### Lien de section
```html
<a href="/chemin/" class="section-link">
  Tout voir <i class="bi bi-arrow-right"></i>
</a>
```
```css
/* CSS de section-link */
.section-link {
  font-size: 12px; color: var(--accent);
  display: inline-flex; align-items: center; gap: 4px;
  font-weight: 500; transition: gap .18s, opacity .18s;
}
.section-link:hover { gap: 7px; opacity: .8; }
```

---

## 12. Règles spécifiques à Django

- **Ne jamais** utiliser des filtres Django inexistants : pas de `|split`, pas de `|math`, pas de `|add` avec des flottants.
- Comparaisons heure/date → toujours en JavaScript (`new Date().getHours()`), pas dans les balises de template Django.
- Séquences de délai d'animation → utiliser du CSS `:nth-child(n)` explicite, jamais une boucle `{% for %}` pour générer des chaînes CSS.
- Toutes les valeurs monétaires : formater avec `|floatformat:0` et ajouter `DA` en texte.
- Pourcentages : `|floatformat:1` avec `%`.
- Dates : `|date:"j M Y"` pour la forme courte, `|date:"l, N j, Y"` pour la forme longue.
- `{% csrf_token %}` dans chaque formulaire POST, sans exception.
- Utiliser `{% url 'nom_app:nom_vue' %}` pour tous les liens internes.
- Protéger tous les accès à `userprofile` avec `{% if request.user.userprofile %}`.
- La salutation (Bonjour / Bon après-midi / Bonsoir) doit toujours se faire en JS côté client.
- Pluriels : utiliser le filtre Django `{{ valeur|pluralize }}` pour `(s)` sur les mots français simples.

---

## 13. Lexique français de l'interface (référence de traduction)

| Anglais | Français |
|---|---|
| Dashboard | Tableau de bord |
| Home | Accueil |
| Inventory | Inventaire |
| Purchases | Achats |
| Sales | Ventes |
| Customers | Clients |
| Suppliers | Fournisseurs |
| Payments | Paiements |
| Commissions | Commissions |
| Reports | Rapports |
| Settings | Paramètres |
| Overview | Vue d'ensemble |
| Operations | Opérations |
| Finance | Finance |
| System | Système |
| Sign Out / Logout | Déconnexion |
| Sign In / Login | Connexion |
| My Profile | Mon profil |
| Key Metrics | Indicateurs clés |
| Current Month | Mois en cours |
| Vehicle Pipeline | Pipeline des véhicules |
| Analytics | Analytiques |
| Recent Transactions | Transactions récentes |
| All Modules | Tous les modules |
| View all | Tout voir |
| No items found | Aucun élément trouvé |
| No active alerts | Aucune alerte active |
| Finalized | Finalisé |
| Draft | Brouillon |
| In Transit | En transit |
| At Customs | En douane |
| Available | Disponibles |
| Reserved | Réservés |
| Outstanding | Impayés |
| Overdue | En retard |
| No change | Aucun changement |
| Revenue | Chiffre d'affaires |
| Margin | Marge |
| Inventory Value | Valeur du stock |
| Monthly Revenue | Chiffre d'affaires mensuel |
| Monthly Margin | Marge mensuelle |
| Sales Count | Nombre de ventes |
| Trader Performance | Performance des traders |
| Sales Split | Répartition des ventes |
| Month Summary | Récapitulatif du mois |
| Revenue Trend | Tendance du chiffre d'affaires |
| Alerts | Alertes |
| Recent issues to review | Problèmes récents à examiner |
| Vehicle | Véhicule |
| Customer | Client |
| Trader | Trader |
| Date | Date |
| Sale Price | Prix de vente |
| Status | Statut |
| Your Commission | Votre commission |
| My Sales | Mes ventes |
| Good morning | Bonjour |
| Good afternoon | Bon après-midi |
| Good evening | Bonsoir |
| Welcome | Bienvenue |
| Quick overview of all modules | Aperçu rapide de tous les modules |
| Search | Rechercher |
| Filter | Filtrer |
| Create | Créer |
| Edit | Modifier |
| Delete | Supprimer |
| Save | Enregistrer |
| Cancel | Annuler |
| Confirm | Confirmer |
| Back | Retour |
| Export | Exporter |
| Print | Imprimer |
| Loading... | Chargement… |
| Error | Erreur |
| Success | Succès |
| Warning | Avertissement |
| Danger Zone | Zone dangereuse |
| Required field | Champ obligatoire |
| Invalid value | Valeur invalide |
| No VIN | Aucun NIV |
| Add / Create first | Créer le premier |
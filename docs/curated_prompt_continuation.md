# Invite de continuation — HB China Cars v2

> Prompt de référence pour générer les templates Django restants
> Thème clair · Interface française · Mobile-first responsive

---

## Prompt standard (à copier-coller)

```
En utilisant le fichier DESIGN_SYSTEM.md joint comme spécification visuelle stricte
(version 2.0 — thème clair, interface française, mobile-first), ainsi que base.html,
dashboard.html et index.html comme implémentations de référence, construis tous les
templates Django restants pour l'application `{NOM_APP}` — spécifiquement :
`{liste des templates}` — en étendant base.html, en utilisant Bootstrap 5 +
Bootstrap Icons 1.11.3 + Chart.js 4 selon les besoins, en respectant chaque token,
modèle de composant, règle d'espacement et contrainte Django définie dans le système
de design, sans aucun écart de couleur, typographie ou structure de composant.

Contraintes impératives :
1. Thème clair uniquement — aucune couleur de la palette v1 sombre (pas de #0d0f12,
   #13161b, #1b1f27, rgba(255,255,255,...) pour les bordures ou fonds).
2. Toute l'interface en français — labels, placeholders, messages de validation,
   états vides, confirmations.
3. Mobile-first — chaque composant fonctionne sur 320px puis s'étend. Cibles
   tactiles min 44px. Tableaux avec défilement horizontal. Grilles qui s'empilent.
4. Conserver intégralement la logique des templates Django ({% %}, {{ }}),
   les routes et les fonctionnalités existantes.
5. Chart.js : utiliser les valeurs par défaut et couleurs de la v2 (tooltips blancs,
   grilles rgba(0,0,0,0.05), palette de couleurs claire).
```

---

## Fichiers à joindre à chaque session

| Fichier                           | Pourquoi                                                                    |
| --------------------------------- | --------------------------------------------------------------------------- |
| `DESIGN_SYSTEM.md` (v2)           | La spécification — tokens v2, composants, règles responsive, lexique FR     |
| `base.html` (v2)                  | Le shell étendu — overlay mobile, thème clair, barre latérale responsive    |
| `dashboard.html` (v2)             | Référence la plus complète — graphiques, tableaux, métriques, alertes en FR |
| `index.html` (v2)                 | Référence grille de cartes + animations + modules en FR                     |
| `views.py` de l'app concernée     | Variables de contexte exactes disponibles dans les templates                |
| `models.py` de l'app concernée    | Noms de champs et relations pour les accès `{{ objet.champ }}`              |
| `urls.py` de l'app (ou `urls.md`) | Pour que les balises `{% url %}` soient correctes                           |

> **Important :** Joindre les fichiers v2 (`base.html`, `dashboard.html`, `index.html`)
> et non les originaux sombres v1. Les fichiers de référence v2 sont les sorties
> produites lors de la migration vers le thème clair.

---

## Stratégie de traitement par lot

Traiter **une application à la fois** pour une meilleure cohérence :

### Ordre recommandé

```
Lot 1 : inventory   → list.html, detail.html, form.html, alerts.html
Lot 2 : purchases   → list.html, detail.html, form.html
Lot 3 : sales       → list.html, detail.html, form.html
Lot 4 : customers   → list.html, detail.html, form.html
Lot 5 : suppliers   → list.html, detail.html, form.html
Lot 6 : payments    → list.html, detail.html
Lot 7 : commissions → list.html, detail.html, my_commission.html
Lot 8 : reports     → index.html (ou dashboard.html)
Lot 9 : settings    → index.html, user_preferences.html, exchange_rates.html
Lot 10: registration → login.html (template autonome, n'étend pas base)
```

### Remplacer dans le prompt :

- `{NOM_APP}` → ex. `inventory`
- `{liste des templates}` → ex. `list.html, detail.html, form.html, alerts.html`

---

## Rappels de cohérence v2 par type de template

### Templates de liste (`list.html`)

- En-tête de page : titre `section-eyebrow` + bouton "Créer" en haut à droite
- Barre d'outils : champ de recherche avec icône `bi-search` + filtres déroulants si nécessaire
- Compteur de résultats : `{{ count }} résultat{{ count|pluralize }}` en `--text-muted`
- Tableau avec `table-card` + `table-scroll` wrapper pour mobile
- En-têtes de colonnes : `background: var(--bg-raised)` (important v2)
- État vide avec snippet "Aucun élément trouvé" + bouton de création
- Pagination Bootstrap avec styles v2 si nécessaire

### Templates de détail (`detail.html`)

- Bouton retour en haut : `<a href="..." class="section-link"><i class="bi bi-arrow-left me-1"></i> Retour</a>`
- Panneau principal : `chart-card` pour les données clés
- Données secondaires : disposition en deux colonnes `col-xl-8 / col-xl-4`
- Historique / activité : tableau avec `table-card`
- Actions (modifier/supprimer) : en haut à droite dans la topbar-like action row
- Zone de danger pour la suppression (uniquement gestionnaire)

### Templates de formulaire (`form.html`)

- Formulaire contenu dans une `chart-card` centrée `col-xl-8 mx-auto`
- Chaque champ : label au-dessus + icône à gauche + messages d'erreur en dessous
- Bouton de soumission : pleine largeur en mobile, `auto` en bureau
- `{% csrf_token %}` sans exception
- Messages d'erreur non-champ : en haut du formulaire avec style `pill-danger`

### Templates de connexion (`login.html`)

- Template autonome — **ne pas** étendre `base.html`
- Centré verticalement et horizontalement sur `--bg-base` clair
- Card connexion : max-width 400px, `box-shadow: var(--shadow-lg)`
- Logo + titre de marque en haut de la card
- Pas de barre latérale ni de barre supérieure

---

## Checklist de validation v2 (à vérifier pour chaque template livré)

### Thème clair

- [ ] Aucune couleur hexadécimale sombre codée en dur (`#0d0f12`, `#13161b`, `#1b1f27`, `#21262f`)
- [ ] Aucune couleur de bordure blanche transparente (`rgba(255,255,255,...)`)
- [ ] Les badges/étiquettes utilisent les couleurs sémantiques v2 (ex. `#16a34a` pas `#4ade80`)
- [ ] Les ombres utilisent les tokens `var(--shadow-sm/md/lg)` pas des valeurs codées en dur
- [ ] Les tooltips Chart.js ont `backgroundColor: '#ffffff'`

### Interface française

- [ ] Tous les labels de colonne de tableau en français
- [ ] Tous les états vides en français
- [ ] Tous les textes de boutons en français
- [ ] Tous les messages de validation/erreur en français
- [ ] Les placeholders de champs en français
- [ ] Les en-têtes de section (`section-eyebrow`) en français

### Responsive mobile

- [ ] Pas de largeurs fixes qui dépassent `100vw` sur mobile
- [ ] Les tableaux ont `.table-scroll` avec `overflow-x: auto`
- [ ] Tous les boutons ont `min-height: 44px`
- [ ] Tous les champs de formulaire ont `min-height: 44px`
- [ ] Les grilles multi-colonnes s'empilent sur mobile
- [ ] Les graphiques Chart.js ont `maintainAspectRatio: false` avec hauteur réduite sur mobile

### Django

- [ ] `{% extends "base.html" %}` en première ligne (sauf login)
- [ ] `{% block nav_{nom} %}active{% endblock %}` défini
- [ ] `{% block page_title %}` et `{% block page_sub_text %}` remplis
- [ ] `{% csrf_token %}` présent dans tout formulaire POST
- [ ] Toutes les valeurs monétaires formatées avec `|floatformat:0` + `DA`
- [ ] `{% if request.user.userprofile %}` garde les accès au profil
- [ ] Les URLs utilisent `{% url 'app:vue' %}` pas des chemins codés en dur

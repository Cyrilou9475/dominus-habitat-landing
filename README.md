# Dominus Habitat — landing page ITE

Landing page statique pour l'isolation thermique par l'extérieur (ITE).
Un seul `index.html` (CSS et JS inline, sans framework ni build), plus les logos détourés.

## Structure

| Fichier | Rôle |
|---|---|
| `index.html` | La landing page |
| `mentions-legales.html`, `confidentialite.html` | Pages légales (squelettes à compléter) |
| `assets/logo-monogramme.png` | Monogramme DH, PNG transparent (6 Ko) — header, favicon |
| `assets/logo-dominus-habitat.png` | Logo complet, PNG transparent (20 Ko) — footer, Open Graph |
| `_headers` | En-têtes HTTP de sécurité et de cache (format Netlify / Cloudflare Pages) |
| `tools/build_headers.py` | Régénère `_headers` avec les empreintes CSP des blocs inline |
| `robots.txt`, `sitemap.xml` | SEO |

Aperçu local : `python3 -m http.server` puis http://localhost:8000.

## À remplacer avant mise en ligne

- [ ] **Téléphone** : `01 23 45 67 89` / `tel:+33123456789` est un faux numéro. Il apparaît dans le header, la FAQ, le CTA final, le footer, le CTA mobile et le JSON-LD (`telephone`).
- [ ] **Envoi du formulaire** : voir le `TODO` dans le script de `index.html` (fonction `submit`). Aujourd'hui, la page affiche la confirmation sans rien envoyer. À prévoir côté serveur : revalidation des champs, anti-spam (le honeypot `website` est déjà en place, à compléter par du rate limiting ou Turnstile/hCaptcha), HTTPS, aucune clé API dans le HTML. Ajouter le domaine de l'endpoint dans `connect-src` (`tools/build_headers.py`).
- [ ] **Avis clients** : les 3 témoignages sont fictifs. Les remplacer par de vrais avis (avec accord écrit) ou un widget d'avis vérifiés. Publier de faux avis est une pratique commerciale trompeuse.
- [ ] **Photos avant / après** : les deux illustrations SVG du comparateur sont des placeholders. Les remplacer par deux photos WebP au même cadrage (1200×900), avec `width`/`height`, `loading="lazy"` et un `alt` descriptif (exemple en commentaire dans le code).
- [ ] **Liens légaux** : compléter tous les `[à compléter]` de `mentions-legales.html` (raison sociale, SIRET, adresse, hébergeur, directeur de publication, assureur décennal) et de `confidentialite.html` (responsable, sous-traitants, durée de conservation des leads, contact RGPD).
- [ ] **Chiffres clés** (section « Pourquoi isoler maintenant ») : vérifier et sourcer précisément avant publication.
  - `+44 %` : cumul des hausses du TRVE électricité de février 2022 à février 2024 (≈ +4 %, +15 %, +10 %, +10 %), source CRE. À confirmer.
  - `20-25 %` des déperditions par les murs : ordre de grandeur ADEME.
  - `8 sur 10` Français préoccupés par leur facture : **chiffre à remplacer par un sondage précis et daté**, ou à retirer.
- [ ] **Domaine** : `https://www.dominus-habitat.fr/` est supposé. Le corriger dans `canonical`, Open Graph, JSON-LD, `sitemap.xml`, `robots.txt` et les pages légales.
- [ ] **Zone desservie** : `areaServed` du JSON-LD vaut `Île-de-France` par défaut.
- [ ] **Délai de rappel** : l'écran de confirmation promet un appel « sous 48 h ouvrées », à ajuster.
- [ ] **Image Open Graph** : idéalement une image dédiée 1200×630 (photo de façade + logo) au lieu du logo.

## Choix de design

- Palette : marine `#164174` / `#0f2d52` / `#0a1f3a`, or `#ecb855` / `#c9962f`, ivoire `#f7f4ee`. Tokens sur `:root`.
- Contraste : `#c9962f` ne fait que 2,7:1 sur blanc, il est donc réservé aux éléments décoratifs. Les textes or sur fond clair utilisent `--gold-text` (`#8a6516`, 4,8:1 sur ivoire). L'or `#ecb855` sur marine fait 5,7:1.
- Typo : Cormorant Garamond 600 (titres) et Jost 400/500/600 (texte), 4 graisses au total, `display=swap`.
- Signature : la diagonale du toit du logo, avec un liseré or, entre le hero et la suite, puis avant le CTA final. C'est le seul effet graphique ; le reste reste sobre.
- Aucune animation décorative. `prefers-reduced-motion` désactive le défilement fluide et la seule transition (CTA mobile).

## Sécurité et déploiement

- `_headers` fixe une CSP stricte sans `unsafe-inline` : les blocs `<style>` et `<script>` inline sont autorisés par empreinte SHA-256. **Après toute modification d'un bloc `<style>` ou `<script>`, relancer `python3 tools/build_headers.py`**, sinon le navigateur bloquera le style ou le script.
- `_headers` est lu tel quel par Netlify et Cloudflare Pages. Sur Vercel, reporter les en-têtes dans `vercel.json` ; sur OVH/Apache, dans un `.htaccess`. GitHub Pages ne permet pas de définir d'en-têtes HTTP.
- `/assets/*` est servi avec un cache d'un an (`immutable`) : quand un fichier change, changer aussi son nom (ex. `logo-dominus-habitat.v2.png`).
- Aucun script tiers, aucun cookie. Si vous ajoutez des analytics ou un pixel, les charger après consentement et ajouter un bandeau cookies.

## Vérifié

- Rendu à 360, 768 et 1440 px sans défilement horizontal ; parcours complet du formulaire (erreurs, étapes, confirmation, focus) ; comparateur au clavier ; aucune erreur console ni violation CSP (Chromium).
- Reste à faire avant mise en ligne : test sur mobile réel (Chrome et Safari) et audit Lighthouse sur l'URL de production.

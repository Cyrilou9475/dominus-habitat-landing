# Dominus Habitat — landing page ITE

Landing page statique pour l'isolation thermique par l'extérieur (ITE).
Un seul `index.html` (CSS et JS inline, sans framework ni build), plus les logos détourés.

## Structure

| Fichier | Rôle |
|---|---|
| `index.html` | La landing page |
| `mentions-legales.html`, `confidentialite.html` | Pages légales, même header/footer que la landing. **Générées** par `tools/build_legal.py` : modifier le script, pas les fichiers HTML |
| `assets/logo-monogramme.png` | Monogramme DH, PNG transparent (6 Ko) — header, favicon |
| `assets/logo-dominus-habitat.png` | Logo complet, PNG transparent (20 Ko) — footer, Open Graph |
| `_headers` | En-têtes HTTP de sécurité et de cache (format Netlify / Cloudflare Pages) |
| `tools/build_headers.py` | Régénère `_headers` avec les empreintes CSP des blocs inline |
| `tools/build_legal.py` | Régénère les pages légales à partir du header, du footer et des styles d'`index.html` |
| `chantiers/chantiers.json`, `chantiers/sources/<slug>/` | Données et photos d'origine de la rubrique « Nos chantiers » (voir `chantiers/README.md`) |
| `tools/build_chantiers.py` | **Génère** la rubrique : photos optimisées (`assets/chantiers/`), `nos-chantiers/`, fiches, pages de département, `lp/isolation-exterieure/`, section d'accueil, `sitemap.xml`. Modifier le script ou les données, pas les pages générées |
| `robots.txt`, `sitemap.xml` | SEO (`sitemap.xml` est généré par `tools/build_chantiers.py`) |

Aperçu local : `python3 -m http.server` puis http://localhost:8000.

## Rubrique « Nos chantiers »

Ajouter un chantier = une entrée dans `chantiers/chantiers.json` + ses photos dans `chantiers/sources/<slug>/`, puis :

```
python3 tools/build_chantiers.py && python3 tools/build_legal.py && python3 tools/build_headers.py
```

Rien n'est publié sans les trois étapes (avant, pendant, après), l'accord écrit du client et `publie: true`. Le script liste ce qui manque.
Maquette locale avec les chantiers non publiés : `python3 tools/build_chantiers.py --apercu /tmp/apercu` (ne jamais mettre en ligne).

Mesure et envoi des demandes : bloc `DH_CONFIG` dans le script `<!-- mesure:start -->` d'`index.html` (adresse de la source « Formulaire web » du CRM,
identifiants GA4 et Google Ads). Rien ne se déclenche avant le consentement (Consent Mode v2 refusé par défaut). Test A/B : `?v=b` sur la page publicitaire.

## À remplacer avant mise en ligne

- [ ] **Téléphone** : la landing n'affiche plus aucun numéro (contact par formulaire et contact@dominushabitat.com). Seul le téléphone des mentions légales reste `[À COMPLÉTER]`, dans `tools/build_legal.py`.
- [ ] **Pixel Meta** : remplacer `[PIXEL_ID]` dans le script de consentement d'`index.html`, puis lancer `python3 tools/build_legal.py && python3 tools/build_headers.py`. Tant que l'ID n'est pas renseigné, le pixel ne se charge pas. Dans le Gestionnaire d'événements Meta, laisser la « correspondance avancée automatique » désactivée : sinon le pixel lit les champs du formulaire (nom, téléphone), ce que la politique de confidentialité exclut.
- [ ] **Envoi du formulaire** : renseigner `DH_CONFIG.leadEndpoint` (adresse de la source « Formulaire web » du CRM Dominus) dans `index.html`, puis relancer les trois scripts. Tant qu'elle est vide, la page affiche la confirmation sans rien envoyer (message dans la console). Le CRM revalide, dédoublonne et limite le débit ; le honeypot `website` reste côté page.
- [ ] **Mesure** : `DH_CONFIG.ga4`, `DH_CONFIG.adsId`, `DH_CONFIG.adsLabel` ; `adsEnhanced` seulement après validation de la politique de confidentialité. API de conversions Meta : à brancher côté CRM (jeton Meta nécessaire).
- [ ] **Nos chantiers** : photos AVANT et PENDANT du chantier de Fourmies (59), accord écrit du client, caractéristiques connues (isolant, épaisseur, surface, durée) ; preuves de certification (RGE, Qualibat, décennale) pour activer le bloc de confiance (`CERTIFICATIONS` dans `tools/build_chantiers.py`). Désactiver le filigrane « Galaxy S26+ » de l'appareil photo pour les prochaines prises.
- [ ] **Avis clients** : les 3 témoignages sont fictifs. Les remplacer par de vrais avis (avec accord écrit) ou un widget d'avis vérifiés. Publier de faux avis est une pratique commerciale trompeuse.
- [x] **Photos avant / après** : les trois comparateurs utilisent de vraies photos (`assets/avant*.webp`, `assets/apres*.webp`). Pour changer une photo, lui donner un **nouveau nom** de fichier : GitHub Pages et les navigateurs gardent l'ancienne image en cache si le nom ne change pas.
- [ ] **Pages légales** : contenu renseigné (Dominus Consultancy FZCO). Reste le téléphone `[À COMPLÉTER]` des mentions légales, dans `tools/build_legal.py`.
- [ ] **Chiffres clés** (section « Pourquoi isoler maintenant ») : vérifier et sourcer précisément avant publication.
  - `+44 %` : cumul des hausses du TRVE électricité de février 2022 à février 2024 (≈ +4 %, +15 %, +10 %, +10 %), source CRE. À confirmer.
  - `20-25 %` des déperditions par les murs : ordre de grandeur ADEME.
  - `8 sur 10` Français préoccupés par leur facture : **chiffre à remplacer par un sondage précis et daté**, ou à retirer.
- [ ] **Photos des isolants** (`assets/isolant-pse.webp`, `assets/isolant-laine.webp`) : images générées par IA (Canva), conservées en basse résolution (200 px agrandis à 900 px). À remplacer par des photos nettes d'au moins 900×900 px, **sous de nouveaux noms** de fichier (cache) ; le cadrage se règle avec `object-position` dans `.insulant>img`.
- [ ] **Domaine** : `dominushabitat.com` (fichier `CNAME` pour GitHub Pages). DNS à configurer : 4 enregistrements A sur `@` vers `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`, et un CNAME `www` vers `cyrilou9475.github.io`, en « DNS only » sur Cloudflare. Puis cocher « Enforce HTTPS » dans Settings → Pages.
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

- Après toute modification du header, du footer ou du `<style>` d'`index.html` : `python3 tools/build_legal.py && python3 tools/build_headers.py`, pour que les pages légales restent identiques.
- `_headers` fixe une CSP stricte sans `unsafe-inline` : les blocs `<style>` et `<script>` inline sont autorisés par empreinte SHA-256. **Après toute modification d'un bloc `<style>` ou `<script>`, relancer `python3 tools/build_headers.py`**, sinon le navigateur bloquera le style ou le script.
- `_headers` est lu tel quel par Netlify et Cloudflare Pages. Sur Vercel, reporter les en-têtes dans `vercel.json` ; sur OVH/Apache, dans un `.htaccess`. GitHub Pages ne permet pas de définir d'en-têtes HTTP.
- `/assets/*` est servi avec un cache d'un an (`immutable`) : quand un fichier change, changer aussi son nom (ex. `logo-dominus-habitat.v2.png`).
- Cookies : seul le Pixel Meta est utilisé, et il n'est chargé qu'après « Accepter » dans le bandeau. Le bandeau est une modale centrée qui bloque la page jusqu'au choix (sauf sur les pages légales, qui restent lisibles). Le choix est gardé 13 mois dans `localStorage` (`dh-consent`). « Gérer mes cookies » (footer, politique de confidentialité) rouvre le bandeau ; un refus après acceptation révoque le pixel et efface les cookies `_fbp`/`_fbc`. Une demande d'étude envoyée déclenche l'événement `Lead`, uniquement avec consentement.
- Ne pas ajouter d'autre traceur sans mettre à jour le bandeau, la politique de confidentialité et la CSP (`tools/build_headers.py`).

## Vérifié

- Rendu à 360, 768 et 1440 px sans défilement horizontal ; parcours complet du formulaire (erreurs, étapes, confirmation, focus) ; comparateur au clavier ; aucune erreur console ni violation CSP (Chromium).
- Reste à faire avant mise en ligne : test sur mobile réel (Chrome et Safari) et audit Lighthouse sur l'URL de production.

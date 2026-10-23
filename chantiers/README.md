# Chantiers : données et photos

`chantiers.json` alimente la rubrique « Nos chantiers » (accueil, `/nos-chantiers/`, fiches, pages de département,
page publicitaire, sitemap). **Ajouter un chantier = ajouter une entrée ici et déposer ses photos, puis lancer :**

```
python3 tools/build_chantiers.py && python3 tools/build_legal.py && python3 tools/build_headers.py
```

## Une entrée

| Champ | Rôle |
|---|---|
| `reference` | Numéro du chantier (`001`, `002`…), repris dans l'adresse de la fiche |
| `slug` | Adresse de la fiche : `isolation-exterieure-[departement]-[code]-[commune]-[reference]` |
| `departement` | `{ "code": "59", "nom": "Nord" }` : seule localisation toujours affichée |
| `commune`, `afficher_commune` | La commune ne s'affiche que si `afficher_commune` vaut `true` (accord du client) |
| `type_logement`, `travaux`, `titre_court` | Texte des cartes. `travaux` : `ite` (seule valeur pour l'instant) |
| `resume` | Deux ou trois phrases en haut de la fiche |
| `caracteristiques` | Ne renseigner que ce qui est connu : un champ `null` n'est pas affiché |
| `apres_seul` | `true` pour un chantier photographié après travaux seulement : publié avec la mention « photos avant travaux non disponibles », 3 vues « après » (`vue` : Rue, Arrière, Détail) à la place des 3 étapes |
| `accord_client` | Accord écrit du client pour publier les photos (oui / non) |
| `publie` | Interrupteur de publication |
| `photos.avant` / `pendant` / `apres` | Listes de photos : `fichier` (dans `sources/<slug>/`), `alt` (texte alternatif unique), `flou` (zones à flouter `[x, y, largeur, hauteur]` en pixels de l'original : numéro de maison, plaque, visage, boîte aux lettres), `focal` (point d'intérêt `[x, y]` entre 0 et 1 pour le recadrage 4:3) |

## Règles appliquées par le script

- Un chantier n'est **publié** que s'il a au moins une photo à chacune des trois étapes, `accord_client: true` et `publie: true`.
  Sinon il est ignoré et listé dans le rapport du script (« ce qui manque »).
- Les photos sont recadrées au format 4:3, floutées aux zones indiquées, débarrassées de leurs métadonnées (EXIF, GPS),
  puis exportées en AVIF, WebP et JPEG en 480, 800 et 1200 px dans `assets/chantiers/<slug>/`.
- Une page de département (`/nos-chantiers/nord-59/`) n'est créée qu'à partir de **2 chantiers publiés** dans ce département.
- L'adresse exacte n'est jamais affichée.

## Aperçu local

`python3 tools/build_chantiers.py --apercu /tmp/apercu` copie le site dans ce dossier **en incluant les chantiers non publiés**
(bandeau « Aperçu : non publié », étapes manquantes signalées), pour relire la maquette. Ne jamais mettre ce dossier en ligne.

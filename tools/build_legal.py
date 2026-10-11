"""Génère mentions-legales.html et confidentialite.html avec le header, le footer
et les styles d'index.html.

À relancer après toute modification du header, du footer ou du <style> d'index.html,
ou du contenu légal ci-dessous :
    python3 tools/build_legal.py && python3 tools/build_headers.py
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://www.dominus-habitat.fr/"  # TODO : domaine définitif (identique à index.html)
EMAIL = '<a href="mailto:contact@dominushabitat.com">contact@dominushabitat.com</a>'
CNIL = '<a href="https://www.cnil.fr" rel="noopener noreferrer">www.cnil.fr</a>'
TODO = '<span class="todo">[À COMPLÉTER]</span>'

PAGES = {
    "mentions-legales": {
        "title": "Mentions légales",
        "description": "Mentions légales du site Dominus Habitat : éditeur, directeur de publication, contact et hébergeur.",
        "rows": [
            ("Raison sociale", "Dominus Consultancy FZCO"),
            ("Forme juridique", "Free Zone Company (FZCO)"),
            ("Numéro d’immatriculation", "57137"),
            ("Siège social", "IFZA Properties, Dubai Silicon Oasis, Dubai, Émirats Arabes Unis"),
            ("Directeur de publication", "Thomas Martin"),
            ("Email", EMAIL),
            ("Téléphone", TODO),
            ("Hébergeur", "GitHub Pages — GitHub Inc., 88 Colin P Kelly Jr St, San Francisco, CA 94107, USA"),
        ],
    },
    "confidentialite": {
        "title": "Politique de confidentialité",
        "description": "Politique de confidentialité de Dominus Habitat : données collectées, finalité, conservation et exercice de vos droits.",
        "rows": [
            ("Responsable", "Dominus Consultancy FZCO — Thomas Martin — IFZA Properties, Dubai Silicon Oasis, Dubai, UAE"),
            ("Données collectées", "Nom et prénom, téléphone, code postal"),
            ("Finalité", "Recontacter le prospect pour établir un devis ITE"),
            ("Base légale", "Intérêt légitime (demande explicite de l’utilisateur)"),
            ("Conservation", "3 ans après la dernière prise de contact"),
            ("Destinataires", "Dominus Consultancy FZCO uniquement, aucune vente ni transmission"),
            ("Droits (accès, rectification, suppression)", EMAIL),
            ("Réclamation", "CNIL — " + CNIL),
        ],
    },
}

EXTRA_CSS = """
/* ---------- Pages légales ---------- */
.page-hero{background:var(--marine);color:var(--on-dark);padding:clamp(48px,7vw,80px) 0 calc(var(--cut) + clamp(32px,4vw,48px))}
.page-hero h1{color:#fff;font-size:clamp(2.2rem,4.6vw,3.4rem)}
.page-hero .kicker a{color:var(--gold);text-decoration:none}
.page-hero .kicker a:hover{text-decoration:underline}
.page-hero :focus-visible{outline-color:var(--gold)}
.legal{padding:clamp(48px,7vw,88px) 0}
.legal-list{max-width:820px;margin:0;border-top:2px solid var(--marine)}
.legal-list div{display:grid;grid-template-columns:minmax(0,15rem) minmax(0,1fr);gap:8px 32px;padding:20px 0;border-bottom:1px solid var(--line)}
.legal-list dt{font-weight:600;color:var(--ink)}
.legal-list dd{margin:0;color:var(--text);overflow-wrap:anywhere}
.legal-list a{color:var(--marine)}
.todo{background:#fff3d6;color:var(--ink);padding:2px 8px;border-radius:4px;font-weight:500}
.legal-back{margin-top:40px}
@media (max-width:640px){.legal-list div{grid-template-columns:1fr}}
"""


def block(html, pattern):
    m = re.search(pattern, html, re.S)
    assert m, pattern
    return m.group(0)


def localize(fragment, current):
    """Les ancres de la landing pointent vers index.html depuis les pages légales."""
    fragment = re.sub(r'href="#top"', 'href="index.html"', fragment)
    fragment = re.sub(r'href="#([\w-]+)"', r'href="index.html#\1"', fragment)
    fragment = fragment.replace(' id="year"', "").replace(' id="mobile-cta"', "")
    return fragment.replace(f'href="{current}.html"', f'href="{current}.html" aria-current="page"')


index = (ROOT / "index.html").read_text(encoding="utf-8")
style = block(index, r"<style>.*?</style>").replace("</style>", EXTRA_CSS.lstrip("\n") + "</style>")
header = block(index, r'<header class="site-header">.*?</header>')
footer = block(index, r'<footer class="site-footer">.*?</footer>')
mobile = block(index, r'<div class="mobile-cta".*?</a>\s*</div>')

for slug, page in PAGES.items():
    rows = "\n".join(
        f"        <div><dt>{label}</dt><dd>{value}</dd></div>" for label, value in page["rows"]
    )
    html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page["title"]} | Dominus Habitat</title>
<meta name="description" content="{page["description"]}">
<link rel="canonical" href="{SITE}{slug}.html">
<meta name="robots" content="noindex, follow">
<meta name="theme-color" content="#164174">
<meta name="color-scheme" content="light">
<link rel="icon" type="image/png" href="assets/logo-monogramme.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Jost:wght@400;500;600&display=swap">
<!-- Généré par tools/build_legal.py : modifier le script, pas ce fichier. -->
{style}
</head>
<body>
<a class="skip" href="#contenu">Aller au contenu</a>

{localize(header, slug)}

<main id="contenu">
<div class="roof-bottom">
  <div class="page-hero roof-panel">
    <div class="wrap">
      <p class="kicker kicker-light"><a href="index.html">Accueil</a> / {page["title"]}</p>
      <h1>{page["title"]}</h1>
    </div>
  </div>
</div>

<section class="legal" aria-label="{page["title"]}">
  <div class="wrap">
    <dl class="legal-list">
{rows}
    </dl>
    <p class="legal-back"><a class="btn btn-line" href="index.html">Retour à l’accueil</a></p>
  </div>
</section>
</main>

{localize(footer, slug)}

{localize(mobile, slug)}
</body>
</html>
"""
    (ROOT / f"{slug}.html").write_text(html, encoding="utf-8")
    print("écrit", f"{slug}.html")

"""Génère mentions-legales.html et confidentialite.html avec le header, le footer
et les styles d'index.html.

Le bandeau cookies et son script sont aussi repris d'index.html.

À relancer après toute modification du header, du footer, du bandeau cookies ou du <style> d'index.html,
ou du contenu légal ci-dessous :
    python3 tools/build_legal.py && python3 tools/build_headers.py
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://dominushabitat.com/"
EMAIL = '<a href="mailto:contact@dominushabitat.com">contact@dominushabitat.com</a>'
CNIL = '<a href="https://www.cnil.fr" rel="noopener noreferrer">www.cnil.fr</a>'
TODO = '<span class="todo">[À COMPLÉTER]</span>'

GOOGLE_DPF = '<a href="https://www.dataprivacyframework.gov" rel="noopener noreferrer">Data Privacy Framework</a>'

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
        "sections": [],
    },
    "confidentialite": {
        "title": "Politique de confidentialité",
        "description": "Politique de confidentialité de Dominus Habitat : données collectées, finalité, conservation, cookies et exercice de vos droits.",
        "rows": [
            ("Données collectées", "Via le formulaire de demande d’étude : nom, prénom, numéro de téléphone, code postal, type de logement (maison individuelle ou maison de ville), surface de façade estimée, et toute information complémentaire communiquée lors des échanges ultérieurs avec nos conseillers (situation du logement, année de construction, mode de chauffage, objectifs de rénovation). Avec votre demande sont enregistrés la page d’origine et, le cas échéant, les paramètres de la campagne publicitaire qui vous a amené sur le site (utm, gclid, fbclid)."),
            ("Finalité", "Recontacter le prospect pour établir un devis ITE ; mesurer l’efficacité des campagnes publicitaires"),
            ("Base légale", "Intérêt légitime"),
            ("Conservation", "3 ans"),
            ("Destinataires", "Équipe Dominus Habitat et sociétés partenaires intervenant pour la réalisation du devis et des travaux d’isolation."),
            ("Vos droits", "Accès, rectification, suppression, opposition, portabilité : " + EMAIL + ". Réponse sous 30 jours."),
            ("Réclamation", "CNIL — " + CNIL + " — 3 place de Fontenoy, 75007 Paris"),
            ("Responsable du traitement", "Dominus Consultancy FZCO, Thomas Martin, IFZA Properties, Dubai Silicon Oasis, Dubai, UAE"),
        ],
        "sections": [
            ("stockage", "Stockage des données", [
                "Les données du formulaire sont transmises à notre outil de gestion des demandes (CRM Dominus, hébergé par Supabase et Vercel dans l’Union européenne) et à " + EMAIL + ". Cette boîte est hébergée via Cloudflare Email Routing et Gmail (Google LLC).",
                "Les serveurs de Google sont situés dans l’Union européenne et aux États-Unis. Google adhère au " + GOOGLE_DPF + " et agit comme sous-traitant dans le cadre de l’accord de traitement des données (DPA) Google Workspace.",
                "Le site lui-même ne stocke aucune donnée : il transmet la demande à notre CRM.",
            ]),
            ("cookies", "Cookies", [
                "Ce site utilise, uniquement après votre consentement : le Pixel Meta (Meta Platforms Ireland Ltd, 4 Grand Canal Square, Dublin 2, Irlande) à des fins publicitaires ; Google Analytics 4 et le suivi des conversions Google Ads (Google Ireland Ltd, Gordon House, Barrow Street, Dublin 4, Irlande) pour mesurer l’audience du site et l’efficacité de nos publicités (pages vues, clics sur les boutons, demandes d’étude). Le mode de consentement de Google (Consent Mode v2) est réglé sur « refusé » par défaut.",
                'Vous pouvez retirer votre consentement à tout moment via le lien « Gérer mes cookies » en bas de page : <button type="button" class="link-btn link-inline" data-cookie-settings>gérer mes cookies</button>.',
                "Meta et Google adhèrent au Data Privacy Framework UE–États-Unis. Aucun autre cookie de traçage n’est utilisé.",
            ]),
            ("securite", "Mesures de sécurité", [
                "Transmission chiffrée (HTTPS), accès limité aux personnes habilitées, aucun stockage sur le site.",
            ]),
        ],
    },
}

EXTRA_CSS = """
/* ---------- Pages légales ---------- */
.legal{padding:clamp(48px,7vw,88px) 0}
.legal-list{max-width:820px;margin:0;border-top:2px solid var(--marine)}
.legal-list div{display:grid;grid-template-columns:minmax(0,15rem) minmax(0,1fr);gap:8px 32px;padding:20px 0;border-bottom:1px solid var(--line)}
.legal-list dt{font-weight:600;color:var(--ink)}
.legal-list dd{margin:0;color:var(--text);overflow-wrap:anywhere}
.legal-list a{color:var(--marine)}
.legal-section{max-width:820px;margin-top:56px;scroll-margin-top:96px}
.legal-section:first-child{margin-top:0}
.legal-section .legal-list{margin-top:1.25rem}
.legal-section h2{font-size:clamp(1.7rem,3vw,2.1rem);margin-bottom:1rem}
.legal-section p{max-width:68ch;color:var(--text)}
.legal-section p+p{margin-top:.8rem}
.legal-section a,.link-inline{color:var(--marine);text-decoration:underline}
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
cookies = block(index, r'<div class="cookie-banner".*?</script>')

for slug, page in PAGES.items():
    sections = "".join(
        f'\n    <div class="legal-section" id="{sid}">\n      <h2>{title}</h2>\n'
        + "".join(f"      <p>{para}</p>\n" for para in paras)
        + "    </div>"
        for sid, title, paras in page["sections"]
    )
    sections = sections.lstrip("\n")
    rows = "\n".join(
        f"        <div><dt>{label}</dt><dd>{value}</dd></div>" for label, value in page["rows"]
    )
    table = f'    <dl class="legal-list">\n{rows}\n    </dl>'
    if sections:
        body = sections + '\n    <div class="legal-section" id="rgpd">\n      <h2>Synthèse RGPD</h2>\n' + table + "\n    </div>"
    else:
        body = table
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
<link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fonts/source-serif-4-latin.woff2">
<link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fonts/jost-latin.woff2">
<!-- Généré par tools/build_legal.py : modifier le script, pas ce fichier. -->
{style}
</head>
<body data-cookie-prompt="manual">
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
{body}
    <p class="legal-back"><a class="btn btn-line" href="index.html">Retour à l’accueil</a></p>
  </div>
</section>
</main>

{localize(footer, slug)}

{localize(mobile, slug)}

{cookies}
</body>
</html>
"""
    (ROOT / f"{slug}.html").write_text(html, encoding="utf-8")
    print("écrit", f"{slug}.html")

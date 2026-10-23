#!/usr/bin/env python3
"""Génère la rubrique « Nos chantiers » à partir de chantiers/chantiers.json.

- Photos : recadrage 4:3 autour du point d'intérêt, floutage des zones indiquées, suppression des métadonnées,
  export AVIF + WebP + JPEG en 480 / 800 / 1200 px dans assets/chantiers/<slug>/ (noms descriptifs).
- Pages : /nos-chantiers/ (liste, filtres, pagination), une fiche par chantier, une page par département
  (à partir de 2 chantiers publiés), la page publicitaire /lp/isolation-exterieure/ (noindex).
- Accueil : section « Nos réalisations » (3 chantiers) entre les marqueurs <!-- chantiers:start/end -->,
  lien « Nos chantiers » dans l'en-tête et le pied de page.
- sitemap.xml avec les images.

Un chantier n'est publié que s'il a les trois étapes (avant, pendant, après), accord_client = true et publie = true.
Le reste est listé dans le rapport « ce qui manque » en fin d'exécution.

    python3 tools/build_chantiers.py                    # site réel
    python3 tools/build_chantiers.py --apercu /tmp/x    # copie du site avec les chantiers non publiés (maquette)

Puis : python3 tools/build_legal.py && python3 tools/build_headers.py
"""
import argparse, datetime, html, json, pathlib, re, shutil, sys
from PIL import Image, ImageFilter, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://dominushabitat.com/"
WIDTHS = [480, 800, 1200]
RATIO = (4, 3)
PER_PAGE = 9
STEPS = [("avant", "Avant", "État initial de la façade"), ("pendant", "Pendant", "Pose de l'isolant et sous-enduit"), ("apres", "Après", "Façade terminée")]
TRAVAUX = {"ite": "Isolation thermique par l'extérieur"}
# Certifications affichées dans le bloc de confiance des fiches : laisser vide tant que les preuves ne sont pas fournies.
CERTIFICATIONS = []
TODAY = datetime.date.today().isoformat()

esc = html.escape


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------
def slugify(s):
    s = s.lower()
    for a, b in (("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"), ("à", "a"), ("â", "a"), ("î", "i"), ("ï", "i"), ("ô", "o"), ("ù", "u"), ("û", "u"), ("ç", "c"), ("'", "-"), ("’", "-")):
        s = s.replace(a, b)
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")


def load():
    data = json.loads((ROOT / "chantiers" / "chantiers.json").read_text(encoding="utf-8"))
    out = []
    for c in data["chantiers"]:
        missing = []
        for step, _, _ in STEPS:
            # apres_seul : chantier photographié après travaux seulement, publié avec une mention honnête
            if not c["photos"].get(step) and not (c.get("apres_seul") and step != "apres"):
                missing.append(f"photos « {step} »")
        if not c.get("accord_client"):
            missing.append("accord du client pour la publication")
        if not c.get("publie"):
            missing.append("interrupteur « publie » à true")
        c["_manque"] = missing
        c["_publiable"] = not missing
        c["dept_slug"] = f"{slugify(c['departement']['nom'])}-{c['departement']['code']}"
        c["lieu"] = f"{c['departement']['nom']} ({c['departement']['code']})"
        c["lieu_long"] = (f"{c['commune']}, " if c.get("afficher_commune") and c.get("commune") else "") + c["lieu"]
        c["travaux_label"] = TRAVAUX.get(c["travaux"], c["travaux"])
        c["url"] = f"/nos-chantiers/{c['slug']}/"
        out.append(c)
    return out


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------
def process_photo(c, step, n, photo, assets_dir):
    """Recadre, floute, retire les métadonnées, exporte en 3 formats × 3 largeurs. Renvoie le descripteur HTML."""
    src = ROOT / "chantiers" / "sources" / c["slug"] / photo["fichier"]
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    for x, y, w, h in photo.get("flou", []):
        box = (x, y, x + w, y + h)
        region = im.crop(box)
        small = region.resize((max(1, w // 24), max(1, h // 24)), Image.BILINEAR).resize(region.size, Image.NEAREST)
        im.paste(small.filter(ImageFilter.GaussianBlur(radius=max(w, h) / 10)), box)
    # Recadrage 4:3 autour du point d'intérêt
    W, H = im.size
    fx, fy = photo.get("focal", [0.5, 0.5])
    if W / H > RATIO[0] / RATIO[1]:
        cw, ch = int(H * RATIO[0] / RATIO[1]), H
    else:
        cw, ch = W, int(W * RATIO[1] / RATIO[0])
    left = min(max(int(fx * W - cw / 2), 0), W - cw)
    top = min(max(int(fy * H - ch / 2), 0), H - ch)
    im = im.crop((left, top, left + cw, top + ch))
    base = f"ite-{slugify(c['type_logement'])}-{c['departement']['code']}-{step}-{n}"
    assets_dir.mkdir(parents=True, exist_ok=True)
    widths = [w for w in WIDTHS if w <= im.width] or [im.width]
    for w in widths:
        out = im.resize((w, int(w * RATIO[1] / RATIO[0])), Image.LANCZOS)
        out.save(assets_dir / f"{base}-{w}.avif", quality=58)
        out.save(assets_dir / f"{base}-{w}.webp", quality=78, method=6)
        out.save(assets_dir / f"{base}-{w}.jpg", quality=82, optimize=True, progressive=True)
    rel = f"/assets/chantiers/{c['slug']}/{base}"
    return {"base": rel, "widths": widths, "alt": photo["alt"], "step": step, "vue": photo.get("vue")}


def picture(p, sizes, priority=False, cls=""):
    if p is None:
        return ""
    def srcset(ext):
        return ", ".join(f"{p['base']}-{w}.{ext} {w}w" for w in p["widths"])
    mid = 800 if 800 in p["widths"] else p["widths"][-1]
    load = 'fetchpriority="high"' if priority else 'loading="lazy"'
    return (
        f'<picture{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>'
        f'<source type="image/avif" srcset="{srcset("avif")}" sizes="{sizes}">'
        f'<source type="image/webp" srcset="{srcset("webp")}" sizes="{sizes}">'
        f'<img src="{p["base"]}-{mid}.jpg" srcset="{srcset("jpg")}" sizes="{sizes}" width="{RATIO[0] * 300}" height="{RATIO[1] * 300}" alt="{esc(p["alt"])}" {load} decoding="async"></picture>'
    )


def placeholder(step_label):
    return f'<div class="step-missing" role="img" aria-label="Photo {step_label.lower()} : à venir"><span>Photo à venir</span></div>'


# ---------------------------------------------------------------------------
# Fragments de page
# ---------------------------------------------------------------------------
PIN = '<svg class="pin" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M8 14.5s4.5-4.3 4.5-8a4.5 4.5 0 0 0-9 0c0 3.7 4.5 8 4.5 8z"/><circle cx="8" cy="6.5" r="1.6"/></svg>'
ARROW = '<svg class="btn-arrow" width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 9h11M10 4.5L14.5 9 10 13.5"/></svg>'


def card(c, priority=False, heading="h3"):
    """Dossier de chantier : les trois étapes côte à côte, puis le texte et le bouton."""
    tiles = []
    note = ""
    if c.get("apres_seul"):
        # Trois vues après travaux (rue, arrière, détail) à la place des trois étapes, avec la mention
        for i, p in enumerate(c["_pictures"]["apres"][:3]):
            label = p.get("vue") or "Après"  # étiquette courte (Rue, Arrière, Détail) ; la couleur or signale « après »
            tiles.append(f'<li class="step step-apres"><button type="button" class="step-open" data-label="{esc(label)}" aria-label="Agrandir : {esc(label)}">{picture(p, "(max-width:640px) 92vw, (max-width:900px) 60vw, 380px", priority and i == 0)}</button><span class="step-tag">{esc(label)}</span></li>')
        note = ""
    else:
        for i, (step, label, _) in enumerate(STEPS):
            photos = c["_pictures"][step]
            pic = picture(photos[0], "(max-width:640px) 92vw, (max-width:900px) 60vw, 380px", priority and i == 2) if photos else placeholder(label)
            tiles.append(
                f'<li class="step step-{step}"><button type="button" class="step-open" data-label="{label}" aria-label="Agrandir : {label}">{pic}</button>'
                f'<span class="step-tag">{label}</span></li>'
            )
    apercu = '<span class="apercu-tag">Aperçu : non publié</span>' if not c["_publiable"] else ""
    return f"""<article class="chantier-card" data-gallery data-chantier="{esc(c['slug'])}" data-departement="{c['departement']['code']}" data-travaux="{esc(c['travaux'])}">
  {apercu}
  <ol class="chantier-steps{' steps-apres-seul' if c.get('apres_seul') else ''}" aria-label="{'Après travaux' if c.get('apres_seul') else 'Avant, pendant, après'}">{''.join(tiles)}</ol>{note}
  <div class="chantier-body">
    <{heading}>{esc(c['travaux_label'])}</{heading}>
    <p class="chantier-place">{PIN}<span>{esc(c['lieu_long'])}</span></p>
    <p class="chantier-kind">{esc(c['type_logement'])}, {esc(c['titre_court'].lower())}</p>
    <a class="btn btn-line" href="{c['url']}" data-cta="chantier-card">Découvrir ce chantier{ARROW}</a>
  </div>
</article>"""


def carousel(items, label, priority_first=False):
    cards = "".join(card(c, priority=(priority_first and i == 0)) for i, c in enumerate(items))
    return f"""<div class="chantier-carousel" data-carousel>
  <div class="chantier-track" tabindex="0" role="region" aria-label="{esc(label)}" aria-roledescription="carrousel">{cards}</div>
  <div class="carousel-nav" hidden>
    <button type="button" class="carousel-btn" data-dir="-1" aria-label="Chantiers précédents"><svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.5 4L6.5 10l6 6"/></svg></button>
    <div class="carousel-dots" role="tablist" aria-label="Pages du carrousel"></div>
    <button type="button" class="carousel-btn" data-dir="1" aria-label="Chantiers suivants"><svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7.5 4l6 6-6 6"/></svg></button>
  </div>
</div>"""


LIGHTBOX = """<dialog class="lightbox" id="lightbox" aria-label="Photo du chantier en grand">
  <div class="lightbox-head"><p id="lightbox-title" class="lightbox-title"></p><button type="button" class="lightbox-close" data-close aria-label="Fermer">&times;</button></div>
  <figure class="lightbox-figure"><div id="lightbox-img"></div><figcaption id="lightbox-cap"></figcaption></figure>
  <div class="lightbox-nav"><button type="button" class="btn btn-outline" data-nav="-1">Étape précédente</button><button type="button" class="btn btn-gold" data-nav="1">Étape suivante</button></div>
</dialog>"""

CHANTIERS_JS = r"""<script>
/* Nos chantiers : carrousel (scroll-snap, sans défilement automatique), photo en grand (dialog natif). */
(function(){
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll("[data-carousel]").forEach(function(c){
    var track = c.querySelector(".chantier-track"), nav = c.querySelector(".carousel-nav"), dots = c.querySelector(".carousel-dots");
    var cards = track.querySelectorAll(".chantier-card");
    if (!cards.length) return;
    function perView(){ var w = cards[0].getBoundingClientRect().width || 1; return Math.max(1, Math.round(track.clientWidth / w)); }
    function pages(){ return Math.ceil(cards.length / perView()); }
    function current(){ var w = cards[0].getBoundingClientRect().width || 1; return Math.round(track.scrollLeft / (w * perView())); }
    function render(){
      var n = pages();
      nav.hidden = n <= 1;
      dots.innerHTML = "";
      for (var i = 0; i < n; i++){
        var b = document.createElement("button");
        b.type = "button"; b.setAttribute("role", "tab"); b.setAttribute("aria-label", "Page " + (i + 1) + " sur " + n);
        b.setAttribute("aria-selected", i === current() ? "true" : "false"); b.dataset.page = i;
        dots.appendChild(b);
      }
    }
    function go(page){
      var w = cards[0].getBoundingClientRect().width || 1, gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      track.scrollTo({ left: page * perView() * (w + gap), behavior: reduce ? "auto" : "smooth" });
    }
    nav.addEventListener("click", function(e){
      var d = e.target.closest("[data-dir]"), p = e.target.closest("[data-page]");
      if (d) go(Math.min(pages() - 1, Math.max(0, current() + Number(d.dataset.dir))));
      else if (p) go(Number(p.dataset.page));
    });
    track.addEventListener("keydown", function(e){
      if (e.key === "ArrowRight"){ e.preventDefault(); go(Math.min(pages() - 1, current() + 1)); }
      if (e.key === "ArrowLeft"){ e.preventDefault(); go(Math.max(0, current() - 1)); }
    });
    var t; track.addEventListener("scroll", function(){ clearTimeout(t); t = setTimeout(function(){ dots.querySelectorAll("[role=tab]").forEach(function(b, i){ b.setAttribute("aria-selected", i === current() ? "true" : "false"); }); }, 80); }, { passive: true });
    window.addEventListener("resize", render);
    render();
  });

  var box = document.getElementById("lightbox");
  if (!box || typeof box.showModal !== "function") return;
  var steps = [], idx = 0, opener = null;
  function show(i){
    idx = (i + steps.length) % steps.length;
    var s = steps[idx];
    document.getElementById("lightbox-title").textContent = s.label + " · " + (idx + 1) + " / " + steps.length;
    var holder = document.getElementById("lightbox-img");
    holder.innerHTML = "";
    if (s.picture){ var clone = s.picture.cloneNode(true); clone.querySelectorAll("img").forEach(function(im){ im.removeAttribute("loading"); im.sizes = "100vw"; }); holder.appendChild(clone); }
    else { var d = document.createElement("p"); d.className = "step-missing"; d.textContent = "Photo à venir"; holder.appendChild(d); }
    document.getElementById("lightbox-cap").textContent = s.alt || "";
  }
  document.addEventListener("click", function(e){
    var b = e.target.closest(".step-open");
    if (!b) return;
    var scope = b.closest("[data-gallery]") || document;
    var buttons = Array.prototype.slice.call(scope.querySelectorAll(".step-open"));
    steps = buttons.map(function(btn){
      var pic = btn.querySelector("picture"), img = btn.querySelector("img");
      return { label: btn.dataset.label || "", picture: pic, alt: img ? img.alt : "" };
    });
    opener = b; show(buttons.indexOf(b));
    box.showModal();
    if (window.dhEvent) window.dhEvent("photo_zoom", { chantier: scope.dataset ? scope.dataset.chantier : "", etape: steps[idx].label });
  });
  box.addEventListener("click", function(e){
    if (e.target.closest("[data-close]") || e.target === box) box.close();
    var n = e.target.closest("[data-nav]"); if (n) show(idx + Number(n.dataset.nav));
  });
  box.addEventListener("keydown", function(e){ if (e.key === "ArrowRight") show(idx + 1); if (e.key === "ArrowLeft") show(idx - 1); });
  box.addEventListener("close", function(){ if (opener) opener.focus(); });
})();
</script>"""

LP_JS = r"""<script>
/* Formulaire de la page publicitaire : validation, envoi au CRM (dhSendLead), mesure (dhLead). */
(function(){
  "use strict";
  var form = document.getElementById("lead-form"); if (!form) return;
  function setError(input, id, msg){ document.getElementById(id).textContent = msg || ""; if (input) input.setAttribute("aria-invalid", msg ? "true" : "false"); return !msg; }
  form.addEventListener("submit", function(e){
    e.preventDefault();
    if (form.website.value) return;
    var ok = true;
    ok = setError(form.prenom, "err-prenom", form.prenom.value.trim().length < 2 ? "Indiquez votre prénom." : "") && ok;
    var t = form.tel.value.replace(/[\s.\-]/g, "");
    ok = setError(form.tel, "err-tel", /^(?:(?:\+|00)33|0)[1-9]\d{8}$/.test(t) ? "" : "Indiquez un numéro français valide, par exemple 06 12 34 56 78.") && ok;
    ok = setError(form.cp, "err-cp", /^(?:0[1-9]|[1-8]\d|9[0-8])\d{3}$/.test(form.cp.value.trim()) ? "" : "Indiquez un code postal à 5 chiffres.") && ok;
    var picked = form.querySelector("input[name=logement]:checked");
    ok = setError(null, "err-logement", picked ? "" : "Choisissez votre type de logement.") && ok;
    ok = setError(form.consentement, "err-consent", form.consentement.checked ? "" : "Cochez la case pour que nous puissions vous rappeler.") && ok;
    if (!ok){ var bad = form.querySelector("[aria-invalid=true]"); if (bad) bad.focus(); return; }
    var data = { prenom: form.prenom.value.trim(), tel: form.tel.value.trim(), cp: form.cp.value.trim(), logement: picked.value, consentement: "oui", page: location.href };
    var btn = form.querySelector("button[type=submit]"), err = document.getElementById("err-envoi");
    btn.disabled = true; err.textContent = "";
    (window.dhSendLead ? window.dhSendLead(data) : Promise.resolve({ ok: true }))
      .then(function(){ form.hidden = true; var done = document.getElementById("lead-done"); done.hidden = false; done.focus(); if (window.dhLead) window.dhLead(data); })
      .catch(function(){ btn.disabled = false; err.textContent = "L'envoi a échoué. Réessayez dans un instant ou écrivez-nous à contact@dominushabitat.com."; });
  });
  var mcta = document.getElementById("mobile-cta"), lead = document.getElementById("etude");
  if (mcta && lead && "IntersectionObserver" in window) new IntersectionObserver(function(entries){ mcta.classList.toggle("is-hidden", entries[0].isIntersecting); }, { threshold: 0.15 }).observe(lead);
})();
</script>"""

FILTERS_JS = r"""<script>
/* Filtres de la page Nos chantiers : agissent sur les cartes déjà présentes dans la page (aucune donnée chargée en JS). */
(function(){
  "use strict";
  var form = document.getElementById("filtres"); if (!form) return;
  var cards = document.querySelectorAll("#grille .chantier-card"), count = document.getElementById("compteur"), empty = document.getElementById("vide");
  function apply(push){
    var d = form.departement.value, t = form.travaux.value, n = 0;
    cards.forEach(function(c){ var ok = (!d || c.dataset.departement === d) && (!t || c.dataset.travaux === t); c.hidden = !ok; if (ok) n++; });
    count.textContent = n + (n > 1 ? " chantiers" : " chantier");
    empty.hidden = n > 0;
    if (push){ var p = new URLSearchParams(); if (d) p.set("departement", d); if (t) p.set("travaux", t); history.replaceState(null, "", location.pathname + (p.toString() ? "?" + p : "")); }
  }
  var q = new URLSearchParams(location.search);
  if (q.get("departement")) form.departement.value = q.get("departement");
  if (q.get("travaux")) form.travaux.value = q.get("travaux");
  form.addEventListener("change", function(){ apply(true); });
  form.addEventListener("submit", function(e){ e.preventDefault(); apply(true); });
  apply(false);
})();
</script>"""


# ---------------------------------------------------------------------------
# Gabarit commun (en-tête, pied de page, styles d'index.html)
# ---------------------------------------------------------------------------
def block(text, pattern):
    m = re.search(pattern, text, re.S)
    assert m, pattern
    return m.group(0)


def absolutize(fragment, current=None):
    """Depuis un sous-dossier, les liens de la landing deviennent absolus."""
    fragment = re.sub(r'href="#top"', 'href="/"', fragment)
    fragment = re.sub(r'href="#([\w-]+)"', r'href="/#\1"', fragment)
    fragment = re.sub(r'(src|href)="assets/', r'\1="/assets/', fragment)
    fragment = re.sub(r'href="(mentions-legales|confidentialite)\.html', r'href="/\1.html', fragment)
    fragment = fragment.replace('url("assets/', 'url("/assets/').replace(' id="year"', "").replace(' id="mobile-cta"', ' id="mobile-cta"')
    if current:
        fragment = fragment.replace(f'href="{current}"', f'href="{current}" aria-current="page"')
    return fragment


def layout(index, *, title, description, canonical, body, robots="index, follow", og_image=None, extra_head="", body_attrs="", current="/nos-chantiers/", light=False):
    style = absolutize(block(index, r"<style>.*?</style>"))
    header = absolutize(block(index, r'<header class="site-header">.*?</header>'), current)
    footer = absolutize(block(index, r'<footer class="site-footer">.*?</footer>'), current)
    mobile = absolutize(block(index, r'<div class="mobile-cta".*?</a>\s*</div>'))
    mesure = absolutize(block(index, r"<!-- mesure:start -->.*?<!-- mesure:end -->"))
    renov = block(index, r'<div class="renov-banner".*?</script>')  # bandeau France Rénov' (obligatoire sur toutes les pages)
    cookies = absolutize(block(index, r'<div class="cookie-banner".*?</script>'))
    if light:
        # Page publicitaire : en-tête réduit à la marque (pas de navigation), pied de page légal seulement
        header = re.sub(r'<a class="header-link".*?</a>', "", header, flags=re.S)
        footer = re.sub(r'<div>\s*<h2>La page</h2>.*?</div>\s*', "", footer, count=1, flags=re.S)
    og = og_image or f"{SITE}assets/logo-dominus-habitat.png"
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="{robots}">
<meta name="theme-color" content="#164174">
<meta name="color-scheme" content="light">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="Dominus Habitat">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="{'summary_large_image' if og_image else 'summary'}">
<link rel="icon" type="image/png" href="/assets/logo-monogramme.png">
<link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fonts/source-serif-4-latin.woff2">
<link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fonts/jost-latin.woff2">
{extra_head}<!-- Généré par tools/build_chantiers.py : modifier le script ou chantiers/chantiers.json, pas ce fichier. -->
{style}
</head>
<body{body_attrs}>
<a class="skip" href="#contenu">Aller au contenu</a>

{header}

<main id="contenu">
{body}
</main>

{footer}

{mobile}

{LIGHTBOX}
{renov}
{mesure}
{cookies}
{CHANTIERS_JS}
</body>
</html>
"""


def breadcrumb_html(items):
    parts = []
    for i, (label, href) in enumerate(items):
        if href and i < len(items) - 1:
            parts.append(f'<li><a href="{href}">{esc(label)}</a></li>')
        else:
            parts.append(f'<li aria-current="page">{esc(label)}</li>')
    return f'<nav class="crumbs" aria-label="Fil d\'Ariane"><ol>{"".join(parts)}</ol></nav>'


def breadcrumb_ld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": label, **({"item": SITE.rstrip("/") + href} if href else {})} for i, (label, href) in enumerate(items)],
    }


def ld(obj):
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>\n'


def page_slim(crumbs, h1, sub):
    """Titre compact (liste des chantiers) : les chantiers apparaissent tout de suite, sans défiler."""
    return f"""<div class="page-slim">
  <div class="wrap">
    {crumbs}
    <h1>{h1}</h1>
    <p class="slim-sub">{esc(sub)}</p>
  </div>
</div>"""


def page_hero(crumbs, kicker, h1, lede, cta=True):
    btn = f'<p class="hero-actions"><a class="btn btn-gold" href="/#etude" data-cta="hero">Demander mon étude gratuite{ARROW}</a></p>' if cta else ""
    return f"""<div class="roof-bottom">
  <div class="page-hero roof-panel">
    <div class="wrap">
      {crumbs}
      <p class="kicker kicker-light">{esc(kicker)}</p>
      <h1>{h1}</h1>
      <p class="hero-sub">{esc(lede)}</p>
      {btn}
    </div>
  </div>
</div>"""


CTA_BAND = """<section class="chantier-cta" aria-labelledby="cta-chantiers">
  <div class="wrap">
    <h2 id="cta-chantiers">Et si c'était votre maison ?</h2>
    <p>Décrivez-nous votre projet en trois questions. Un conseiller vous rappelle pour préparer votre étude, sans engagement.</p>
    <a class="btn btn-gold" href="/#etude" data-cta="bande">Demander mon étude gratuite{ARROW}</a>
  </div>
</section>""".replace("{ARROW}", ARROW)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
INTRO = "Nos chantiers, notre savoir-faire en images."
SOUS_TITRE = "De la préparation des façades aux dernières finitions, découvrez les étapes de nos réalisations en isolation thermique par l'extérieur : l'état initial, la pose de l'isolant, la façade terminée."
REASSURANCE = "Des chantiers réels, des travaux visibles, un savoir-faire à découvrir."


def page_liste(index, items, out_dir, *, dept=None, page=1, pages_total=1, all_depts=(), dept_pages=()):
    if dept:
        base = f"/nos-chantiers/{dept['slug']}/"
        title = f"Isolation thermique par l'extérieur en {dept['nom']} ({dept['code']}) : chantiers réalisés | Dominus Habitat"
        description = f"Nos chantiers d'isolation thermique par l'extérieur dans le {dept['nom']} ({dept['code']}) : façades avant, pendant et après travaux, maisons individuelles rénovées. Étude gratuite."
        h1 = f"Isolation thermique par l'extérieur en {esc(dept['nom'])} <span class=\"h1-accent\">({dept['code']})</span>"
        lede = f"Maisons isolées par l'extérieur dans le {dept['nom']} : chaque chantier est présenté en trois étapes, de la façade d'origine à la finition."
        crumbs_items = [("Accueil", "/"), ("Nos chantiers", "/nos-chantiers/"), (f"{dept['nom']} ({dept['code']})", base)]
    else:
        base = "/nos-chantiers/"
        title = "Nos chantiers d'isolation thermique par l'extérieur (ITE) | Dominus Habitat"
        description = "Chantiers réels d'isolation de façade avant, pendant et après travaux : maisons individuelles et maisons de ville rénovées par Dominus Habitat. Étude gratuite."
        h1 = INTRO.replace("savoir-faire", '<span class="h1-accent">savoir-faire</span>')
        lede = SOUS_TITRE
        crumbs_items = [("Accueil", "/"), ("Nos chantiers", base)]
    canonical = SITE.rstrip("/") + base + (f"page/{page}/" if page > 1 else "")
    crumbs = breadcrumb_html(crumbs_items)
    opts_d = "".join(f'<option value="{d["code"]}">{esc(d["nom"])} ({d["code"]})</option>' for d in all_depts)
    filtres = "" if (dept or len(all_depts) < 2) else f"""<form id="filtres" class="filtres" aria-label="Filtrer les chantiers">
      <div class="field"><label for="f-dep">Département</label><select id="f-dep" name="departement"><option value="">Tous</option>{opts_d}</select></div>
      <div class="field"><label for="f-tr">Type de travaux</label><select id="f-tr" name="travaux"><option value="">Tous</option>{''.join(f'<option value="{k}">{esc(v)}</option>' for k, v in TRAVAUX.items())}</select></div>
      <noscript><button type="submit" class="btn btn-line">Filtrer</button></noscript>
    </form>"""
    n = len(items)
    grid = "".join(card(c, priority=(i == 0), heading="h2") for i, c in enumerate(items))
    pagination = ""
    if pages_total > 1:
        links = []
        for p in range(1, pages_total + 1):
            href = base if p == 1 else f"{base}page/{p}/"
            links.append(f'<li><a href="{href}"{" aria-current=&quot;page&quot;" if p == page else ""}>{p}</a></li>'.replace("&quot;", '"'))
        pagination = f'<nav class="pagination" aria-label="Pages"><ol>{"".join(links)}</ol></nav>'
    dept_links = ""
    if not dept and dept_pages:
        dept_links = '<p class="dept-links">Par département : ' + ", ".join(f'<a href="/nos-chantiers/{d["slug"]}/">{esc(d["nom"])} ({d["code"]})</a>' for d in dept_pages) + "</p>"
    sub = REASSURANCE if not dept else lede
    body = page_slim(crumbs, h1, sub) + f"""
<section class="chantiers-liste liste-top" aria-label="Liste des chantiers">
  <div class="wrap">
    <div class="liste-bar">
      {filtres}
      <p id="compteur" class="compteur" aria-live="polite">{n} chantier{'s' if n > 1 else ''}</p>
    </div>
    {dept_links}
    <div id="grille" class="chantier-grid">{grid}</div>
    <p id="vide" class="vide" {'hidden' if n else ''}>Aucun chantier ne correspond à ces critères pour le moment. <a href="{base}">Voir tous les chantiers</a> ou <a href="/#etude">demander votre étude gratuite</a>.</p>
    {pagination}
  </div>
</section>
{CTA_BAND}
"""
    extra = ld(breadcrumb_ld(crumbs_items))
    for c in items:
        for p in c["_pictures"]["apres"][:1]:
            extra += ld({"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": f"{SITE.rstrip('/')}{p['base']}-1200.jpg", "name": p["alt"], "description": p["alt"]})
    html_out = layout(index, title=title, description=description, canonical=canonical, body=body, extra_head=extra, current="/nos-chantiers/")
    html_out = html_out.replace(CHANTIERS_JS, CHANTIERS_JS + ("" if dept else FILTERS_JS))
    out = out_dir / ("" if page == 1 else f"page/{page}") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_out, encoding="utf-8")
    return canonical


def page_fiche(index, c, others, out_root):
    title = f"ITE à {c['commune']}, {c['lieu']} : chantier {c['reference']} | Dominus Habitat" if c.get("afficher_commune") and c.get("commune") else f"Isolation extérieure en {c['lieu']} : chantier {c['reference']} | Dominus Habitat"
    description = f"Isolation thermique par l'extérieur d'une {c['type_logement'].lower()} en {c['lieu']} : photos avant, pendant et après travaux, enduit de finition, étapes du chantier. Étude gratuite."
    h1 = f"Isolation thermique par l'extérieur à {esc(c['commune'])}, {esc(c['departement']['nom'])} <span class=\"h1-accent\">({c['departement']['code']})</span>" if c.get("afficher_commune") and c.get("commune") else f"Isolation thermique par l'extérieur en {esc(c['departement']['nom'])} <span class=\"h1-accent\">({c['departement']['code']})</span>"
    crumbs_items = [("Accueil", "/"), ("Nos chantiers", "/nos-chantiers/"), (f"Chantier {c['reference']} · {c['lieu']}", c["url"])]
    crumbs = breadcrumb_html(crumbs_items)

    galleries = []
    for step, label, legend in STEPS:
        if c.get("apres_seul") and step != "apres":
            continue
        pics = c["_pictures"][step]
        if pics:
            figs = "".join(f'<figure class="gal-item"><button type="button" class="step-open" data-label="{label} · photo {k + 1}" aria-label="Agrandir la photo {label.lower()} {k + 1}">{picture(p, "(max-width:760px) 100vw, (max-width:1200px) 50vw, 580px", priority=(step == "apres" and k == 0))}</button><figcaption>{esc(p["alt"])}</figcaption></figure>' for k, p in enumerate(pics))
        else:
            figs = f'<p class="step-missing step-missing-wide">Photos « {label.lower()} » à venir.</p>'
        galleries.append(f'<section class="gal gal-{step}" aria-labelledby="gal-{step}"><h2 id="gal-{step}"><span class="step-tag step-tag-{step}">{label}</span> {esc(legend)}</h2><div class="gal-grid">{figs}</div></section>')

    carac = c.get("caracteristiques", {})
    rows = [
        ("Type d'isolation", carac.get("type_isolation")),
        ("Isolant", carac.get("materiau")),
        ("Épaisseur", f"{carac['epaisseur']} mm" if carac.get("epaisseur") else None),
        ("Finition", carac.get("finition")),
        ("Surface isolée", f"{carac['surface_m2']} m²" if carac.get("surface_m2") else None),
        ("Durée du chantier", carac.get("duree")),
        ("Année", str(carac["annee"]) if carac.get("annee") else None),
        ("Logement", c.get("type_logement")),
        ("Localisation", c["lieu_long"]),
    ]
    rows = [(k, v) for k, v in rows if v]
    carac_html = f'<section class="carac" aria-labelledby="carac-titre"><div class="wrap"><h2 id="carac-titre">Le chantier en bref</h2><dl class="carac-list">{"".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in rows)}</dl></div></section>' if rows else ""

    trust_html = ""
    if CERTIFICATIONS:
        trust_html = '<section class="trust-block" aria-labelledby="trust-titre"><div class="wrap"><h2 id="trust-titre">Nos garanties</h2><ul class="trust">' + "".join(f"<li>{esc(t)}</li>" for t in CERTIFICATIONS) + "</ul></div></section>"

    similar = [o for o in others if o["slug"] != c["slug"]]
    similar.sort(key=lambda o: (o["departement"]["code"] != c["departement"]["code"], o["reference"]))
    similar_html = f'<section class="similaires" aria-labelledby="sim-titre"><div class="wrap"><h2 id="sim-titre">Chantiers similaires</h2>{carousel(similar[:3], "Chantiers similaires")}<p class="more"><a class="btn btn-line" href="/nos-chantiers/">Voir toutes nos réalisations{ARROW}</a></p></div></section>' if similar else ""

    apercu = '<p class="apercu-band">Aperçu : ce chantier n\'est pas publié (' + esc(", ".join(c["_manque"])) + ").</p>" if not c["_publiable"] else ""
    body = page_hero(crumbs, f"Chantier {c['reference']} · {c['type_logement']}", h1, c["resume"]) + f"""
{apercu}
<section class="fiche" aria-label="Photos du chantier">
  <div class="wrap" data-gallery data-chantier="{esc(c['slug'])}">
    <p class="fiche-intro">{esc(c['type_logement'])}, {esc(c['titre_court'].lower())}. {"" if c.get("apres_seul") else "Chaque étape est photographiée sur le chantier : l'état initial, la pose de l'isolant et la façade terminée."}</p>
    {''.join(galleries)}
  </div>
</section>
{carac_html}
{trust_html}
{similar_html}
{CTA_BAND}
"""
    extra = ld(breadcrumb_ld(crumbs_items))
    for step, _, _ in STEPS:
        for p in c["_pictures"][step]:
            extra += ld({"@context": "https://schema.org", "@type": "ImageObject", "contentUrl": f"{SITE.rstrip('/')}{p['base']}-1200.jpg", "name": p["alt"], "description": p["alt"], "representativeOfPage": step == "apres"})
    og = f"{SITE.rstrip('/')}{c['_pictures']['apres'][0]['base']}-1200.jpg" if c["_pictures"]["apres"] else None
    out = out_root / c["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(layout(index, title=title, description=description, canonical=SITE.rstrip("/") + c["url"], body=body, og_image=og, extra_head=extra, body_attrs=f' data-chantier="{esc(c["slug"])}"'), encoding="utf-8")


def page_lp(index, items, out_root):
    """Page d'atterrissage publicitaire : message = annonce, 3 chantiers, 3 arguments, formulaire court. noindex."""
    strip = carousel(items[:3], "Trois chantiers avant, pendant, après", priority_first=True) if items else ""
    body = f"""<div class="roof-bottom">
  <div class="page-hero lp-hero roof-panel">
    <div class="wrap lp-grid">
      <div>
        <p class="kicker kicker-light">Isolation thermique par l'extérieur</p>
        <h1 data-ab="titre" data-a="Une façade neuve qui garde la chaleur de votre maison." data-b="Isolez votre maison par l'extérieur, sans perdre un mètre carré.">Une façade neuve qui garde la chaleur <span class="h1-accent">de votre maison.</span></h1>
        <p class="hero-sub">Étude gratuite et sans engagement : un conseiller étudie votre façade et vous rappelle. Vous restez chez vous pendant les travaux.</p>
        <ul class="hero-points">
          <li>{PIN} Chantiers visibles avant, pendant et après</li>
          <li>{PIN} Aucune surface habitable perdue</li>
          <li>{PIN} Un seul interlocuteur, de l'étude à la réception</li>
        </ul>
        <p class="hero-actions"><a class="btn btn-gold" href="#lp-form" data-cta="lp-hero" data-ab="cta" data-a="Demander mon étude gratuite" data-b="Recevoir mon étude gratuite">Demander mon étude gratuite{ARROW}</a></p>
      </div>
      <div class="lead" id="etude">
        <form id="lead-form" class="lp-form" novalidate action="/" method="post">
          <h2 id="lp-form">Demander mon étude gratuite</h2>
          <p class="lead-intro">Quatre questions, moins d'une minute.</p>
          <div class="field"><label for="lp-prenom">Prénom</label><input id="lp-prenom" name="prenom" type="text" autocomplete="given-name" required maxlength="60" aria-describedby="err-prenom"><span class="err" id="err-prenom"></span></div>
          <div class="field"><label for="lp-tel">Téléphone</label><input id="lp-tel" name="tel" type="tel" autocomplete="tel" inputmode="tel" required maxlength="20" aria-describedby="err-tel"><span class="err" id="err-tel"></span></div>
          <div class="field"><label for="lp-cp">Code postal</label><input id="lp-cp" name="cp" type="text" autocomplete="postal-code" inputmode="numeric" required maxlength="5" aria-describedby="err-cp"><span class="err" id="err-cp"></span></div>
          <fieldset class="choices-inline"><legend>Type de logement</legend>
            <label><input type="radio" name="logement" value="Maison individuelle" required> Maison individuelle</label>
            <label><input type="radio" name="logement" value="Maison de ville"> Maison de ville</label>
            <span class="err" id="err-logement" role="alert"></span>
          </fieldset>
          <label class="consent-check"><input type="checkbox" name="consentement" required> J'accepte d'être recontacté par Dominus Habitat au sujet de mon projet. <a href="/confidentialite.html">Politique de confidentialité</a>.<span class="err" id="err-consent"></span></label>
          <label class="visually-hidden" for="lp-website" aria-hidden="true">Ne pas remplir</label><input class="visually-hidden" id="lp-website" name="website" type="text" tabindex="-1" autocomplete="off" aria-hidden="true">
          <input type="hidden" name="utm_source"><input type="hidden" name="utm_medium"><input type="hidden" name="utm_campaign"><input type="hidden" name="utm_term"><input type="hidden" name="utm_content"><input type="hidden" name="gclid"><input type="hidden" name="fbclid"><input type="hidden" name="page_origine"><input type="hidden" name="variante">
          <button type="submit" class="btn btn-gold btn-block" data-ab="cta" data-a="Demander mon étude gratuite" data-b="Recevoir mon étude gratuite">Demander mon étude gratuite{ARROW}</button>
          <p class="err" id="err-envoi" role="alert"></p>
          <p class="consent">Sans engagement. Vos données ne sont ni vendues ni cédées.</p>
        </form>
        <div class="done" id="lead-done" hidden tabindex="-1" aria-live="polite">
          <h2>Merci, votre demande est bien reçue.</h2>
          <p>Un conseiller Dominus Habitat vous rappelle pour préparer votre étude gratuite.</p>
        </div>
      </div>
    </div>
  </div>
</div>
<section class="lp-chantiers" aria-labelledby="lp-ch">
  <div class="wrap">
    <p class="kicker">Nos réalisations</p>
    <h2 id="lp-ch">{esc(INTRO)}</h2>
    <p class="lede">{esc(REASSURANCE)}</p>
    {strip or '<p class="vide">Les photos de nos chantiers arrivent très prochainement.</p>'}
  </div>
</section>
<section class="alt lp-args" aria-labelledby="lp-args">
  <div class="wrap">
    <h2 id="lp-args">Pourquoi isoler par l'extérieur ?</h2>
    <div class="benefits">
      <div class="benefit"><h3>Une façade neuve et protégée</h3><p>L'isolant est recouvert d'un enduit de finition dont vous choisissez la teinte. Fissures et murs fatigués disparaissent.</p></div>
      <div class="benefit"><h3>Aucune surface perdue</h3><p>Tout se passe dehors : vos pièces gardent leur taille et vous continuez à vivre normalement pendant le chantier.</p></div>
      <div class="benefit"><h3>Un seul interlocuteur</h3><p>Étude, visite technique, déclaration en mairie, pose et réception : nous suivons votre chantier de bout en bout.</p></div>
    </div>
    <p class="hero-actions center"><a class="btn btn-gold" href="#lp-form" data-cta="lp-bas">Demander mon étude gratuite{ARROW}</a></p>
  </div>
</section>
"""
    out = out_root / "lp" / "isolation-exterieure" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    html_out = layout(index, title="Isolation thermique par l'extérieur : votre étude gratuite | Dominus Habitat", description="Façade neuve, maison qui garde sa chaleur, aucune surface perdue. Demandez votre étude gratuite et sans engagement.", canonical=f"{SITE}lp/isolation-exterieure/", body=body, robots="noindex, follow", body_attrs=' data-lp="isolation-exterieure"', light=True)
    html_out = html_out.replace('<a class="btn btn-gold" href="/#etude">Demander mon étude gratuite</a>', '<a class="btn btn-gold" href="#lp-form">Demander mon étude gratuite</a>').replace(CHANTIERS_JS, CHANTIERS_JS + LP_JS)
    out.write_text(html_out, encoding="utf-8")


def home_section(items):
    if not items:
        return ""
    return f"""<section id="realisations" aria-labelledby="real-title">
  <div class="wrap">
    <div class="section-head measure">
      <p class="kicker">Nos réalisations</p>
      <h2 id="real-title">{esc(INTRO)}</h2>
      <p class="lede">{esc(SOUS_TITRE)}</p>
    </div>
    {carousel(items[:3], "Nos réalisations : trois chantiers avant, pendant, après")}
    <p class="more"><span class="reassurance">{esc(REASSURANCE)}</span><a class="btn btn-line" href="/nos-chantiers/" data-cta="voir-realisations">Voir toutes nos réalisations{ARROW}</a></p>
  </div>
</section>
{LIGHTBOX}"""


def update_index(index, items):
    """Section d'accueil, lien d'en-tête et de pied de page, script du carrousel : tout entre marqueurs."""
    section = home_section(items)
    index = re.sub(r"<!-- chantiers:start -->.*?<!-- chantiers:end -->", "<!-- chantiers:start -->\n" + section + "\n<!-- chantiers:end -->", index, flags=re.S)
    if 'class="header-link"' not in index:
        index = index.replace('<a class="btn btn-gold header-cta" href="#etude">', '<a class="header-link" href="/nos-chantiers/">Nos chantiers</a>\n    <a class="btn btn-gold header-cta" href="#etude">', 1)
    if 'href="/nos-chantiers/">Nos chantiers</a></li>' not in index:
        index = index.replace('<li><a href="#faq">FAQ</a></li>\n        </ul>', '<li><a href="#faq">FAQ</a></li>\n          <li><a href="/nos-chantiers/">Nos chantiers</a></li>\n        </ul>', 1)
    index = re.sub(r"<!-- chantiers-js:start -->.*?<!-- chantiers-js:end -->", "<!-- chantiers-js:start -->\n" + (CHANTIERS_JS if items else "") + "\n<!-- chantiers-js:end -->", index, flags=re.S)
    return index


def write_sitemap(root, urls):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for loc, images in urls:
        lines.append(f"  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod>" + "".join(f"<image:image><image:loc>{u}</image:loc><image:title>{esc(t)}</image:title></image:image>" for u, t in images) + "</url>")
    lines.append("</urlset>")
    (root / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apercu", help="dossier de maquette incluant les chantiers non publiés (jamais mis en ligne)")
    args = ap.parse_args()
    apercu = bool(args.apercu)
    root = ROOT
    if apercu:
        root = pathlib.Path(args.apercu)
        if root.exists():
            shutil.rmtree(root)
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "chantiers", "tools", "node_modules"))

    chantiers = load()
    shown = [c for c in chantiers if c["_publiable"] or apercu]
    # Photos : traitées pour les chantiers affichés seulement
    for c in shown:
        c["_pictures"] = {}
        for step, _, _ in STEPS:
            c["_pictures"][step] = [process_photo(c, step, k + 1, p, root / "assets" / "chantiers" / c["slug"]) for k, p in enumerate(c["photos"].get(step, []))]
    shown.sort(key=lambda c: (c["departement"]["code"], c["reference"]), reverse=False)

    index = (ROOT / "index.html").read_text(encoding="utf-8")
    index = update_index(index, shown)
    (root / "index.html").write_text(index, encoding="utf-8")

    out_root = root / "nos-chantiers"
    if out_root.exists():
        shutil.rmtree(out_root)
    # Départements : page seulement à partir de 2 chantiers
    by_dept = {}
    for c in shown:
        by_dept.setdefault(c["dept_slug"], {"slug": c["dept_slug"], "nom": c["departement"]["nom"], "code": c["departement"]["code"], "items": []})["items"].append(c)
    dept_pages = sorted([d for d in by_dept.values() if len(d["items"]) >= 2], key=lambda d: d["code"])
    all_depts = sorted(by_dept.values(), key=lambda d: d["code"])

    urls = [(SITE, [])]
    pages_total = max(1, -(-len(shown) // PER_PAGE))
    for p in range(1, pages_total + 1):
        loc = page_liste(index, shown[(p - 1) * PER_PAGE : p * PER_PAGE], out_root, page=p, pages_total=pages_total, all_depts=all_depts, dept_pages=dept_pages)
        urls.append((loc, []))
    for d in dept_pages:
        loc = page_liste(index, d["items"], out_root / d["slug"], dept=d, all_depts=all_depts, dept_pages=dept_pages)
        urls.append((loc, []))
    for c in shown:
        page_fiche(index, c, shown, out_root)
        imgs = [(f"{SITE.rstrip('/')}{p['base']}-1200.jpg", p["alt"]) for step, _, _ in STEPS for p in c["_pictures"][step]]
        urls.append((SITE.rstrip("/") + c["url"], imgs))
    page_lp(index, [c for c in shown], root)
    write_sitemap(root, urls)

    # Rapport
    print(f"{len(shown)} chantier(s) affiché(s){' (APERÇU, avec les non publiés)' if apercu else ''}, {len(dept_pages)} page(s) de département, {pages_total} page(s) de liste.")
    for c in chantiers:
        if c["_manque"]:
            print(f"  - {c['slug']} : NON PUBLIÉ. Il manque : {', '.join(c['_manque'])}.")
    if not CERTIFICATIONS:
        print("  - Bloc de confiance des fiches : masqué (aucune certification avec preuve fournie).")
    if apercu:
        print(f"Maquette écrite dans {root} (ne jamais mettre en ligne).")


if __name__ == "__main__":
    main()

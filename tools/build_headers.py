"""Régénère _headers (Netlify / Cloudflare Pages) avec les empreintes CSP des <style> et <script> inline.

À relancer après toute modification d'un bloc <style> ou <script> :
    python3 tools/build_headers.py
"""
import base64, hashlib, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ["index.html", "mentions-legales.html", "confidentialite.html"]


def hashes(tag, html):
    out = []
    for m in re.finditer(rf"<{tag}(?![^>]*application/ld\+json)[^>]*>(.*?)</{tag}>", html, re.S):
        digest = hashlib.sha256(m.group(1).encode()).digest()
        out.append("'sha256-%s'" % base64.b64encode(digest).decode())
    return out


scripts, styles = [], []
for page in PAGES:
    html = (ROOT / page).read_text(encoding="utf-8")
    scripts += hashes("script", html)
    styles += hashes("style", html)

csp = "; ".join([
    "default-src 'self'",
    "script-src 'self' " + " ".join(sorted(set(scripts))) if scripts else "script-src 'self'",
    "style-src 'self' https://fonts.googleapis.com " + " ".join(sorted(set(styles))),
    "font-src https://fonts.gstatic.com",
    "img-src 'self' data:",
    # TODO : ajouter ici le domaine de l'endpoint d'envoi du formulaire (ex. https://api.exemple.fr)
    "connect-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "object-src 'none'",
    "upgrade-insecure-requests",
])

headers = f"""# Généré par tools/build_headers.py — ne pas éditer la CSP à la main.
/*
  Content-Security-Policy: {csp}
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), interest-cohort=()
  X-Frame-Options: DENY

/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*.html
  Cache-Control: public, max-age=0, must-revalidate
"""
(ROOT / "_headers").write_text(headers, encoding="utf-8")
print(headers)

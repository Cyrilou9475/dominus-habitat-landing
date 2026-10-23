"""Régénère _headers (Netlify / Cloudflare Pages) avec les empreintes CSP des <style> et <script> inline.

À relancer après toute modification d'un bloc <style> ou <script> :
    python3 tools/build_headers.py
"""
import base64, hashlib, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(str(f.relative_to(ROOT)) for f in ROOT.rglob("*.html") if ".git" not in f.parts and "node_modules" not in f.parts)


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
    # connect.facebook.net : Pixel Meta, chargé uniquement après consentement
    # www.googletagmanager.com : gtag (GA4 + Google Ads), chargé uniquement après consentement
    "script-src 'self' https://connect.facebook.net https://www.googletagmanager.com " + " ".join(sorted(set(scripts))),
    "style-src 'self' https://fonts.googleapis.com " + " ".join(sorted(set(styles))),
    "font-src https://fonts.gstatic.com",
    "img-src 'self' data: https://www.facebook.com https://www.googletagmanager.com https://*.google-analytics.com https://googleads.g.doubleclick.net https://www.google.com https://www.google.fr",
    # crm.dominusconsultancy.com : envoi des demandes d'étude au CRM Dominus (source « Formulaire web »)
    "connect-src 'self' https://www.facebook.com https://connect.facebook.net https://crm.dominusconsultancy.com https://www.googletagmanager.com https://*.google-analytics.com https://*.analytics.google.com https://googleads.g.doubleclick.net https://www.google.com",
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

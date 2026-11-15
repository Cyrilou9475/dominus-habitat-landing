// Vérification de la logique de consentement sans navigateur : on exécute le bloc « mesure »
// de la page générée dans un DOM minimal, puis on inspecte la file dataLayer.
import { readFileSync } from "node:fs";
import vm from "node:vm";

const page = new URL("../lp/isolation-exterieure/index.html", import.meta.url);
const html = readFileSync(page, "utf8");
const bloc = html.match(/<!-- mesure:start -->\s*<script>([\s\S]*?)<\/script>/)[1];

const champs = {};
const el = (name) => ({ get value() { return champs[name] ?? ""; }, set value(v) { champs[name] = v; }, getAttribute: () => null, querySelector: () => null });
const scripts = [];
const doc = {
  body: { dataset: { lp: "isolation-exterieure" } },
  head: { appendChild: (s) => scripts.push(s.src) },
  createElement: () => ({ set src(v) { this._src = v; }, get src() { return this._src; }, set async(v) {} }),
  querySelectorAll: (sel) => (sel === "form" ? [{ querySelector: (q) => el(q.match(/name="?([a-z_]+)"?/)[1]) }] : []),
  addEventListener: () => {},
};
const store = {};
const ctx = {
  console,
  document: doc,
  location: { search: "?gclid=TESTCLICK123&utm_source=google&utm_campaign=DH-Search-ITE", pathname: "/lp/isolation-exterieure/" },
  sessionStorage: { getItem: (k) => store[k] ?? null, setItem: (k, v) => (store[k] = v) },
  URLSearchParams,
  fetch: async () => ({ ok: true }),
  setTimeout, AbortController, Promise, Object, JSON, Array, Date, String, Error,
};
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(bloc, ctx);

const seq = () => (ctx.dataLayer || []).map((a) => Array.from(a));
const ok = [], ko = [];
const check = (n, c, d = "") => (c ? ok : ko).push(n + (c ? "" : " — " + d));

const avant = seq();
check("1. gclid récupéré dans le champ caché", champs.gclid === "TESTCLICK123", JSON.stringify(champs));
check("2. utm_campaign récupéré", champs.utm_campaign === "DH-Search-ITE");
check("3. consentement refusé par défaut (Consent Mode v2)",
  avant.some((e) => e[0] === "consent" && e[1] === "default" && e[2].ad_storage === "denied" && e[2].analytics_storage === "denied" && e[2].ad_user_data === "denied" && e[2].ad_personalization === "denied"));
check("4. ads_data_redaction activé (aucun identifiant sans accord)", avant.some((e) => e[0] === "set" && e[1] === "ads_data_redaction" && e[2] === true));
check("5. url_passthrough activé", avant.some((e) => e[0] === "set" && e[1] === "url_passthrough" && e[2] === true));
check("6. balise Google chargée dès l'arrivée (mode avancé)", scripts.some((s) => s.includes("googletagmanager.com/gtag/js")), JSON.stringify(scripts));
check("7. GA4 et Google Ads configurés sans attendre l'accord",
  avant.some((e) => e[0] === "config" && e[1] === "G-NKVJWQLPEW") && avant.some((e) => e[0] === "config" && e[1] === "AW-18575408445"));
check("8. conversions améliorées désactivées (téléphone jamais envoyé sans accord)",
  avant.find((e) => e[0] === "config" && e[1] === "AW-18575408445")[2].allow_enhanced_conversions === false);

// Le visiteur REFUSE tout, puis envoie le formulaire
const n0 = ctx.dataLayer.length;
ctx.dhOnConsent({ audience: false, ads: false });
ctx.dhLead({ logement: "maison", tel: "+33600000000" });
const apres = seq().slice(n0);
check("9. refus transmis à Google", apres.some((e) => e[0] === "consent" && e[1] === "update" && e[2].ad_storage === "denied"));
check("10. CONVERSION ENVOYÉE MALGRÉ LE REFUS (signal anonyme)",
  apres.some((e) => e[0] === "event" && e[1] === "conversion" && e[2].send_to === "AW-18575408445/wZC8CJC8xbgdEL36uJlF"), JSON.stringify(apres));
check("11. generate_lead envoyé malgré le refus", apres.some((e) => e[0] === "event" && e[1] === "generate_lead"));
check("12. aucun téléphone transmis à Google après refus", !apres.some((e) => e[0] === "set" && e[1] === "user_data"));
check("13. Pixel Meta non déclenché après refus", ctx.fbqAppele !== true);

// Le visiteur ACCEPTE : tout doit continuer de marcher
const n1 = ctx.dataLayer.length;
let fbq = 0; ctx.fbq = () => fbq++;
ctx.dhOnConsent({ audience: true, ads: true });
ctx.dhLead({ logement: "maison", tel: "+33600000000" });
const accepte = seq().slice(n1);
check("14. acceptation transmise à Google", accepte.some((e) => e[0] === "consent" && e[1] === "update" && e[2].ad_storage === "granted"));
check("15. conversion envoyée après acceptation", accepte.some((e) => e[0] === "event" && e[1] === "conversion"));
check("16. Pixel Meta déclenché seulement après acceptation", fbq === 1, "appels fbq : " + fbq);

console.log(ok.map((s) => "  OK  " + s).join("\n"));
if (ko.length) { console.log("\n" + ko.map((s) => "  KO  " + s).join("\n")); process.exit(1); }
console.log(`\n${ok.length} scénarios OK`);

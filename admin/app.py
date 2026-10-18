#!/usr/bin/env python3
"""
focalis.cc admin — switch active variant + WordPress-like admin bar
Listens on 0.0.0.0:8788, proxied by Caddy at /admin/*
Auth: HTTP Basic Auth + session cookie (form login). Bar uses cookie/session.
"""
import os
import hmac
import subprocess
import secrets
import base64
from pathlib import Path
from functools import wraps

from flask import Flask, request, Response, redirect, g, session, jsonify, make_response

# ---- config ----
ACTIVE_FILE = os.environ.get("ACTIVE_FILE", "/site/ACTIVE")
VARIANTS_DIR = os.environ.get("VARIANTS_DIR", "/site/variants")
ACTIVE_SYMLINK = os.path.join(VARIANTS_DIR, "active")
CREDENTIALS_FILE = os.environ.get("CREDENTIALS_FILE", "/app/.credentials")

ALLOWED_VARIANTS = {
    "variant-a-studio": {"label": "Studio", "title": "Focalis Studio", "sub": "Tools that stay out of the way", "color": "#7C5CFF", "bg": "#0A0A0B", "desc": "Minimal premium. Zinc+violet.", "preview": "/studio/"},
    "variant-b-labs":   {"label": "Labs",   "title": "Focalis Labs",   "sub": "Experiments you can ship",    "color": "#FF4D00", "bg": "#FFFBF5", "desc": "Bold, bento, experimental.", "preview": "/labs/"},
    "variant-c-systems":{"label": "Systems","title": "Focalis Systems","sub": "Infrastructure you can trust","color": "#0F2342", "bg": "#FFFFFF", "desc": "Enterprise, light, SLA-grade.", "preview": "/systems/"},
    "variant-d-world":  {"label": "World",  "title": "Focalis — World",  "sub": "Technology that gives time back", "color": "#2A7F6F", "bg": "#FAF6F1", "desc": "Human, warm, story-driven. No direct sales — studio showcase.", "preview": "/world/"},
}
VARIANT_ALIASES = {
    "studio": "variant-a-studio",
    "variant-a": "variant-a-studio",
    "labs": "variant-b-labs",
    "variant-b": "variant-b-labs",
    "systems": "variant-c-systems",
    "variant-c": "variant-c-systems",
    "world": "variant-d-world",
    "variant-d": "variant-d-world",
}

app = Flask(__name__)

# Secret for session cookies — persisted to avoid invalidating on restart
SECRET_FILE = os.environ.get("SECRET_FILE", "/app/.secret_key")
if os.environ.get("FLASK_SECRET"):
    app.secret_key = os.environ["FLASK_SECRET"]
elif Path(SECRET_FILE).exists():
    app.secret_key = Path(SECRET_FILE).read_text().strip()
else:
    sk = secrets.token_hex(32)
    Path(SECRET_FILE).write_text(sk)
    try:
        os.chmod(SECRET_FILE, 0o600)
    except Exception:
        pass
    app.secret_key = sk
    print(f"[admin] generated Flask secret -> {SECRET_FILE}", flush=True)

# ---- credentials ----
def load_or_create_credentials():
    env_user = os.environ.get("ADMIN_USER")
    env_pass = os.environ.get("ADMIN_PASS")
    if env_user and env_pass:
        print(f"[admin] using ADMIN_USER/ADMIN_PASS from env (user={env_user})", flush=True)
        return env_user, env_pass

    cred_path = Path(CREDENTIALS_FILE)
    if not cred_path.exists():
        alt = Path("/site/admin/.credentials")
        if alt.exists():
            cred_path = alt

    if cred_path.exists():
        try:
            text = cred_path.read_text()
            user = None
            pw = None
            for line in text.splitlines():
                line=line.strip()
                if line.startswith("ADMIN_USER="):
                    user=line.split("=",1)[1].strip()
                elif line.startswith("ADMIN_PASS="):
                    pw=line.split("=",1)[1].strip()
            if user and pw:
                print(f"[admin] loaded credentials from {cred_path} (user={user})", flush=True)
                return user, pw
        except Exception as e:
            print(f"[admin] failed to read {cred_path}: {e}", flush=True)

    user = env_user or "admin"
    pw = env_pass or base64.b64encode(secrets.token_bytes(9)).decode().rstrip("=").replace("/","+")[:12]
    if len(pw) < 12:
        pw = (pw + secrets.token_urlsafe(6))[:12]
    pw = pw.replace(":", "-").replace("\n","")
    cred_path.parent.mkdir(parents=True, exist_ok=True)
    cred_path.write_text(f"ADMIN_USER={user}\nADMIN_PASS={pw}\n")
    try:
        os.chmod(cred_path, 0o600)
    except Exception:
        pass
    print(f"[admin] GENERATED credentials user={user} pass={pw} -> saved to {cred_path} (chmod 600)", flush=True)
    print(f"[admin] *** ADMIN CREDENTIALS: user={user} password={pw} ***", flush=True)
    return user, pw

ADMIN_USER, ADMIN_PASS = load_or_create_credentials()

def check_basic(username, password):
    return hmac.compare_digest(username or "", ADMIN_USER) and hmac.compare_digest(password or "", ADMIN_PASS)

def is_authenticated():
    # 1) Flask session
    if session.get("admin_user") and session.get("admin_user") == ADMIN_USER:
        return True
    # 2) focalis_admin cookie is not sufficient alone — but check if valid session cookie? Use signed session.
    #    Also allow plain Basic Auth header
    auth = request.authorization
    if auth and check_basic(auth.username, auth.password):
        return True
    return False

def get_auth_user():
    if session.get("admin_user"):
        return session.get("admin_user")
    auth = request.authorization
    if auth and check_basic(auth.username, auth.password):
        return auth.username
    return None

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if is_authenticated():
            g.admin_user = get_auth_user() or ADMIN_USER
            return f(*args, **kwargs)
        # If client sent Basic Auth header and it failed, send 401
        if request.authorization:
            return Response("Authentication required", 401, {"WWW-Authenticate": 'Basic realm="focalis admin"'})
        # For browser navigation, redirect to login form
        # For API/fetch with Accept: json, maybe 401
        wants_json = request.headers.get("Accept","").find("application/json") != -1 or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if wants_json and request.path.startswith("/admin/status"):
            return jsonify({"authenticated": False})
        # Redirect to login
        return redirect(f"/admin/login?next={request.path}", code=302)
    return decorated

def get_active_variant():
    try:
        if os.path.exists(ACTIVE_FILE):
            v = Path(ACTIVE_FILE).read_text().strip()
            v = VARIANT_ALIASES.get(v, v)
            if v in ALLOWED_VARIANTS:
                return v
    except Exception:
        pass
    try:
        link = os.readlink(ACTIVE_SYMLINK)
        base = os.path.basename(link.rstrip("/"))
        base = VARIANT_ALIASES.get(base, base)
        if base in ALLOWED_VARIANTS:
            return base
    except Exception:
        pass
    return "variant-c-systems"

def set_active_variant(variant):
    variant = VARIANT_ALIASES.get(variant, variant)
    if variant not in ALLOWED_VARIANTS:
        raise ValueError(f"unknown variant {variant}")
    os.makedirs(VARIANTS_DIR, exist_ok=True)
    Path(ACTIVE_FILE).write_text(variant + "\n")
    try:
        subprocess.run(["ln", "-sfn", variant, ACTIVE_SYMLINK], check=True)
    except Exception as e:
        try:
            if os.path.islink(ACTIVE_SYMLINK) or os.path.exists(ACTIVE_SYMLINK):
                os.unlink(ACTIVE_SYMLINK)
        except Exception:
            pass
        os.symlink(variant, ACTIVE_SYMLINK)
        print(f"[admin] fallback symlink {variant} -> {ACTIVE_SYMLINK} ({e})", flush=True)
    print(f"[admin] switched active to {variant}", flush=True)
    return variant

# ---- contact form handling (public, no auth) ----
import json as _json
import time as _time
from datetime import datetime, timezone

# simple in-memory rate limit: {ip: [timestamps]}
_contact_hits = {}
_contact_notified_today = {"day": "", "n": 0}
_CONTACT_LOG = os.environ.get("CONTACT_LOG", "/site/logs/contact.jsonl")


def _contact_rate_ok(ip):
    """Three windows, because the endpoint sends real email to the owner's inbox.

    5/minute stops a scripted loop; 10/hour and 20/day stop a slow drip that would otherwise
    be 300 notifications an hour. A blocked request is rejected outright (the response says
    to retry), so nothing is silently dropped.
    """
    now = _time.time()
    hits = [t for t in _contact_hits.get(ip, []) if now - t < 86400]
    if len([t for t in hits if now - t < 60]) >= 5:
        _contact_hits[ip] = hits
        return False
    if len([t for t in hits if now - t < 3600]) >= 10:
        _contact_hits[ip] = hits
        return False
    if len(hits) >= 20:
        _contact_hits[ip] = hits
        return False
    hits.append(now)
    _contact_hits[ip] = hits
    return True


def _contact_notify_budget_ok(limit=100):
    """A global daily ceiling on *notifications* (not on saving leads)."""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _contact_notified_today.get("day") != day:
        _contact_notified_today.update({"day": day, "n": 0})
    if _contact_notified_today["n"] >= limit:
        return False
    _contact_notified_today["n"] += 1
    return True

def _send_email_via_smtp(to_addr, subject, body, reply_to=None):
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587") or "587")
    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASS")
    from_addr = os.environ.get("SMTP_FROM") or user or "noreply@focalis.cc"
    if not host or not user or not pw:
        return False, "SMTP not configured (set SMTP_HOST/USER/PASS)"
    try:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        if reply_to:
            msg["Reply-To"] = reply_to
        with smtplib.SMTP(host, port, timeout=10) as s:
            # try STARTTLS if port 587
            try:
                s.starttls()
            except Exception:
                pass
            s.login(user, pw)
            s.sendmail(from_addr, [to_addr], msg.as_string())
        return True, "sent"
    except Exception as e:
        print(f"[contact] SMTP send failed: {e}", flush=True)
        return False, str(e)

def _send_email_via_agentmail(to_addr, subject, body, reply_to=None):
    """Send through the branded AgentMail inbox (focalis@agentmail.to).

    SMTP is optional and was never configured, which meant a contact-form submission was
    written to logs/contact.jsonl and nobody was told. This is the leg that actually
    notifies: AgentMail's HTTP API with the key we already hold. A copy is kept in the
    agent inbox (bcc) so an agent can read and answer the lead without the owner's mailbox.
    """
    key = os.environ.get("AGENTMAIL_API_KEY")
    sender = os.environ.get("AGENTMAIL_FROM", "focalis@agentmail.to")
    if not key:
        return False, "AGENTMAIL_API_KEY not configured"
    payload = {"to": to_addr, "subject": subject, "text": body}
    if reply_to:
        payload["reply_to"] = reply_to
    copy = os.environ.get("AGENTMAIL_BCC", "")
    if copy:
        payload["bcc"] = copy
    try:
        import urllib.request
        req = urllib.request.Request(
            f"https://api.agentmail.to/v0/inboxes/{sender}/messages/send",
            data=_json.dumps(payload).encode(), method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            _json.loads(r.read().decode() or "{}")
        return True, "sent"
    except Exception as e:  # noqa: BLE001
        print(f"[contact] AgentMail send failed: {e}", flush=True)
        return False, str(e)


# ---- routes ----

@app.route("/admin/health", methods=["GET"])
def health():
    return "ok", 200

@app.route("/admin/status", methods=["GET"])
def status():
    active = get_active_variant()
    authed = is_authenticated()
    user = get_auth_user() if authed else None
    resp = jsonify({"authenticated": authed, "active": active, "user": user, "variants": list(ALLOWED_VARIANTS.keys())})
    # CORS not needed (same origin), but allow credentials
    return resp

@app.route("/admin/bar.js", methods=["GET"])
def bar_js():
    # public JS, no auth required — fetches /admin/status
    js = r"""
(function(){
  try{
    fetch('/admin/status', {credentials:'include', headers:{'Accept':'application/json'}})
      .then(function(r){ return r.json(); })
      .then(function(data){
        if(!data || !data.authenticated) return;
        var active = data.active || 'unknown';
        var labels = { 'variant-a-studio':'Studio','variant-b-labs':'Labs','variant-c-systems':'Systems','variant-d-world':'World' };
        var colors = { 'variant-a-studio':'#7C5CFF','variant-b-labs':'#FF4D00','variant-c-systems':'#0F2342','variant-d-world':'#2A7F6F' };
        if(document.getElementById('focalis-admin-bar')) return;
        var bar = document.createElement('div');
        bar.id = 'focalis-admin-bar';
        bar.style.cssText = 'position:fixed;top:0;left:0;right:0;height:32px;background:#0B0B0F;color:#E5E7EB;z-index:99999;display:flex;align-items:center;gap:10px;padding:0 12px;font-family:Inter,system-ui,sans-serif;font-size:12px;line-height:1;border-bottom:1px solid #1F1F23;box-shadow:0 1px 6px rgba(0,0,0,0.35);';
        var dot = colors[active] || '#7C5CFF';
        bar.innerHTML = ''
          + '<a href="/admin/" style="display:flex;align-items:center;gap:8px;text-decoration:none;color:#fff;font-weight:700;">'
          + '<span style="width:20px;height:20px;border-radius:6px;background:#fff;color:#000;display:grid;place-items:center;font-weight:900;font-size:11px;">F</span>'
          + '<span>focalis.cc</span><span style="font-weight:500;color:#9CA3AF;">Admin</span></a>'
          + '<span style="width:1px;height:16px;background:#2A2A2E;display:inline-block;"></span>'
          + '<span style="display:flex;align-items:center;gap:6px;">'
          + '<span style="width:8px;height:8px;border-radius:999px;background:'+dot+';display:inline-block;"></span>'
          + '<span style="color:#9CA3AF;">LIVE:</span><span style="color:#fff;font-weight:600;">'+(labels[active]||active)+'</span>'
          + '<span style="color:#6B7280;font-family:JetBrains Mono,monospace;font-size:11px;">'+active+'</span></span>'
          + '<span style="width:1px;height:16px;background:#2A2A2E;display:inline-block;"></span>'
          + '<span style="display:flex;align-items:center;gap:6px;">'
          + '<button data-v="variant-a-studio" style="padding:4px 8px;border-radius:999px;border:1px solid '+(active==='variant-a-studio'?'#7C5CFF':'#2A2A2E')+';background:'+(active==='variant-a-studio'?'#7C5CFF':'transparent')+';color:'+(active==='variant-a-studio'?'#fff':'#D1D5DB')+';font-size:11px;font-weight:600;cursor:pointer;">Studio</button>'
          + '<button data-v="variant-b-labs" style="padding:4px 8px;border-radius:999px;border:1px solid '+(active==='variant-b-labs'?'#FF4D00':'#2A2A2E')+';background:'+(active==='variant-b-labs'?'#FF4D00':'transparent')+';color:'+(active==='variant-b-labs'?'#fff':'#D1D5DB')+';font-size:11px;font-weight:600;cursor:pointer;">Labs</button>'
          + '<button data-v="variant-c-systems" style="padding:4px 8px;border-radius:999px;border:1px solid '+(active==='variant-c-systems'?'#0F2342':'#2A2A2E')+';background:'+(active==='variant-c-systems'?'#0F2342':'transparent')+';color:'+(active==='variant-c-systems'?'#fff':'#D1D5DB')+';font-size:11px;font-weight:600;cursor:pointer;">Systems</button>'
          + '<button data-v="variant-d-world" style="padding:4px 8px;border-radius:999px;border:1px solid '+(active==='variant-d-world'?'#2A7F6F':'#2A2A2E')+';background:'+(active==='variant-d-world'?'#2A7F6F':'transparent')+';color:'+(active==='variant-d-world'?'#fff':'#D1D5DB')+';font-size:11px;font-weight:600;cursor:pointer;">World</button>'
          + '</span>'
          + '<span style="margin-left:auto;display:flex;align-items:center;gap:8px;">'
          + '<a href="/studio/" style="color:#9CA3AF;text-decoration:none;">Preview: /studio/</a>'
          + '<a href="/labs/" style="color:#9CA3AF;text-decoration:none;">/labs/</a>'
          + '<a href="/systems/" style="color:#9CA3AF;text-decoration:none;">/systems/</a>'
          + '<a href="/world/" style="color:#9CA3AF;text-decoration:none;">/world/</a>'
          + '<a href="/selector/" style="color:#9CA3AF;text-decoration:none;border-left:1px solid #2A2A2E;padding-left:8px;margin-left:4px;">Selector</a>'
          + '<a href="/admin/" style="color:#fff;text-decoration:none;background:#1F1F23;border:1px solid #2A2A2E;padding:4px 8px;border-radius:6px;">Dashboard</a>'
          + '<a href="/admin/logout" style="color:#F87171;text-decoration:none;padding:4px 6px;">Logout</a>'
          + '</span>';
        document.documentElement.style.scrollPaddingTop = '32px';
        document.body.style.paddingTop = '32px';
        document.body.insertBefore(bar, document.body.firstChild);
        bar.querySelectorAll('button[data-v]').forEach(function(btn){
          btn.addEventListener('click', function(){
            var v = btn.getAttribute('data-v');
            btn.textContent = '…';
            fetch('/admin/switch', {method:'POST', credentials:'include', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:'variant='+encodeURIComponent(v)})
              .then(function(r){ if(r.redirected){ window.location.href=r.url; } else if(r.ok){ window.location.reload(); } else { alert('Switch failed'); btn.textContent=v; }})
              .catch(function(){ alert('Network error'); });
          });
        });
      })
      .catch(function(){});
  }catch(e){}
})();
"""
    resp = make_response(js)
    resp.headers["Content-Type"] = "application/javascript; charset=utf-8"
    resp.headers["Cache-Control"] = "no-cache"
    return resp

@app.route("/admin/login", methods=["GET"])
def login_page():
    if is_authenticated():
        return redirect("/admin/", code=302)
    nxt = request.args.get("next", "/admin/")
    err = request.args.get("err", "")
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>focalis.cc — Login</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>*{{font-family:Inter,sans-serif}}</style>
</head>
<body class="min-h-screen bg-[#FCFCF9] grid place-items-center p-6">
<div class="w-full max-w-sm rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
  <div class="flex items-center gap-3 mb-6">
    <div class="w-8 h-8 rounded-lg bg-zinc-900 text-white grid place-items-center font-black text-sm">F</div>
    <div><div class="font-semibold">focalis.cc — Admin</div><div class="text-xs text-zinc-500">Sign in to manage live variant</div></div>
  </div>
  {'<div class="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">'+err+'</div>' if err else ''}
  <form method="POST" action="/admin/login" class="space-y-4">
    <input type="hidden" name="next" value="{nxt}"/>
    <div><label class="text-xs font-semibold text-zinc-700">Username</label><input name="username" autofocus required class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900" placeholder="admin"/></div>
    <div><label class="text-xs font-semibold text-zinc-700">Password</label><input name="password" type="password" required class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"/></div>
    <button type="submit" class="w-full rounded-xl bg-zinc-900 text-white py-2.5 text-sm font-semibold hover:bg-black">Sign in →</button>
  </form>
  <div class="mt-4 text-xs text-zinc-500">Basic Auth also works: <span class="font-mono">curl -u admin:…</span>. Credentials: <code class="bg-zinc-100 px-1 rounded">{CREDENTIALS_FILE}</code></div>
</div>
</body></html>"""
    return Response(html, mimetype="text/html")

@app.route("/admin/login", methods=["POST"])
def login_post():
    username = request.form.get("username","").strip()
    password = request.form.get("password","")
    nxt = request.form.get("next","/admin/") or "/admin/"
    # allow only same-origin next
    if not nxt.startswith("/"):
        nxt = "/admin/"
    if check_basic(username, password):
        session["admin_user"] = username
        session.permanent = True
        resp = make_response(redirect(nxt, code=303))
        # also set plain cookie for JS quick check (not HttpOnly)
        resp.set_cookie("focalis_admin", "1", httponly=False, samesite="Lax", path="/", max_age=30*24*3600)
        print(f"[admin] login success user={username} -> {nxt}", flush=True)
        return resp
    print(f"[admin] login failed user={username}", flush=True)
    return redirect(f"/admin/login?err=Invalid+credentials&next={nxt}", code=303)

@app.route("/admin/logout", methods=["GET","POST"])
def logout():
    session.clear()
    resp = make_response(redirect("/admin/login", code=303))
    resp.delete_cookie("focalis_admin", path="/")
    return resp

@app.route("/admin", methods=["GET"])
def admin_no_slash():
    return redirect("/admin/", code=308)

@app.route("/admin/", methods=["GET"])
@requires_auth
def dashboard():
    active = get_active_variant()
    msg = request.args.get("msg", "")
    err = request.args.get("err", "")

    cards_html = ""
    for vid, meta in ALLOWED_VARIANTS.items():
        is_active = (vid == active)
        badge = '<span class="ml-2 inline-flex items-center gap-1.5 text-[11px] font-bold tracking-widest uppercase px-2 py-1 rounded-full bg-emerald-500 text-white">● ACTIVE</span>' if is_active else ""
        border = "border-emerald-500 ring-1 ring-emerald-500/20" if is_active else "border-zinc-200 hover:border-zinc-300"
        btn_label = "Current ✓" if is_active else "Make Active →"
        btn_disabled = "disabled opacity-50 cursor-not-allowed" if is_active else "hover:bg-zinc-900 hover:text-white"
        btn_extra = "disabled" if is_active else ""
        preview_iframe = f'<iframe src="{meta["preview"]}" class="w-full h-[160px] border-0 bg-white" loading="lazy" title="{meta["title"]} preview"></iframe>'
        cards_html += f"""
        <div class="rounded-2xl border {border} bg-white overflow-hidden flex flex-col">
          <div class="h-1.5" style="background:{meta["color"]}"></div>
          <div class="p-5 flex-1 flex flex-col">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full" style="background:{meta["color"]}"></span>
              <span class="text-[11px] tracking-widest font-semibold text-zinc-500">VARIANT {meta["label"].upper()}</span>
              {badge}
            </div>
            <h3 class="mt-3 text-lg font-bold tracking-tight text-zinc-900">{meta["title"]}</h3>
            <p class="text-xs font-medium" style="color:{meta["color"]}">{meta["sub"]}</p>
            <p class="mt-2 text-sm text-zinc-600 leading-relaxed">{meta["desc"]}</p>
            <div class="mt-4 rounded-xl overflow-hidden border border-zinc-200 bg-zinc-50">
              {preview_iframe}
            </div>
            <div class="mt-4 flex items-center gap-2 text-xs">
              <a href="{meta["preview"]}" target="_blank" class="px-3 py-1.5 rounded-full border border-zinc-200 text-zinc-700 hover:bg-zinc-50">Preview {meta["preview"]} ↗</a>
              <span class="text-zinc-400 font-mono text-[11px]">{vid}</span>
            </div>
            <form method="POST" action="/admin/switch" class="mt-4">
              <input type="hidden" name="variant" value="{vid}"/>
              <button type="submit" {btn_extra} class="w-full inline-flex justify-center items-center gap-2 px-4 py-2.5 rounded-xl border border-zinc-900 text-sm font-semibold bg-white text-zinc-900 {btn_disabled} transition">
                {btn_label}
              </button>
            </form>
          </div>
        </div>
        """

    alert = ""
    if msg:
        alert = f'<div class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">✓ {msg}</div>'
    if err:
        alert = f'<div class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">✗ {err}</div>'

    active_meta = ALLOWED_VARIANTS.get(active, {})
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>focalis.cc — Admin</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>*{{font-family:Inter,sans-serif}} .mono{{font-family:'JetBrains Mono',monospace}}</style>
</head>
<body class="min-h-screen bg-[#FCFCF9] text-zinc-900">
<header class="border-b border-zinc-200 bg-white/80 backdrop-blur sticky top-0 z-10">
  <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-zinc-900 text-white grid place-items-center font-black text-sm">F</div>
      <div>
        <div class="font-semibold tracking-tight leading-none">focalis.cc — Admin</div>
        <div class="mono text-xs text-zinc-500">variant switcher · /admin</div>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <span class="mono text-xs text-zinc-500 hidden sm:inline">user: {g.admin_user}</span>
      <a href="/admin/logout" class="mono text-xs px-3 py-1.5 rounded-full border border-zinc-200 text-zinc-600 hover:bg-zinc-50">Logout</a>
      <a href="/selector/" class="text-sm font-medium text-zinc-600 hover:text-zinc-900">Selector →</a>
      <a href="/" class="text-sm font-medium px-3 py-1.5 rounded-full bg-zinc-900 text-white">Live site →</a>
    </div>
  </div>
</header>

<main class="max-w-6xl mx-auto px-6 py-8">
  <div class="flex flex-wrap items-start justify-between gap-4 mb-6">
    <div>
      <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight">Choose the live variant</h1>
      <p class="mt-2 text-zinc-600 max-w-2xl">The apex <span class="mono text-xs bg-zinc-100 border border-zinc-200 px-1.5 py-0.5 rounded">focalis.cc /</span> is served from <span class="mono text-xs bg-zinc-900 text-white px-1.5 py-0.5 rounded">/srv/active → {active}</span>. Switch is instant (symlink + ACTIVE file). Previews stay at <span class="mono text-xs">/studio/</span> <span class="mono text-xs">/labs/</span> <span class="mono text-xs">/systems/</span> and <span class="mono text-xs">/selector/</span>.</p>
    </div>
    <div class="rounded-2xl border border-zinc-200 bg-white px-5 py-4 min-w-[280px]">
      <div class="mono text-[11px] tracking-widest font-semibold text-zinc-500">CURRENT ACTIVE</div>
      <div class="mt-1 font-bold text-lg" style="color:{active_meta.get('color','#111')}">{active_meta.get('title', active)}</div>
      <div class="mono text-xs text-zinc-500">{active}</div>
      <div class="mono text-xs text-zinc-400 mt-1">ACTIVE: {ACTIVE_FILE}</div>
      <div class="mono text-xs text-zinc-400">symlink: {ACTIVE_SYMLINK} → {active}</div>
    </div>
  </div>

  {alert}

  <div class="mt-6 grid md:grid-cols-3 gap-5">
    {cards_html}
  </div>

  <div class="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
    <h2 class="font-semibold text-sm text-amber-900">✦ Site Config — no developer needed</h2>
    <p class="mono text-xs text-amber-800 mt-1">Change emails, company name, location and tagline without editing code. <a href="/admin/config" class="underline font-semibold">Open /admin/config →</a> — saves to <code>site.config.json</code> + <code>site.config.private.json</code> (gitignored) + regenerates <code>assets/js/site-config.js</code> and syncs HTML fallback.</p>
    <div class="mt-2 flex gap-2">
      <a href="/admin/config" class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-900 text-white text-xs font-semibold hover:bg-black">Edit Site Config →</a>
      <a href="/api/site-config" class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-zinc-300 bg-white text-xs">View /api/site-config</a>
      <a href="/admin/contacts" class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-zinc-300 bg-white text-xs">View Contacts</a>
    </div>
  </div>

  <div class="mt-4 rounded-xl border border-zinc-200 bg-white p-4">
    <h2 class="font-semibold text-sm">How it works &amp; Admin bar</h2>
    <ul class="mt-2 mono text-xs text-zinc-600 space-y-1 list-disc pl-4">
      <li>POST /admin/switch writes <code>{ACTIVE_FILE}</code> and runs <code>ln -sfn &lt;variant&gt; {ACTIVE_SYMLINK}</code>.</li>
      <li>Caddy <code>root * /srv/active</code> follows symlink — no reload needed.</li>
      <li>Credentials: <code>{CREDENTIALS_FILE}</code> (600, gitignored). Override via <code>ADMIN_USER</code>/<code>ADMIN_PASS</code> env.</li>
      <li>Admin bar: include <code>&lt;script src="/admin/bar.js"&gt;&lt;/script&gt;</code> on every variant page. When logged in, it shows a WP-like top bar with quick switch.</li>
      <li>Auth: form login at <a href="/admin/login" class="underline">/admin/login</a> sets session + <code>focalis_admin=1</code> cookie. Basic Auth also works.</li>
      <li>Health: <a href="/admin/health" class="underline">/admin/health</a> (no auth), <a href="/health" class="underline">/health</a> via Caddy.</li>
    </ul>
  </div>

  <div class="mt-6 mono text-xs text-zinc-400">
    <span>Live: <a href="/" class="underline hover:text-zinc-600">/</a> · </span>
    <span>Selector: <a href="/selector/" class="underline hover:text-zinc-600">/selector/</a> · </span>
    <span>Previews: <a href="/studio/" class="underline">/studio/</a> <a href="/labs/" class="underline">/labs/</a> <a href="/systems/" class="underline">/systems/</a></span>
  </div>
</main>
<script src="/admin/bar.js"></script>
</body>
</html>"""
    return Response(html, mimetype="text/html")

@app.route("/admin/switch", methods=["POST"])
@requires_auth
def switch():
    variant = request.form.get("variant", "").strip()
    if not variant and request.is_json:
        variant = (request.get_json(silent=True) or {}).get("variant","").strip()
    # also accept query
    if not variant:
        variant = request.args.get("variant","").strip()
    if not variant:
        # for fetch API with JSON body fallback
        try:
            body = request.get_data(as_text=True)
            if "variant" in body:
                import urllib.parse
                qs = urllib.parse.parse_qs(body)
                if "variant" in qs:
                    variant = qs["variant"][0]
        except Exception:
            pass
    if not variant:
        return redirect("/admin/?err=Missing+variant", code=303)
    normalized = VARIANT_ALIASES.get(variant, variant)
    if normalized not in ALLOWED_VARIANTS:
        return redirect(f"/admin/?err=Unknown+variant+{variant}", code=303)
    try:
        set_active_variant(normalized)
        # if fetch (Accept json) return json
        if request.headers.get("Accept","").find("application/json") != -1 or request.headers.get("X-Requested-With") == "fetch":
            return jsonify({"ok": True, "active": normalized})
        return redirect(f"/admin/?msg=Switched+to+{normalized}+✓", code=303)
    except Exception as e:
        if request.headers.get("Accept","").find("application/json") != -1:
            return jsonify({"ok": False, "error": str(e)}), 400
        return redirect(f"/admin/?err={str(e)}", code=303)

@app.route("/admin/switch", methods=["GET"])
@requires_auth
def switch_get():
    return redirect("/admin/", code=302)

@app.route("/api/contact", methods=["POST", "OPTIONS"])
@app.route("/api/contact/", methods=["POST", "OPTIONS"])
def api_contact():
    # CORS preflight
    if request.method == "OPTIONS":
        r = make_response("", 204)
        r.headers["Access-Control-Allow-Origin"] = "*"
        r.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        r.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return r
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    if not _contact_rate_ok(ip):
        return jsonify({"ok": False, "error": "Too many requests, please wait a minute"}), 429
    # support both JSON and form-encoded
    data = {}
    if request.is_json:
        try:
            data = request.get_json(force=True) or {}
        except Exception:
            data = {}
    else:
        data = request.form.to_dict()
        if not data:
            try:
                data = _json.loads(request.get_data(as_text=True) or "{}")
            except Exception:
                pass
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or data.get("msg") or "").strip()
    honey = (data.get("website") or data.get("_honey") or "").strip()  # honeypot
    if honey:
        return jsonify({"ok": False, "error": "Spam detected"}), 400
    if not name or len(name) < 2:
        return jsonify({"ok": False, "error": "Please enter your name (at least 2 characters)"}), 400
    if not email or "@" not in email or "." not in email:
        return jsonify({"ok": False, "error": "Please enter a valid email"}), 400
    if not message or len(message) < 10:
        return jsonify({"ok": False, "error": "Please write a message (at least 10 characters)"}), 400
    if len(message) > 5000:
        return jsonify({"ok": False, "error": "Message too long (max 5000 chars)"}), 400
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ip": ip,
        "ua": request.headers.get("User-Agent", "")[:200],
        "name": name[:100],
        "email": email[:200],
        "message": message[:5000],
    }
    # persist
    try:
        p = Path(_CONTACT_LOG)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(_json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[contact] {entry['ts']} {name} <{email}> ip={ip} len={len(message)}", flush=True)
    except Exception as e:
        print(f"[contact] log failed: {e}", flush=True)
        return jsonify({"ok": False, "error": "Failed to save message"}), 500
    # try email if configured
    dest = os.environ.get("CONTACT_TO", "hello@focalis.cc")
    subj = f"[focalis.cc] Contact from {name}"
    body = f"From: {name} <{email}>\nIP: {ip}\nTime: {entry['ts']}\n\n{message}\n\n---\nUser-Agent: {entry['ua']}"
    emailed = False
    email_err = None
    if not _contact_notify_budget_ok():
        email_err = "daily notification ceiling reached; lead saved, not emailed"
        print(f"[contact] {email_err}", flush=True)
    elif os.environ.get("SMTP_HOST"):
        ok, info = _send_email_via_smtp(dest, subj, body, reply_to=email)
        emailed, email_err = ok, (info if not ok else None)
    elif os.environ.get("AGENTMAIL_API_KEY"):
        ok, info = _send_email_via_agentmail(dest, subj, body, reply_to=email)
        emailed, email_err = ok, (info if not ok else None)
        # the log stays the source of truth even when the notification fails
        print(f"[contact] notified={emailed} via agentmail ({info})", flush=True)
    else:
        email_err = "no mail leg configured (set AGENTMAIL_API_KEY or SMTP_HOST)"
        print(f"[contact] LEAD SAVED BUT NOT NOTIFIED: {email_err}", flush=True)
    resp = jsonify({"ok": True, "message": "Message received — we'll reply within 24h", "emailed": emailed, "error_email": email_err})
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

@app.route("/api/contact", methods=["GET"])
def api_contact_info():
    return jsonify({"ok": True, "info": "POST JSON {name,email,message} to this endpoint",
                    "log": _CONTACT_LOG,
                    "smtp_configured": bool(os.environ.get("SMTP_HOST")),
                    "notify_sender": os.environ.get("AGENTMAIL_FROM", "") if os.environ.get("AGENTMAIL_API_KEY") else "",
                    "notify_configured": bool(os.environ.get("AGENTMAIL_API_KEY") or os.environ.get("SMTP_HOST"))})

@app.route("/admin/contacts", methods=["GET"])
@requires_auth
def admin_contacts():
    # simple viewer for stored contacts
    entries = []
    try:
        p = Path(_CONTACT_LOG)
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines()[-100:]:
                try:
                    entries.append(_json.loads(line))
                except Exception:
                    continue
            entries = list(reversed(entries))
    except Exception as e:
        entries = [{"error": str(e)}]
    html = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Contacts — focalis.cc</title><script src='https://cdn.tailwindcss.com'></script></head><body class='bg-[#FCFCF9] p-6'><div class='max-w-3xl mx-auto'><a href='/admin/' class='text-sm underline'>← Admin</a><h1 class='text-2xl font-bold mt-4'>Contact messages ({len(entries)})</h1><p class='mono text-xs text-zinc-500'>Log: {_CONTACT_LOG} · SMTP: {'yes' if os.environ.get('SMTP_HOST') else 'no (logging only)'}</p><div class='mt-6 space-y-3'>"""
    if not entries:
        html += "<div class='border border-zinc-200 bg-white rounded-xl p-6 text-sm text-zinc-500'>No messages yet.</div>"
    for e in entries:
        html += f"""<div class='border border-zinc-200 bg-white rounded-xl p-4'><div class='flex justify-between gap-4'><span class='font-semibold text-sm'>{e.get('name','?')} &lt;{e.get('email','?')}&gt;</span><span class='mono text-xs text-zinc-500'>{e.get('ts','')}</span></div><div class='mono text-xs text-zinc-400'>IP {e.get('ip','')} · {e.get('ua','')[:80]}</div><pre class='mt-2 whitespace-pre-wrap text-sm bg-zinc-50 border border-zinc-100 rounded-lg p-3'>{e.get('message','')[:2000]}</pre></div>"""
    html += "</div></div></body></html>"""
    return Response(html, mimetype="text/html")

# ---- site config editor (admin-only, no developer needed) ----
def _site_config_paths(variant=None):
    v = variant or get_active_variant()
    # prefer variant-d-world if it exists, else active
    base = Path(VARIANTS_DIR) / "variant-d-world"
    if not base.exists():
        base = Path(VARIANTS_DIR) / v
    j = base / "site.config.json"
    js = base / "assets" / "js" / "site-config.js"
    priv = base / "site.config.private.json"
    return j, js, priv, base

def _load_site_config():
    j, js, priv, base = _site_config_paths()
    cfg = {"site":{},"company":{},"contact":{},"private":{}}
    if j.exists():
        try:
            cfg.update(_json.loads(j.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"[config] load failed {j}: {e}", flush=True)
    if priv.exists():
        try:
            pj = _json.loads(priv.read_text(encoding="utf-8"))
            cfg["private"] = {**cfg.get("private",{}), **pj.get("private",{})}
            if "forwardTo" in pj.get("private",{}):
                cfg["private"]["forwardTo"] = pj["private"]["forwardTo"]
            if "forwardTo" in pj:
                cfg["private"]["forwardTo"] = pj["forwardTo"]
        except Exception as e:
            print(f"[config] private load failed {priv}: {e}", flush=True)
    return cfg, j, js, priv, base

def _save_site_config(data):
    j, js, priv, base = _site_config_paths()
    # public part -> site.config.json (never store private forwardTo there, keep CHANGEME)
    public = {"site": data.get("site",{}), "company": data.get("company",{}), "contact": data.get("contact",{}), "private": {"_comment": "NOT public - set via gitignored file. See site.config.private.json", "forwardTo": "CHANGEME@gmail.com", "smtpUser": data.get("contact",{}).get("primaryEmail","hello@focalis.cc")}, "meta": {"configVersion": 1, "lastUpdated": datetime.now(timezone.utc).isoformat()}}
    base.mkdir(parents=True, exist_ok=True)
    (base / "assets" / "js").mkdir(parents=True, exist_ok=True)
    j.write_text(_json.dumps(public, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    # private part -> site.config.private.json (gitignored, chmod 600)
    fwd = (data.get("private",{}).get("forwardTo") or "").strip()
    if fwd and fwd != "CHANGEME@gmail.com":
        priv.write_text(_json.dumps({"private": {"forwardTo": fwd}, "_warning": "This file contains private personal email. It is gitignored and NEVER pushed to GitHub."}, indent=2)+"\n", encoding="utf-8")
        try: os.chmod(priv, 0o600)
        except Exception: pass
    # Generate assets/js/site-config.js from public + private (private not injected to HTML, only for backend)
    js_content = f"""/**\n * Focalis — site config (generated by /admin/config — no developer needed)\n * Source: site.config.json (public values only — the private forwardTo never leaves the server)\n * Generated: {{datetime.now(timezone.utc).isoformat()}}\n */\nwindow.FOCALIS_CONFIG = {_json.dumps({"site": public["site"], "company": public["company"], "contact": public["contact"]}, indent=2, ensure_ascii=False)};\n(function(){{\n  if (typeof document === 'undefined') return;\n  function get(path){{ return path.split('.').reduce((o,k)=>o&&o[k], window.FOCALIS_CONFIG); }}\n  function apply(){{\n    document.querySelectorAll('[data-config]').forEach(el=>{{\n      const v=get(el.getAttribute('data-config')); if(v){{\n        if(el.tagName==='A' && el.getAttribute('href')?.startsWith('mailto:')) el.href='mailto:'+v;\n        el.textContent=v;\n      }}\n    }});\n    document.querySelectorAll('[data-config-href]').forEach(el=>{{ const v=get(el.getAttribute('data-config-href')); if(v) el.href='mailto:'+v; }});\n  }}\n  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', apply); else apply();\n}})();\n"""
    js.write_text(js_content, encoding="utf-8")
    # Also sync HTML fallback text for crawlers (so no-JS still shows new email)
    try:
        for html_file in base.glob("*.html"):
            txt = html_file.read_text(encoding="utf-8")
            import re
            primary = public["contact"].get("primaryEmail","")
            support = public["contact"].get("supportEmail","")
            legal = public["company"].get("legalName","")
            loc = public["company"].get("location","")
            if primary:
                txt = re.sub(r'(data-config="contact\.primaryEmail"[^>]*>)[^<]+</a>', r'\g<1>'+primary+'</a>', txt)
            if support:
                txt = re.sub(r'(data-config="contact\.supportEmail"[^>]*>)[^<]+</a>', r'\g<1>'+support+'</a>', txt)
            if legal:
                txt = re.sub(r'(data-config="company\.legalName">)[^<]+</span>', r'\g<1>'+legal+'</span>', txt)
            if loc:
                txt = re.sub(r'(data-config="company\.location">)[^<]+</span>', r'\g<1>'+loc+'</span>', txt)
            html_file.write_text(txt, encoding="utf-8")
        print(f"[config] saved {j} + {js} + synced HTML", flush=True)
    except Exception as e:
        print(f"[config] HTML sync failed: {e}", flush=True)
    return public, fwd

@app.route("/admin/config", methods=["GET"])
@requires_auth
def admin_config_get():
    cfg, j, js, priv, base = _load_site_config()
    msg = request.args.get("msg","")
    err = request.args.get("err","")
    def v(path, default=""):
        cur = cfg
        for k in path.split("."):
            cur = cur.get(k,{}) if isinstance(cur, dict) else default
        return cur if isinstance(cur, str) else default
    alert=""
    if msg:
        alert=f'<div class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{msg}</div>'
    if err:
        alert=f'<div class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{err}</div>'
    html=f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Site Config — focalis.cc</title><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"><style>*{{font-family:Inter,sans-serif}} .mono{{font-family:'JetBrains Mono',monospace}}</style></head><body class="min-h-screen bg-[#FCFCF9]">
<header class="border-b border-zinc-200 bg-white/80 backdrop-blur sticky top-0 z-10"><div class="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between"><div class="flex items-center gap-3"><div class="w-8 h-8 rounded-lg bg-zinc-900 text-white grid place-items-center font-black text-sm">F</div><div><div class="font-semibold">Site Config</div><div class="mono text-xs text-zinc-500">no developer needed — change here, site updates instantly</div></div></div><div class="flex gap-2"><a href="/admin/" class="mono text-xs px-3 py-1.5 rounded-full border border-zinc-200">← Admin</a><a href="/" target="_blank" class="text-xs px-3 py-1.5 rounded-full bg-zinc-900 text-white">View site →</a></div></div></header>
<main class="max-w-3xl mx-auto px-6 py-8">
{alert}
<div class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 mb-6">Editing <span class="mono font-semibold">{base}/site.config.json</span> + <span class="mono font-semibold">site.config.private.json</span> (gitignored) + <span class="mono font-semibold">assets/js/site-config.js</span>. Business emails (<span class="font-semibold">hello@ / contact@</span>) are public and need to stay visible for Dodo verification — private <span class="mono">forwardTo</span> never goes to HTML.</div>
<form method="POST" action="/admin/config" class="space-y-6 bg-white border border-zinc-200 rounded-2xl p-6">
<h3 class="font-semibold">Public — visible on site (crawlers see this)</h3>
<div class="grid sm:grid-cols-2 gap-4">
<div><label class="mono text-xs font-semibold text-zinc-600">Primary Email (hello@)</label><input name="primaryEmail" value="{v('contact.primaryEmail','hello@focalis.cc')}" required class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm" placeholder="hello@focalis.cc"></div>
<div><label class="mono text-xs font-semibold text-zinc-600">Support Email (contact@)</label><input name="supportEmail" value="{v('contact.supportEmail','contact@focalis.cc')}" required class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm" placeholder="contact@focalis.cc"></div>
</div>
<div class="grid sm:grid-cols-2 gap-4">
<div><label class="mono text-xs font-semibold text-zinc-600">Company Legal Name</label><input name="legalName" value="{v('company.legalName','Focalis S.A.S.')}" required class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm"></div>
<div><label class="mono text-xs font-semibold text-zinc-600">Location</label><input name="location" value="{v('company.location','Bogotá, Colombia')}" required class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm"></div>
</div>
<div><label class="mono text-xs font-semibold text-zinc-600">Full Address (footer/legal)</label><input name="fullAddress" value="{v('company.fullAddress','Bogotá, D.C., Colombia')}" class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm"></div>
<div class="grid sm:grid-cols-2 gap-4">
<div><label class="mono text-xs font-semibold text-zinc-600">Domain</label><input name="domain" value="{v('site.domain','focalis.cc')}" class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm"></div>
<div><label class="mono text-xs font-semibold text-zinc-600">Founded</label><input name="founded" value="{v('company.founded','2019')}" class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm"></div>
</div>
<div><label class="mono text-xs font-semibold text-zinc-600">Tagline</label><input name="tagline" value="{v('site.tagline','Technology that gives time back')}" class="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2 text-sm"></div>
<div class="pt-4 border-t border-zinc-200">
<h3 class="font-semibold">Private — never shown on site (gitignored)</h3>
<p class="mono text-xs text-zinc-500">Forward destination for Email Routing / SMTP. Stored in <span class="mono">site.config.private.json</span> (600, never pushed to GitHub).</p>
<div class="mt-3"><label class="mono text-xs font-semibold text-zinc-600">Forward To (your personal Gmail)</label><input name="forwardTo" type="email" value="{v('private.forwardTo','')}" placeholder="you@gmail.com" class="mt-1 w-full rounded-xl border border-amber-300 bg-amber-50/30 px-3 py-2 text-sm"></div>
<p class="mono text-xs text-zinc-400 mt-1">Used for: Cloudflare Email Routing + contact form SMTP. Leave empty if you only use the form log.</p>
</div>
<button type="submit" class="w-full rounded-xl bg-zinc-900 text-white py-3 text-sm font-semibold hover:bg-black">Save → update site instantly</button>
<p class="mono text-xs text-zinc-400 text-center">Writes <span class="mono">site.config.json</span> + <span class="mono">site.config.private.json</span> + <span class="mono">assets/js/site-config.js</span> and syncs HTML fallback for crawlers. No restart needed.</p>
</form>
<div class="mt-6 rounded-xl border border-zinc-200 bg-white p-4 mono text-xs text-zinc-600">
<div class="font-semibold text-zinc-800">Current files</div>
<div>JSON: <span class="mono">{j}</span> — exists: {str(j.exists())}</div>
<div>JS: <span class="mono">{js}</span> — exists: {str(js.exists())}</div>
<div>Private: <span class="mono">{priv}</span> — exists: {str(priv.exists())} (gitignored)</div>
<div class="mt-2">Preview: <a href="/api/site-config" class="underline">/api/site-config</a> (public) · <a href="/assets/js/site-config.js" class="underline">/assets/js/site-config.js</a> · <a href="/world/" class="underline">/world/</a></div>
</div>
</main></body></html>"""
    return Response(html, mimetype="text/html")

@app.route("/admin/config", methods=["POST"])
@requires_auth
def admin_config_post():
    try:
        data = {
            "site": {"domain": request.form.get("domain","focalis.cc").strip(), "title": "Focalis", "tagline": request.form.get("tagline","Technology that gives time back").strip()},
            "company": {"legalName": request.form.get("legalName","Focalis S.A.S.").strip(), "location": request.form.get("location","Bogotá, Colombia").strip(), "fullAddress": request.form.get("fullAddress","Bogotá, D.C., Colombia").strip(), "founded": request.form.get("founded","2019").strip()},
            "contact": {"primaryEmail": request.form.get("primaryEmail","hello@focalis.cc").strip(), "supportEmail": request.form.get("supportEmail","contact@focalis.cc").strip(), "legalEmail": request.form.get("supportEmail","contact@focalis.cc").strip(), "responseTime": "within 24 hours on business days (Mon–Fri, Bogotá UTC-5)"},
            "private": {"forwardTo": request.form.get("forwardTo","").strip()}
        }
        # basic validation
        if "@" not in data["contact"]["primaryEmail"] or "@" not in data["contact"]["supportEmail"]:
            return redirect("/admin/config?err=Invalid+email", code=303)
        if len(data["company"]["legalName"]) < 2:
            return redirect("/admin/config?err=Company+name+too+short", code=303)
        _save_site_config(data)
        return redirect("/admin/config?msg=Saved+✓+site+updated+instantly", code=303)
    except Exception as e:
        print(f"[config] save failed: {e}", flush=True)
        return redirect(f"/admin/config?err={str(e)[:120]}", code=303)

@app.route("/api/site-config", methods=["GET"])
def api_site_config():
    cfg, j, js, priv, base = _load_site_config()
    public = {"site": cfg.get("site",{}), "company": cfg.get("company",{}), "contact": cfg.get("contact",{})}
    return jsonify({"ok": True, "config": public, "variant": str(base.name)})

if __name__ == "__main__":
    print(f"[admin] focalis.cc admin starting on 0.0.0.0:8788, ACTIVE_FILE={ACTIVE_FILE}, VARIANTS_DIR={VARIANTS_DIR}", flush=True)
    app.run(host="0.0.0.0", port=8788, debug=False)

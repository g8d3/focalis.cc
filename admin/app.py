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
}
VARIANT_ALIASES = {
    "studio": "variant-a-studio",
    "variant-a": "variant-a-studio",
    "labs": "variant-b-labs",
    "variant-b": "variant-b-labs",
    "systems": "variant-c-systems",
    "variant-c": "variant-c-systems",
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
        var labels = { 'variant-a-studio':'Studio','variant-b-labs':'Labs','variant-c-systems':'Systems' };
        var colors = { 'variant-a-studio':'#7C5CFF','variant-b-labs':'#FF4D00','variant-c-systems':'#0F2342' };
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
          + '</span>'
          + '<span style="margin-left:auto;display:flex;align-items:center;gap:8px;">'
          + '<a href="/studio/" style="color:#9CA3AF;text-decoration:none;">Preview: /studio/</a>'
          + '<a href="/labs/" style="color:#9CA3AF;text-decoration:none;">/labs/</a>'
          + '<a href="/systems/" style="color:#9CA3AF;text-decoration:none;">/systems/</a>'
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

  <div class="mt-8 rounded-xl border border-zinc-200 bg-white p-4">
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

if __name__ == "__main__":
    print(f"[admin] focalis.cc admin starting on 0.0.0.0:8788, ACTIVE_FILE={ACTIVE_FILE}, VARIANTS_DIR={VARIANTS_DIR}", flush=True)
    app.run(host="0.0.0.0", port=8788, debug=False)

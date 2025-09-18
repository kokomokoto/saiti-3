from flask import Flask, render_template, send_from_directory, request, redirect, url_for, g, jsonify
import os
import json
from datetime import datetime
try:
    import geoip2.database
except Exception:
    geoip2 = None
try:
    from user_agents import parse as ua_parse
except Exception:
    ua_parse = None

# optional path to MaxMind DB (set VISITORS_GEOIP_DB env var or leave None)
GEOIP_DB = os.environ.get('VISITORS_GEOIP_DB')
_geo_reader = None
if geoip2 and GEOIP_DB and os.path.exists(GEOIP_DB):
    try:
        _geo_reader = geoip2.database.Reader(GEOIP_DB)
    except Exception:
        _geo_reader = None

app = Flask(__name__, static_folder='app/static', template_folder='app/templates')


@app.context_processor
def inject_environ():
    return {'environ': os.environ}

# path to append visitor logs (JSON lines)
VISITORS_LOG = os.path.join(app.root_path, 'app', 'data', 'visitors.log')


@app.before_request
def load_language():
    # expose selected language to templates via g.lang
    g.lang = request.cookies.get('lang', 'ka')


@app.before_request
def log_visit():
    # Append a JSON-line with basic visitor info for simple analytics/audit.
    # Avoid logging static assets and the admin endpoint itself.
    try:
        p = request.path or ''
        if p.startswith('/static') or p.startswith('/admin/visitors'):
            return
        ts = datetime.utcnow().isoformat() + 'Z'
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        ua = request.headers.get('User-Agent', '')
        referer = request.headers.get('Referer', '')
        accept = request.headers.get('Accept', '')
        args = request.args.to_dict(flat=True)
        entry = {
            'ts': ts,
            'ip': ip,
            'path': p,
            'method': request.method,
            'ua': ua,
            'referer': referer,
            'accept': accept,
            'args': args
        }
        # enrich with GeoIP (country/city) if available
        try:
            if _geo_reader and ip:
                # if X-Forwarded-For contains comma, take first
                if ',' in ip:
                    ip_lookup = ip.split(',')[0].strip()
                else:
                    ip_lookup = ip
                rec = _geo_reader.city(ip_lookup)
                entry['geo'] = {
                    'country': getattr(rec.country, 'name', None),
                    'country_iso': getattr(rec.country, 'iso_code', None),
                    'city': getattr(rec.city, 'name', None),
                    'lat': getattr(rec.location, 'latitude', None),
                    'lon': getattr(rec.location, 'longitude', None)
                }
        except Exception:
            pass
        # parse user-agent for device/browser if library present
        try:
            if ua_parse and ua:
                ua_obj = ua_parse(ua)
                entry['device'] = {
                    'family': ua_obj.device.family,
                    'brand': ua_obj.device.brand,
                    'model': ua_obj.device.model,
                    'is_mobile': ua_obj.is_mobile,
                    'is_tablet': ua_obj.is_tablet,
                    'is_pc': ua_obj.is_pc,
                    'os': ua_obj.os.family,
                    'browser': ua_obj.browser.family,
                }
        except Exception:
            pass
        # ensure directory exists
        os.makedirs(os.path.dirname(VISITORS_LOG), exist_ok=True)
        with open(VISITORS_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        # do not break the site if logging fails
        pass



@app.route('/set_language/<lang>')
def set_language(lang):
    # simple language setter: store in a cookie and redirect back
    if lang not in ('ka', 'en', 'ru'):
        return redirect(request.referrer or url_for('index'))
    resp = redirect(request.referrer or url_for('index'))
    resp.set_cookie('lang', lang, max_age=30*24*3600)
    return resp


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/object/<path:obj>')
def object_detail_passthrough(obj):
    # Backwards-compatible passthrough for old links. Try to extract an id
    # suffix if the link was constructed as <category><id> and redirect or
    # render the detail for the found id.
    # We will try to find the project by id substring match.
    data_path = os.path.join(app.root_path, 'app', 'data', 'projects.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            projects = json.load(f)
    except FileNotFoundError:
        projects = []
    # try to find an entry whose id is a suffix of the path
    found = None
    for p in projects:
        pid = p.get('id')
        if pid and obj.endswith(pid):
            found = p
            break
    return render_template('object_detail.html', project=found)


@app.route('/object/id/<project_id>')
def object_detail(project_id):
    # Load projects.json and return the project matching project_id.
    data_path = os.path.join(app.root_path, 'app', 'data', 'projects.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            projects = json.load(f)
    except FileNotFoundError:
        projects = []
    found = None
    for p in projects:
        if p.get('id') == project_id:
            found = p
            break
    return render_template('object_detail.html', project=found)


@app.route('/search')
def search():
    # placeholder search route used by templates/js
    q = None
    return render_template('search_results.html')


@app.route('/api/projects')
def api_projects():
    data_path = os.path.join(app.root_path, 'app', 'data', 'projects.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            projects = json.load(f)
    except FileNotFoundError:
        projects = []
    # Normalize category field: allow either string or list in the source JSON,
    # but always return a list to the client for consistent client-side logic.
    for p in projects:
        if 'category' not in p:
            p['category'] = []
        elif isinstance(p['category'], str):
            p['category'] = [p['category']]
        # if it's already a list, leave it as-is
    return {'projects': projects}


@app.route('/api/debug_projects')
def api_debug_projects():
    """Debug endpoint: returns paths and raw file contents for troubleshooting."""
    data_path = os.path.join(app.root_path, 'app', 'data', 'projects.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            raw = f.read()
    except Exception as e:
        raw = f'ERROR: {e}'
    return {
        'app_root_path': app.root_path,
        'data_path': data_path,
        'file_contents': raw
    }


@app.route('/sitemap.xml')
def sitemap_xml():
    # generate a simple sitemap from projects.json
    data_path = os.path.join(app.root_path, 'app', 'data', 'projects.json')
    urls = [url_for('index', _external=True)]
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            projects = json.load(f)
    except Exception:
        projects = []
    for p in projects:
        pid = p.get('id')
        if pid:
            urls.append(url_for('object_detail', project_id=pid, _external=True))
    sitemap_items = '\n'.join([f"  <url>\n    <loc>{u}</loc>\n  </url>" for u in urls])
    sitemap = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n{sitemap_items}\n</urlset>"
    return app.response_class(sitemap, mimetype='application/xml')


@app.route('/robots.txt')
def robots_txt():
    sitemap_url = url_for('sitemap_xml', _external=True)
    content = f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n"
    return app.response_class(content, mimetype='text/plain')


@app.route('/admin/visitors')
def admin_visitors():
    """Return recent visitor log entries as JSON. Protected by VISITORS_SECRET env var.
    Call with: /admin/visitors?secret=THE_SECRET&limit=100
    """
    secret = request.args.get('secret') or os.environ.get('VISITORS_SECRET')
    if not secret or secret != os.environ.get('VISITORS_SECRET'):
        return jsonify({'error': 'unauthorized'}), 401
    try:
        limit = int(request.args.get('limit', '200'))
    except ValueError:
        limit = 200
    entries = []
    if os.path.exists(VISITORS_LOG):
        with open(VISITORS_LOG, 'r', encoding='utf-8') as f:
            # read last N lines efficiently
            lines = f.readlines()[-limit:]
        for ln in lines:
            try:
                entries.append(json.loads(ln))
            except Exception:
                continue
    return jsonify({'entries': entries})


if __name__ == '__main__':
    # Use 0.0.0.0 only if you need external access; default is fine for local
    app.run(debug=True)

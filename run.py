from flask import Flask, render_template, send_from_directory
import os
import json

app = Flask(__name__, static_folder='app/static', template_folder='app/templates')


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


if __name__ == '__main__':
    # Use 0.0.0.0 only if you need external access; default is fine for local
    app.run(debug=True)

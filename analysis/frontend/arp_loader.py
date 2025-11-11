"""Loader to attach the ARP_Attack Dash UI to Doom-and-Gloom's Flask app.

This reads the original ARP_Attack dashboard source, patches it to reuse
the existing Flask `app` (from analysis/dashboard_enhanced.py) instead of
creating a new Flask instance, and executes it in a controlled module
namespace. This avoids duplicating the large dashboard source and keeps
maintenance simple.

Run (in WSL2 recommended):
  python3 analysis/frontend/arp_loader.py

Then visit http://localhost:8050 to view the ARP dashboard (it will bind
to the same Flask process if you run analysis/dashboard_enhanced.py first).
"""

import os
import importlib.util
import sys

# Locate repository and target files
THIS = os.path.abspath(os.path.dirname(__file__))
REPO = os.path.abspath(os.path.join(THIS, '..', '..'))
ARP_DASH_SRC = os.path.join(os.path.dirname(REPO), 'ARP_Attack', 'Labsetup-arm', 'volumes', 'dashboard.py')
LOCAL_DASH = os.path.join(REPO, 'analysis', 'dashboard_enhanced.py')

if not os.path.exists(ARP_DASH_SRC):
    print(f"ARP dashboard source not found at: {ARP_DASH_SRC}")
    sys.exit(1)

if not os.path.exists(LOCAL_DASH):
    print(f"Local Doom-and-Gloom dashboard not found at: {LOCAL_DASH}")
    sys.exit(1)

# Import the local dashboard module to get its Flask `app` instance
spec = importlib.util.spec_from_file_location('doom_dashboard', LOCAL_DASH)
doom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doom)

flask_app = getattr(doom, 'app', None)
if flask_app is None:
    print("Could not find Flask `app` in analysis/dashboard_enhanced.py")
    sys.exit(1)

# Read ARP_Attack dashboard source and write a temporary patched copy that
# uses `flask_app` as the server (so Dash attaches to the existing Flask
# application). We'll then import that patched file using importlib so the
# module has a proper __file__ and root path for Dash.
with open(ARP_DASH_SRC, 'r', encoding='utf-8') as f:
    src = f.read()

# Patch 1: Replace Flask server creation with our existing flask_app
patched = src.replace("server = Flask(__name__)", "server = flask_app  # replaced by arp_loader to reuse existing Flask app")

# Patch 2: Add url_base_pathname to Dash app to avoid conflict with Flask / route
patched = patched.replace(
    'app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.DARKLY])',
    'app = dash.Dash(__name__, server=server, url_base_pathname="/dash/", external_stylesheets=[dbc.themes.DARKLY])'
)

patched_path = os.path.join(THIS, '_arp_dashboard_patched.py')
with open(patched_path, 'w', encoding='utf-8') as f:
    f.write(patched)

# Import the patched module via importlib so Dash can determine a valid root path
spec2 = importlib.util.spec_from_file_location('arp_dashboard_patched', patched_path)
arp_mod = importlib.util.module_from_spec(spec2)
# inject our existing flask_app into the module namespace before execution
setattr(arp_mod, 'flask_app', flask_app)
try:
    spec2.loader.exec_module(arp_mod)
except Exception as e:
    print(f"Error importing patched ARP dashboard module: {e}")
    raise

arp_dash_app = getattr(arp_mod, 'app', None) or getattr(arp_mod, 'dash', None)
if arp_dash_app:
    print("ARP_Attack dashboard attached to Doom-and-Gloom Flask app (patched import).")
    print(f"Dash app will be available at http://localhost:5000{arp_dash_app.config.url_base_pathname}")
else:
    print("Warning: patched ARP_Attack dashboard imported but no Dash `app` instance found.")

if __name__ == '__main__':
    # If run directly, start the local Flask+SocketIO server which now
    # has the Dash app attached. This mirrors how the repository runs
    # the dashboard_enhanced script normally.
    print("Starting Doom-and-Gloom dashboard (with ARP UI attached) on http://0.0.0.0:5000")
    print("  - Flask API endpoints: http://localhost:5000/api/*")
    print("  - Flask dashboard: http://localhost:5000/")
    print("  - Dash ARP UI: http://localhost:5000/dash/")
    # Use the run logic already present in the local dashboard module
    try:
        doom.socketio.run(doom.app, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Failed to start combined server: {e}")

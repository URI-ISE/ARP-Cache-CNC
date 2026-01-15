import os
import json
import dash
import signal
import subprocess
import threading
import pandas as pd
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask
from datetime import datetime

LOG_DIR = "/volumes/logs"
LOG_FILE = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json") and f.startswith("packet_log")])[-1] if any(f.endswith(".json") and f.startswith("packet_log") for f in os.listdir(LOG_DIR)) else None
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE) if LOG_FILE else None
MITM_SCRIPT = "/volumes/mitm.py"
CONTROL_FILE = "/volumes/logs/mitm_control.json"

# Track the subprocess & mode
mitm_process = None
selected_mode = "default"
poisoning_enabled = False
sniffer_enabled = False

# Create Flask server
server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.DARKLY])

# Function to update the control file
def update_control_file():
    try:
        # Create the control data
        control_data = {
            "poisoning_enabled": poisoning_enabled,
            "sniffer_enabled": sniffer_enabled,
            "mode": selected_mode,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Write to the control file
        with open(CONTROL_FILE, "w") as f:
            json.dump(control_data, f)
            
        print(f"Updated control file: {CONTROL_FILE}")
        print(f"New state: poisoning={poisoning_enabled}, sniffer={sniffer_enabled}, mode={selected_mode}")
    except Exception as e:
        print(f"Error updating control file: {e}")

# Function to read the current state from the control file
def read_control_file():
    global poisoning_enabled, sniffer_enabled, selected_mode
    try:
        if os.path.exists(CONTROL_FILE):
            with open(CONTROL_FILE, "r") as f:
                control_data = json.load(f)
                poisoning_enabled = control_data.get("poisoning_enabled", False)
                sniffer_enabled = control_data.get("sniffer_enabled", False)
                selected_mode = control_data.get("mode", "default")
            print(f"Read from control file: poisoning={poisoning_enabled}, sniffer={sniffer_enabled}, mode={selected_mode}")
    except Exception as e:
        print(f"Error reading control file: {e}")

# Function to launch MITM in subprocess
def run_mitm(mode):
    global mitm_process
    mitm_process = subprocess.Popen(["python3", MITM_SCRIPT, mode])

def stop_mitm():
    global mitm_process
    if mitm_process and mitm_process.poll() is None:
        mitm_process.terminate()
        mitm_process = None

def is_mitm_running():
    return mitm_process is not None and mitm_process.poll() is None

def load_logs():
    data = []
    try:
        if LOG_PATH and os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry["timestamp"] = pd.to_datetime(entry["timestamp"])
                        entry["packet_type"] = entry.get("packet_type", "Unknown").strip()
                        data.append(entry)
                    except Exception as e:
                        print(f"[Log parse error] {e}")
        else:
            print(f"[Log load] No log file found at {LOG_PATH}")
    except Exception as e:
        print(f"[Log read error] {e}")

    print(f"[Log load] {len(data)} entries loaded from {LOG_PATH}")
    if data:
        print(pd.DataFrame(data).head())
    return pd.DataFrame(data)

@app.callback(
    Output("filter-type", "options"),
    Output("filter-start", "value"),
    Output("filter-end", "value"),
    Input("refresh", "n_intervals")
)
def update_dropdowns(_):
    df = load_logs()
    if df.empty:
        return [], None, None
    unique_types = sorted(df["packet_type"].dropna().unique())
    start_time = df["timestamp"].min().strftime("%Y-%m-%d %H:%M:%S")
    end_time = df["timestamp"].max().strftime("%Y-%m-%d %H:%M:%S")
    return ([{"label": t, "value": t} for t in unique_types], start_time, end_time)

@app.callback(
    Output("log-chart", "figure"),
    Output("log-table", "children"),
    Output("debug-output", "children"),
    Input("refresh", "n_intervals"),
    State("filter-src", "value"),
    State("filter-dst", "value"),
    State("filter-type", "value"),
    State("filter-start", "value"),
    State("filter-end", "value")
)
def update_dashboard(_, filter_src, filter_dst, packet_type, start_time, end_time):
    df = load_logs()
    if df.empty:
        return dash.no_update, dash.no_update, "No log entries found."

    debug_info = f"Loaded {len(df)} entries\n" + str(df[["timestamp", "packet_type", "src_ip", "dst_ip"]].tail(5))

    # Apply filters
    if filter_src:
        df = df[df["src_ip"].str.contains(filter_src.strip())]
    if filter_dst:
        df = df[df["dst_ip"].str.contains(filter_dst.strip())]
    if packet_type:
        df = df[df["packet_type"] == packet_type]
    if start_time:
        df = df[df["timestamp"] >= pd.to_datetime(start_time)]
    if end_time:
        df = df[df["timestamp"] <= pd.to_datetime(end_time)]

    # Bar chart
    count_df = df.groupby(["packet_type", pd.Grouper(key="timestamp", freq="1s")]).size().reset_index(name="count")
    fig = px.bar(count_df, x="timestamp", y="count", color="packet_type", title="Packet Counts Over Time")

    # Styled table
    last_rows = df.sort_values("timestamp", ascending=False).head(16)
    table_rows = []
    for _, row in last_rows.iterrows():
        style = {"color": "red"} if row["packet_type"] == "Modified" else {}
        table_rows.append(html.Tr([
            html.Td(row["timestamp"]), html.Td(row["packet_type"]), html.Td(row["src_ip"]), html.Td(row["dst_ip"]),
            html.Td(row["src_port"]), html.Td(row["dst_port"]), html.Td(row["flags"]),
            html.Td(row["seq"]), html.Td(row["ack"]), html.Td(row["payload_length"]), html.Td(row["payload"])
        ], style=style))

    table = dbc.Table([
        html.Thead(html.Tr([html.Th(c) for c in ["timestamp", "packet_type", "src_ip", "dst_ip", "src_port", "dst_port", "flags", "seq", "ack", "payload_length", "payload"]])),
        html.Tbody(table_rows)
    ], striped=True, bordered=True, hover=True, responsive=True)

    return fig, table, debug_info

# New callback to update the status indicators based on control file
@app.callback(
    Output("poison-status", "children"),
    Output("poison-btn", "className"),
    Output("sniff-status", "children"),
    Output("sniff-btn", "className"),
    Input("status-check", "n_intervals")
)
def update_status_from_control(_):
    # Read current state from control file
    read_control_file()
    
    # Update UI states
    poison_status = "Poisoning Enabled" if poisoning_enabled else "Poisoning Disabled"
    poison_btn_class = "btn btn-success" if poisoning_enabled else "btn btn-danger"
    
    sniff_status = "Sniffer Running" if sniffer_enabled else "Sniffer Stopped"
    sniff_btn_class = "btn btn-success" if sniffer_enabled else "btn btn-danger"
    
    return poison_status, poison_btn_class, sniff_status, sniff_btn_class

# Layout
app.layout = html.Div([
    html.H2("MITM Dashboard", style={"textAlign": "center"}),
    dcc.Interval(id="status-check", interval=3000, n_intervals=0),  # Check status every 3 seconds
    dcc.Tabs([
        dcc.Tab(label="Summary", children=[
            dcc.Interval(id="refresh", interval=3000, n_intervals=0),
            dcc.Graph(id="log-chart"),
            html.Br(),
            dbc.Row([
                dbc.Col([html.Label("Filter by Source IP"), dcc.Input(id="filter-src", type="text", placeholder="10.9.0.5", className="form-control")], width=4),
                dbc.Col([html.Label("Filter by Destination IP"), dcc.Input(id="filter-dst", type="text", placeholder="10.9.0.6", className="form-control")], width=4),
                dbc.Col([html.Label("Packet Type"), dcc.Dropdown(id="filter-type", options=[], placeholder="Select packet type")], width=4)
            ]),
            html.Br(),
            dbc.Row([
                dbc.Col([html.Label("Start Time"), dcc.Input(id="filter-start", type="text", placeholder="YYYY-MM-DD HH:MM:SS", className="form-control")], width=6),
                dbc.Col([html.Label("End Time"), dcc.Input(id="filter-end", type="text", placeholder="YYYY-MM-DD HH:MM:SS", className="form-control")], width=6)
            ]),
            html.Hr(),
            html.H4("Last 16 Messages"),
            html.Div(id="log-table"),
            html.Hr(),
            html.H5("Debug Log Info"),
            html.Pre(id="debug-output", style={"whiteSpace": "pre-wrap", "color": "#00FF00"})
        ]),

        dcc.Tab(label="Setup", children=[
            html.Br(),
            dbc.Row([
                dbc.Col([html.Label("Select Mode"), dcc.Dropdown(
                    id="mode-dropdown",
                    options=[{"label": m, "value": m} for m in ["xy", "g1g0", "dos", "default"]],
                    value="default",
                    style={"color": "black"}
                )], width=4),
                dbc.Col([html.Br(), html.Button("Start/Stop", id="start-btn", className="btn btn-danger")], width=2),
                dbc.Col(html.Div(id="status-text"), width=6)
            ]),
            html.Br(),
            dbc.Row([
                dbc.Col([html.Button("Toggle Poisoning", id="poison-btn", className="btn btn-danger", n_clicks=0)], width=3),
                dbc.Col([html.Button("Toggle Sniffer", id="sniff-btn", className="btn btn-danger", n_clicks=0)], width=3),
                dbc.Col(html.Div(id="poison-status"), width=3),
                dbc.Col(html.Div(id="sniff-status"), width=3)
            ])
        ]),
        dcc.Tab(label="Tab 3", children=[html.Div("(Reserved)")]),
        dcc.Tab(label="Tab 4", children=[html.Div("(Reserved)")])
    ])
])

@app.callback(
    Output("status-text", "children"),
    Output("start-btn", "className"),
    Input("start-btn", "n_clicks"),
    State("mode-dropdown", "value"),
    prevent_initial_call=True
)
def toggle_script(n_clicks, mode):
    global selected_mode
    if is_mitm_running():
        stop_mitm()
        return "Status: STOPPED", "btn btn-danger"
    else:
        selected_mode = mode
        run_mitm(mode)
        # Update the control file with the new mode
        update_control_file()
        return f"Status: RUNNING in '{mode}' mode", "btn btn-success"

@app.callback(
    Output("poison-status", "children", allow_duplicate=True),
    Output("poison-btn", "className", allow_duplicate=True),
    Input("poison-btn", "n_clicks"),
    prevent_initial_call=True
)
def toggle_poisoning(n):
    global poisoning_enabled
    poisoning_enabled = not poisoning_enabled
    
    # Update the control file to communicate with mitm.py
    update_control_file()
    
    status = "Poisoning Enabled" if poisoning_enabled else "Poisoning Disabled"
    btn_class = "btn btn-success" if poisoning_enabled else "btn btn-danger"
    return status, btn_class

@app.callback(
    Output("sniff-status", "children", allow_duplicate=True),
    Output("sniff-btn", "className", allow_duplicate=True),
    Input("sniff-btn", "n_clicks"),
    prevent_initial_call=True
)
def toggle_sniffer(n):
    global sniffer_enabled
    sniffer_enabled = not sniffer_enabled
    
    # Update the control file to communicate with mitm.py
    update_control_file()
    
    status = "Sniffer Running" if sniffer_enabled else "Sniffer Stopped"
    btn_class = "btn btn-success" if sniffer_enabled else "btn btn-danger"
    return status, btn_class

if __name__ == "__main__":
    # Initialize - read current state from control file if it exists
    read_control_file()

    print(f"[Dashboard] Starting with: poisoning={poisoning_enabled}, sniffer={sniffer_enabled}, mode={selected_mode}")
    if LOG_PATH:
        print(f"[Dashboard] Reading log from: {LOG_PATH}")
    else:
        print(f"[Dashboard] No log file found in {LOG_DIR}")
    
    app.run(debug=True, host="0.0.0.0", port=8050)
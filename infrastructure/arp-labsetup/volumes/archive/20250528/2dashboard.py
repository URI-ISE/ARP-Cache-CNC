import os
import json
import dash
import signal
import subprocess
import threading
import pandas as pd
import numpy as np
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask
from datetime import datetime
import re  # For parsing G-code commands

LOG_DIR = "/volumes/logs"
LOG_FILE = sorted([f for f in os.listdir(LOG_DIR) if f.endswith(".json") and f.startswith("packet_log")])[-1] if any(f.endswith(".json") and f.startswith("packet_log") for f in os.listdir(LOG_DIR)) else None
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE) if LOG_FILE else None
MITM_SCRIPT = "/volumes/1mitm.py"
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
                        
                        # Ensure flags have a default value if missing
                        if "flags" not in entry or not entry["flags"]:
                            entry["flags"] = "N/A"
                            
                        # Flag formatting - provide a human-readable description
                        flags = entry["flags"]
                        if flags:
                            # If we have a comma-separated flag string like 'PA', format it for readability
                            formatted_flags = []
                            if 'F' in flags: formatted_flags.append('FIN')
                            if 'S' in flags: formatted_flags.append('SYN')
                            if 'R' in flags: formatted_flags.append('RST')
                            if 'P' in flags: formatted_flags.append('PSH')
                            if 'A' in flags: formatted_flags.append('ACK')
                            if 'U' in flags: formatted_flags.append('URG')
                            if 'E' in flags: formatted_flags.append('ECE')
                            if 'C' in flags: formatted_flags.append('CWR')
                            
                            if formatted_flags:
                                entry["flags"] = ' '.join(formatted_flags)
                            
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
    Output("filter-start", "date"),
    Output("filter-start-time", "value"),
    Output("filter-end", "date"),
    Output("filter-end-time", "value"),
    Input("refresh", "n_intervals")
)
def update_dropdowns(_):
    df = load_logs()
    if df.empty:
        return [], None, "00:00:00", None, "23:59:59"
    
    unique_types = sorted(df["packet_type"].dropna().unique())
    
    if not df.empty:
        # Get min and max timestamps
        min_timestamp = df["timestamp"].min()
        max_timestamp = df["timestamp"].max()
        
        # Format date for the date pickers
        start_date = min_timestamp.date()
        end_date = max_timestamp.date()
        
        # Format time for the time inputs
        start_time = min_timestamp.strftime("%H:%M:%S")
        end_time = max_timestamp.strftime("%H:%M:%S")
        
        return [{"label": t, "value": t} for t in unique_types], start_date, start_time, end_date, end_time
    
    return [{"label": t, "value": t} for t in unique_types], None, "00:00:00", None, "23:59:59"

@app.callback(
    Output("log-chart", "figure"),
    Output("log-table", "children"),
    Output("debug-output", "children"),
    Input("refresh", "n_intervals"),
    State("filter-src", "value"),
    State("filter-dst", "value"),
    State("filter-type", "value"),
    State("filter-start", "date"),
    State("filter-start-time", "value"),
    State("filter-end", "date"),
    State("filter-end-time", "value")
)
def update_dashboard(_, filter_src, filter_dst, packet_type, start_date, start_time, end_date, end_time):
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
    
    # Combine date and time filters
    if start_date and start_time:
        start_datetime_str = f"{start_date} {start_time}"
        try:
            start_datetime = pd.to_datetime(start_datetime_str)
            df = df[df["timestamp"] >= start_datetime]
        except:
            debug_info += f"\nInvalid start date/time: {start_datetime_str}"
    
    if end_date and end_time:
        end_datetime_str = f"{end_date} {end_time}"
        try:
            end_datetime = pd.to_datetime(end_datetime_str)
            df = df[df["timestamp"] <= end_datetime]
        except:
            debug_info += f"\nInvalid end date/time: {end_datetime_str}"
    
    # Bar chart
    count_df = df.groupby(["packet_type", pd.Grouper(key="timestamp", freq="1s")]).size().reset_index(name="count")
    
    # Custom color mapping for packet types
    color_discrete_map = {
        "Original": "blue",
        "Modified": "red"
    }
    
    fig = px.bar(count_df, x="timestamp", y="count", color="packet_type", 
                 title="Packet Counts Over Time",
                 color_discrete_map=color_discrete_map)
    
    # Update layout for better visibility
    fig.update_layout(
        legend_title_text="Packet Type",
        xaxis_title="Time",
        yaxis_title="Count"
    )

    # Styled table with enhanced flag display
    last_rows = df.sort_values("timestamp", ascending=False).head(16)
    table_rows = []
    for _, row in last_rows.iterrows():
        # Style for different packet types
        if row["packet_type"] == "Modified":
            row_style = {"color": "red"}
        else:
            row_style = {}
            
        # Format flags for better display
        flags_display = row["flags"] if pd.notna(row["flags"]) and row["flags"] else "N/A"
        
        # Create table row
        table_rows.append(html.Tr([
            html.Td(row["timestamp"]), 
            html.Td(row["packet_type"]), 
            html.Td(row["src_ip"]), 
            html.Td(row["dst_ip"]),
            html.Td(row["src_port"]), 
            html.Td(row["dst_port"]), 
            html.Td(flags_display, style={"font-weight": "bold"}),  # Make flags bold
            html.Td(row["seq"]), 
            html.Td(row["ack"]), 
            html.Td(row["payload_length"]), 
            html.Td(row["payload"])
        ], style=row_style))

    # Create the table with a tooltip explaining TCP flags
    table = html.Div([
        dbc.Tooltip(
            "TCP Flags: FIN=Connection Finish, SYN=Synchronize, RST=Reset, PSH=Push, ACK=Acknowledge, URG=Urgent, ECE=ECN Echo, CWR=Congestion Window Reduced",
            target="tcp-flags-help",
            placement="top"
        ),
        html.Div([
            html.Span("TCP Flags ", style={"font-weight": "bold"}),
            html.I(className="fas fa-question-circle", id="tcp-flags-help", style={"cursor": "pointer"})
        ], style={"text-align": "center", "margin-bottom": "10px"}),
        dbc.Table([
            html.Thead(html.Tr([html.Th(c) for c in ["timestamp", "packet_type", "src_ip", "dst_ip", "src_port", "dst_port", "flags", "seq", "ack", "payload_length", "payload"]])),
            html.Tbody(table_rows)
        ], striped=True, bordered=True, hover=True, responsive=True)
    ])

    return fig, table, debug_info

# New function to extract G-code commands and convert to 3D coordinates
def extract_gcode_paths():
    df = load_logs()
    if df.empty:
        return None, "No log entries found."
    
    # Filter only packets that likely contain G-code commands (e.g., G0, G1, etc.)
    gcode_pattern = re.compile(r'[G][\d]+')
    
    # Create empty lists to store the path data
    original_path = []
    modified_path = []
    
    # Current position state
    current_original_pos = {'x': 0, 'y': 0, 'z': 0}
    current_modified_pos = {'x': 0, 'y': 0, 'z': 0}
    
    # Process each log entry
    for _, row in df.sort_values("timestamp").iterrows():
        payload = row.get("payload", "")
        
        # Skip if payload doesn't contain G-code commands
        if not isinstance(payload, str) or not gcode_pattern.search(payload):
            continue
        
        # Check if this is a position command (G0 or G1)
        if 'G0' in payload or 'G1' in payload:
            # Extract X, Y, Z coordinates if present
            x_match = re.search(r'X([-+]?\d*\.\d+|\d+)', payload)
            y_match = re.search(r'Y([-+]?\d*\.\d+|\d+)', payload)
            z_match = re.search(r'Z([-+]?\d*\.\d+|\d+)', payload)
            
            # Update current position if coordinates are found
            if x_match:
                x_val = float(x_match.group(1))
            else:
                x_val = current_original_pos['x'] if row["packet_type"] == "Original" else current_modified_pos['x']
                
            if y_match:
                y_val = float(y_match.group(1))
            else:
                y_val = current_original_pos['y'] if row["packet_type"] == "Original" else current_modified_pos['y']
                
            if z_match:
                z_val = float(z_match.group(1))
            else:
                z_val = current_original_pos['z'] if row["packet_type"] == "Original" else current_modified_pos['z']
            
            # Add to appropriate path
            if row["packet_type"] == "Original":
                original_path.append((x_val, y_val, z_val))
                current_original_pos = {'x': x_val, 'y': y_val, 'z': z_val}
            else:  # Modified
                modified_path.append((x_val, y_val, z_val))
                current_modified_pos = {'x': x_val, 'y': y_val, 'z': z_val}
    
    # Convert to DataFrame for easier visualization
    original_df = pd.DataFrame(original_path, columns=['x', 'y', 'z']) if original_path else pd.DataFrame(columns=['x', 'y', 'z'])
    modified_df = pd.DataFrame(modified_path, columns=['x', 'y', 'z']) if modified_path else pd.DataFrame(columns=['x', 'y', 'z'])
    
    debug_info = f"Extracted {len(original_path)} original G-code positions and {len(modified_path)} modified G-code positions."
    
    return {
        'original': original_df,
        'modified': modified_df
    }, debug_info

@app.callback(
    Output("tool-path-3d", "figure"),
    Output("tool-path-status", "children"),
    Input("tool-path-refresh", "n_intervals")
)
def update_tool_path(_):
    paths, debug_info = extract_gcode_paths()
    
    if paths is None:
        return go.Figure(), debug_info
    
    original_df = paths['original']
    modified_df = paths['modified']
    
    # Create 3D plot
    fig = go.Figure()
    
    # Add original tool path in blue
    if not original_df.empty:
        fig.add_trace(go.Scatter3d(
            x=original_df['x'],
            y=original_df['y'],
            z=original_df['z'],
            mode='lines',
            name='Original Path',
            line=dict(color='blue', width=4)
        ))
        
        # Add markers at key points
        fig.add_trace(go.Scatter3d(
            x=[original_df['x'].iloc[0]],
            y=[original_df['y'].iloc[0]],
            z=[original_df['z'].iloc[0]],
            mode='markers',
            marker=dict(size=8, color='darkblue'),
            name='Origin'
        ))
        
        if len(original_df) > 1:
            fig.add_trace(go.Scatter3d(
                x=[original_df['x'].iloc[-1]],
                y=[original_df['y'].iloc[-1]],
                z=[original_df['z'].iloc[-1]],
                mode='markers',
                marker=dict(size=8, color='blue'),
                name='Current Position (Original)'
            ))
    
    # Add modified tool path in red
    if not modified_df.empty:
        fig.add_trace(go.Scatter3d(
            x=modified_df['x'],
            y=modified_df['y'],
            z=modified_df['z'],
            mode='lines',
            name='Modified Path',
            line=dict(color='red', width=4)
        ))
        
        # Add marker for current position
        if len(modified_df) > 0:
            fig.add_trace(go.Scatter3d(
                x=[modified_df['x'].iloc[-1]],
                y=[modified_df['y'].iloc[-1]],
                z=[modified_df['z'].iloc[-1]],
                mode='markers',
                marker=dict(size=8, color='red'),
                name='Current Position (Modified)'
            ))
    
    # Add coordinate axes for reference
    max_range = 10  # Default size if no data available
    
    if not original_df.empty or not modified_df.empty:
        # Combine dataframes to find overall range
        all_data = pd.concat([original_df, modified_df])
        if not all_data.empty:
            x_max = all_data['x'].max() if not all_data['x'].empty else 0
            y_max = all_data['y'].max() if not all_data['y'].empty else 0
            z_max = all_data['z'].max() if not all_data['z'].empty else 0
            x_min = all_data['x'].min() if not all_data['x'].empty else 0
            y_min = all_data['y'].min() if not all_data['y'].empty else 0
            z_min = all_data['z'].min() if not all_data['z'].empty else 0
            
            # Use the largest range for the grid
            max_range = max(
                max(abs(x_max), abs(x_min)),
                max(abs(y_max), abs(y_min)),
                max(abs(z_max), abs(z_min)),
                10  # Minimum range
            )
    
    # Add axes
    axes_length = max_range * 1.2  # Make axes a bit longer than data range
    
    # X-axis (red)
    fig.add_trace(go.Scatter3d(
        x=[0, axes_length],
        y=[0, 0],
        z=[0, 0],
        mode='lines',
        line=dict(color='darkred', width=3),
        name='X-axis'
    ))
    
    # Y-axis (green)
    fig.add_trace(go.Scatter3d(
        x=[0, 0],
        y=[0, axes_length],
        z=[0, 0],
        mode='lines',
        line=dict(color='darkgreen', width=3),
        name='Y-axis'
    ))
    
    # Z-axis (blue)
    fig.add_trace(go.Scatter3d(
        x=[0, 0],
        y=[0, 0],
        z=[0, axes_length],
        mode='lines',
        line=dict(color='darkblue', width=3),
        name='Z-axis'
    ))
    
    # Mark origin with a special marker
    fig.add_trace(go.Scatter3d(
        x=[0],
        y=[0],
        z=[0],
        mode='markers',
        marker=dict(size=10, color='yellow', symbol='circle'),
        name='Origin (0,0,0)'
    ))
    
    # Update layout for better visibility
    fig.update_layout(
        title="3D Tool Path Visualization",
        legend=dict(x=0.8, y=0.9),
        scene=dict(
            xaxis_title="X (mm)",
            yaxis_title="Y (mm)",
            zaxis_title="Z (mm)",
            aspectmode='cube',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        template="plotly_dark"
    )
    
    return fig, debug_info

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

# Tool Path Simulator - Initialize connection callback
@app.callback(
    Output("simulator-status", "children"),
    Input("connect-btn", "n_clicks"),
    State("controller-ip", "value"),
    State("controller-port", "value"),
    State("firmware-ip", "value"),
    State("firmware-port", "value"),
    prevent_initial_call=True
)
def initialize_simulator_connection(n_clicks, controller_ip, controller_port, firmware_ip, firmware_port):
    if n_clicks:
        # Validate inputs
        if not all([controller_ip, controller_port, firmware_ip, firmware_port]):
            return html.Div("Error: All fields are required", style={"color": "red"})
            
        try:
            controller_port = int(controller_port)
            firmware_port = int(firmware_port)
            
            # Here we would add code to establish connection
            # For now, just return status message
            return html.Div(f"Connected to Controller ({controller_ip}:{controller_port}) and Firmware ({firmware_ip}:{firmware_port})", 
                           style={"color": "green"})
        except ValueError:
            return html.Div("Error: Ports must be numeric values", style={"color": "red"})
    return dash.no_update

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
                dbc.Col([html.Label("Start Date"), dcc.DatePickerSingle(
                    id="filter-start",
                    placeholder="Select date",
                    className="form-control",
                    date=None,
                    display_format="YYYY-MM-DD",
                    style={"width": "100%"}
                )], width=3),
                dbc.Col([html.Label("Start Time"), dcc.Input(
                    id="filter-start-time",
                    type="time",
                    placeholder="HH:MM:SS",
                    className="form-control",
                    value="00:00:00",
                    style={"width": "100%"}
                )], width=3),
                dbc.Col([html.Label("End Date"), dcc.DatePickerSingle(
                    id="filter-end",
                    placeholder="Select date",
                    className="form-control",
                    date=None,
                    display_format="YYYY-MM-DD",
                    style={"width": "100%"}
                )], width=3),
                dbc.Col([html.Label("End Time"), dcc.Input(
                    id="filter-end-time",
                    type="time",
                    placeholder="HH:MM:SS",
                    className="form-control",
                    value="23:59:59",
                    style={"width": "100%"}
                )], width=3)
            ]),
            html.Hr(),
            html.H4("TCP Flag Information", className="mb-3"),
            html.P("Common TCP Flags displayed in the logs:", className="mb-2"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Flag"), html.Th("Name"), html.Th("Description")
                ])),
                html.Tbody([
                    html.Tr([html.Td("SYN"), html.Td("Synchronize"), html.Td("Initiates a connection")]),
                    html.Tr([html.Td("ACK"), html.Td("Acknowledge"), html.Td("Acknowledges received data")]),
                    html.Tr([html.Td("PSH"), html.Td("Push"), html.Td("Push buffered data to the receiving application")]),
                    html.Tr([html.Td("FIN"), html.Td("Finish"), html.Td("Properly terminates the connection")]),
                    html.Tr([html.Td("RST"), html.Td("Reset"), html.Td("Aborts a connection (in error scenarios)")]),
                    html.Tr([html.Td("URG"), html.Td("Urgent"), html.Td("Data that should be processed immediately")]),
                    html.Tr([html.Td("ECE"), html.Td("ECN Echo"), html.Td("Indicates network congestion")]),
                    html.Tr([html.Td("CWR"), html.Td("Congestion Window Reduced"), html.Td("Sender reduced congestion window")])
                ])
            ], bordered=True, size="sm", hover=True, className="mb-4"),
            html.H4("Last 16 Messages"),
            html.Div(id="log-table"),
            html.Hr(),
            html.H5("Debug Log Info"),
            html.Pre(id="debug-output", style={"whiteSpace": "pre-wrap", "color": "#00FF00"})
        ]),

        dcc.Tab(label="Setup", children=[
            html.Br(),
            dbc.Container([
                html.H4("MITM Settings", className="mb-3"),
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
                ]),
                
                html.Hr(className="my-4"),
                
                html.H4("CNC Connection Settings", className="mb-4"),
                
                dbc.Row([
                    dbc.Col([
                        html.H5("Controller Settings", className="mb-3"),
                        dbc.Row([
                            dbc.Col([html.Label("Controller IP Address")], width=4),
                            dbc.Col([
                                dcc.Input(
                                    id="controller-ip",
                                    type="text",
                                    placeholder="10.9.0.5",
                                    className="form-control",
                                    value="10.9.0.5"
                                )
                            ], width=8)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([html.Label("Controller Port")], width=4),
                            dbc.Col([
                                dcc.Input(
                                    id="controller-port",
                                    type="number",
                                    placeholder="9090",
                                    className="form-control",
                                    value="9090"
                                )
                            ], width=8)
                        ])
                    ], width=6),
                    
                    dbc.Col([
                        html.H5("Firmware Settings", className="mb-3"),
                        dbc.Row([
                            dbc.Col([html.Label("Firmware IP Address")], width=4),
                            dbc.Col([
                                dcc.Input(
                                    id="firmware-ip",
                                    type="text",
                                    placeholder="10.9.0.6",
                                    className="form-control",
                                    value="10.9.0.6"
                                )
                            ], width=8)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([html.Label("Firmware Port")], width=4),
                            dbc.Col([
                                dcc.Input(
                                    id="firmware-port",
                                    type="number",
                                    placeholder="9090",
                                    className="form-control",
                                    value="9090"
                                )
                            ], width=8)
                        ])
                    ], width=6)
                ], className="mb-4"),
                
                dbc.Row([
                    dbc.Col([
                        html.Button(
                            "Connect", 
                            id="connect-btn", 
                            className="btn btn-primary",
                            style={"width": "100%"}
                        )
                    ], width={"size": 6, "offset": 3})
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        html.Div(id="simulator-status")
                    ], width=12, className="text-center")
                ])
            ])
        ]),
        
        # New Tab for Tool Path Visualization
        dcc.Tab(label="Tool Path Visualization", children=[
            dcc.Interval(id="tool-path-refresh", interval=3000, n_intervals=0),  # Refresh every 3 seconds
            html.Br(),
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H4("G-Code Tool Path Visualization", className="mb-3"),
                        html.P([
                            "This tab visualizes the detected G-code commands intercepted by the MITM proxy. ",
                            "Original tool paths are shown in blue, while modified paths appear in red."
                        ], className="mb-4"),
                        
                        # Information panel for G-codes
                        dbc.Card([
                            dbc.CardHeader("G-Code Information"),
                            dbc.CardBody([
                                html.P("Common G-codes in CNC operations:"),
                                dbc.Table([
                                    html.Thead(html.Tr([
                                        html.Th("Code"), html.Th("Name"), html.Th("Description")
                                    ])),
                                    html.Tbody([
                                        html.Tr([html.Td("G0"), html.Td("Rapid Move"), html.Td("Move quickly to position")]),
                                        html.Tr([html.Td("G1"), html.Td("Linear Move"), html.Td("Move in a straight line")]),
                                        html.Tr([html.Td("G2/G3"), html.Td("Arc Move"), html.Td("Move in a clockwise/counterclockwise arc")]),
                                        html.Tr([html.Td("G28"), html.Td("Home"), html.Td("Move to machine home position")]),
                                        html.Tr([html.Td("G90"), html.Td("Absolute Positioning"), html.Td("Coordinates are absolute")]),
                                        html.Tr([html.Td("G91"), html.Td("Relative Positioning"), html.Td("Coordinates are relative")])
                                    ])
                                ], bordered=True, size="sm", hover=True, className="mb-3"),
                                html.P([
                                    "In the ",
                                    html.Code("g1g0"), 
                                    " attack mode, G1 commands (controlled linear moves) are replaced with G0 commands (rapid moves), ",
                                    "potentially causing machine damage or ruining workpieces."
                                ])
                            ])
                        ], className="mb-4")
                    ], width=4),
                    dbc.Col([
                        # 3D visualization of tool path
                        dcc.Loading(
                            dcc.Graph(
                                id="tool-path-3d",
                                style={"height": "600px"},
                                config={'displayModeBar': True}
                            ),
                            type="circle"
                        ),
                        html.Div(id="tool-path-status", className="mt-2", style={"color": "#00FF00"})
                    ], width=8)
                ]),
                
                html.Hr(className="my-4"),
                
                dbc.Row([
                    dbc.Col([
                        html.H5("Controls", className="mb-3"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Update Interval (ms)"),
                            dbc.Input(
                                id="tool-path-update-interval",
                                type="number",
                                value=3000,
                                min=1000,
                                max=10000,
                                step=1000
                            ),
                            dbc.Button("Set", id="set-interval-btn", color="primary")
                        ], className="mb-3")
                    ], width=6),
                    
                    dbc.Col([
                        html.H5("Latest G-Code", className="mb-3"),
                        dbc.Card([
                            dbc.CardBody([
                                html.Div(id="latest-gcode-display", style={"font-family": "monospace"})
                            ])
                        ])
                    ], width=6)
                ])
            ])
        ]),
        
        dcc.Tab(label="Tool Path Simulator", children=[
            html.Br(),
            dbc.Container([
                html.H4("Tool Path Controls", className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        html.Div("Tool path simulation controls will appear here once connected to the CNC system.")
                    ], width=12)
                ])
            ])
        ]),
        
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
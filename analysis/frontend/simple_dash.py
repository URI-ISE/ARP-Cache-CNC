import os
import requests
import json
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# Simple Dash frontend that talks to the Flask/SocketIO dashboard API
# Run this separately (port 8050): python3 simple_dash.py

API_BASE = os.environ.get('DD_API_BASE', 'http://localhost:5000')

def get_status():
    try:
        r = requests.get(f"{API_BASE}/api/status", timeout=3)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def iptables_action(action):
    try:
        if action == 'enable':
            r = requests.post(f"{API_BASE}/api/iptables/setup", json={})
        else:
            r = requests.post(f"{API_BASE}/api/iptables/disable", json={})
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def connect_cnc(ip, port):
    try:
        r = requests.post(f"{API_BASE}/api/connect", json={'cnc_ip': ip, 'cnc_port': int(port)})
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def send_command(command, apply_attacks=False):
    try:
        r = requests.post(f"{API_BASE}/api/send_command", json={'command': command, 'apply_attacks': apply_attacks})
        return r.json()
    except Exception as e:
        return {'error': str(e)}


external_stylesheets = [dbc.themes.DARKLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = dbc.Container(
    [
        html.H2("Doom-and-Gloom — Simple Frontend", style={'textAlign': 'center', 'marginTop': '10px'}),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Network / IPTables"),
                            dbc.CardBody(
                                [
                                    dbc.Row([
                                        dbc.Col(dbc.Input(id='cnc-ip', placeholder='CNC IP', type='text')),
                                        dbc.Col(dbc.Input(id='cnc-port', placeholder='CNC port', type='number', value=8080)),
                                    ], className='mb-2'),
                                    dbc.Button("Connect CNC", id='connect-btn', color='primary', className='me-2'),
                                    dbc.Button("Enable IPTables", id='iptables-enable', color='danger', className='me-2'),
                                    dbc.Button("Disable IPTables", id='iptables-disable', color='secondary'),
                                    html.Hr(),
                                    html.Div(id='iptables-result', style={'whiteSpace': 'pre-wrap', 'marginTop': '8px'})
                                ]
                            )
                        ]
                    ), width=6
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Status & Stats"),
                            dbc.CardBody(
                                [
                                    dbc.Button("Refresh Status", id='refresh-status', color='info'),
                                    html.Div(id='status-output', style={'whiteSpace': 'pre-wrap', 'marginTop': '8px'})
                                ]
                            )
                        ]
                    ), width=6
                )
            ]
        ),
        html.Hr(),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Send CNC Command"),
                    dbc.CardBody([
                        dbc.Textarea(id='cnc-command', placeholder='G-code or command', style={'width':'100%', 'height':'120px'}),
                        dbc.Checklist(options=[{'label':'Apply attacks', 'value':'apply'}], value=[], id='apply-attacks', inline=True),
                        dbc.Button('Send', id='send-cmd', color='primary', className='mt-2'),
                        html.Div(id='command-result', style={'whiteSpace': 'pre-wrap', 'marginTop': '8px'})
                    ])
                ]), width=12
            )
        ]),
        html.Footer(f"API base: {API_BASE} — Generated: {datetime.utcnow().isoformat()}", style={'marginTop':'20px','color':'#888'})
    ], fluid=True
)


@app.callback(
    Output('status-output', 'children'),
    Input('refresh-status', 'n_clicks')
)
def on_refresh(n):
    s = get_status()
    return json.dumps(s, indent=2)


@app.callback(
    Output('iptables-result', 'children'),
    Input('iptables-enable', 'n_clicks'),
    Input('iptables-disable', 'n_clicks')
)
def on_iptables(enable_clicks, disable_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ''
    btn = ctx.triggered[0]['prop_id'].split('.')[0]
    if btn == 'iptables-enable':
        r = iptables_action('enable')
    else:
        r = iptables_action('disable')
    return json.dumps(r, indent=2)


@app.callback(
    Output('command-result', 'children'),
    Input('send-cmd', 'n_clicks'),
    State('cnc-command', 'value'),
    State('apply-attacks', 'value')
)
def on_send(n, cmd, apply_val):
    if not n:
        return ''
    if not cmd:
        return 'No command supplied.'
    r = send_command(cmd, apply_attacks=('apply' in (apply_val or [])))
    return json.dumps(r, indent=2)


@app.callback(
    Output('cnc-ip', 'value'),
    Output('cnc-port', 'value'),
    Input('connect-btn', 'n_clicks'),
    State('cnc-ip', 'value'),
    State('cnc-port', 'value')
)
def on_connect(n, ip, port):
    if not n:
        # try to pre-fill from status
        s = get_status()
        cfg = s.get('network_config', {}) if isinstance(s, dict) else {}
        return cfg.get('cnc_ip', ''), cfg.get('cnc_port', 8080)
    # perform connect
    r = connect_cnc(ip or '', port or 8080)
    return ip, port


if __name__ == '__main__':
    print(f"Starting simple Dash frontend (connects to {API_BASE}) on http://0.0.0.0:8050")
    app.run_server(host='0.0.0.0', port=8050)

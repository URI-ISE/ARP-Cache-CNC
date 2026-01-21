"""
app.py - Attack Control and Visualization Dashboard
Author: luke pepin
Description: Flask app for controlling attacks and visualizing G-Code toolpaths in real-time.
"""

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)

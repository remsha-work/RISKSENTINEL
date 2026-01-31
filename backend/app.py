import os
from flask import Flask, render_template, redirect, url_for

# Flask finds templates/ automatically from project root when run from backend
app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
           static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))

@app.route('/landing')
def landing(): 
    return render_template('landing.html')

@app.route('/')
def index():
    return redirect(url_for('landing'))

@app.route('/login')
def login():
    return '<h1>Login Page Coming Soon!</h1>'

@app.route('/vendor_register')
def vendor_register():
    return '<h1>Vendor Register Coming Soon!</h1>'

@app.route('/contact', methods=['POST'])  # ADD THIS for HTMX form
def contact():
    return '<div class="text-green-600 font-bold text-lg p-4 bg-green-100 rounded-lg border border-green-400">Thank you! Message sent successfully! 🎉</div>'

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')

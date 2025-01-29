# filepath: /c:/Users/DrPower/OneDrive/Documents/code/Gestion projet/my-flask-app/app.py
from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Handle login logic here
        return redirect(url_for('home'))
    return render_template('connexion.html')

@app.route('/inscription')
def inscription():
    return render_template('inscription.html')

@app.route('/')
def home():
    return redirect(url_for('connexion'))

if __name__ == '__main__':
    app.run(debug=True)
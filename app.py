from flask import Flask, render_template, request, redirect, session, flash
import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import mysql.connector

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Créer le dossier s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = load_model("model/vgg16_skin_cancer.h5")

# CONNEXION MYSQL (lazy - se connecte seulement quand nécessaire)
db = None
cursor = None

def get_db():
    global db, cursor
    try:
        if db is None or not db.is_connected():
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="skin_cancer_db"
            )
            cursor = db.cursor(dictionary=True)
    except mysql.connector.Error as e:
        print(f"⚠️  MySQL non disponible: {e}")
        db = None
        cursor = None
    return db, cursor

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        # Correction: AND au lieu de AID
        db, cursor = get_db()
        if cursor is None:
            flash("Base de données non disponible", "danger")
            return render_template("login.html")
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (user, pwd))
        result = cursor.fetchone()

        if result:
            session["user"] = user
            flash("Login réussi ✓", "success")
            return redirect("/dashboard")
        else:
            flash("Erreur login ✗", "danger")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            name = request.form["name"]
            age = request.form["age"]
            file = request.files["image"]

            if file.filename == "":
                flash("Veuillez choisir une image", "warning")
                return redirect("/predict")

            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)

            # Normalize path for web (forward slashes)
            web_path = path.replace("\\", "/")

            img = image.load_img(path, target_size=(224, 224))
            img = image.img_to_array(img) / 255.0
            img = np.expand_dims(img, axis=0)

            pred = model.predict(img)[0][0]
            result = "Malignant" if pred > 0.5 else "Benign"

            db, cursor = get_db()
            if cursor:
                cursor.execute("""INSERT INTO patients (name, age, result, probability, image_path)
                                VALUES (%s, %s, %s, %s, %s)""",
                               (name, age, result, float(pred), web_path))
                db.commit()

            flash("Analyse réussie ✓", "success")

            return render_template("result.html",
                                   result=result,
                                   prob=round(pred * 100, 2),
                                   img=web_path)

        except Exception as e:
            print(f"Erreur: {e}")  # Pour debug
            flash(f"Erreur système: {str(e)}", "danger")
            return redirect("/predict")

    return render_template("predict.html")

@app.route("/patients")
def patients():
    if "user" not in session:
        return redirect("/")
    
    db, cursor = get_db()
    if cursor is None:
        flash("Base de données non disponible", "danger")
        return render_template("patients.html", patients=[])
    cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
    data = cursor.fetchall()
    return render_template("patients.html", patients=data)

@app.route("/logout")
def logout():
    session.clear()
    flash("Déconnecté", "info")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
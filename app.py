from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import users, save_history, get_history
from datetime import datetime
from deep_translator import GoogleTranslator
import webbrowser
from chatbot_engine import get_bot_response
app = Flask(__name__, template_folder='templates', static_folder='static')
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = "ai_allergy_secret"

# ---------------- HELPER FUNCTIONS ----------------

def risk_score(history_count, severity):
    if severity == "High":
        score = 90
    elif severity == "Medium":
        score = 60
    else:
        score = 30
    score += min(history_count * 2, 10)
    return min(score, 100)

def explain_prediction(text):
    text = text.lower()
    reasons = []
    if "rash" in text or "itch" in text:
        reasons.append("Detected skin-related symptoms")
    if "milk" in text:
        reasons.append("Milk trigger identified")
    if "dust" in text:
        reasons.append("Dust exposure detected")
    if "breathing" in text:
        reasons.append("Respiratory issue detected")
    if not reasons:
        reasons.append("General symptom-based prediction")
    return reasons

food_map = {
    "cake": ["milk","egg","wheat"],
    "pizza": ["cheese","wheat"],
    "burger": ["bread","cheese"],
    "ice cream": ["milk"]
}

def classify_allergy(text):
    if not text:
        return "Environmental Allergy"
    text = text.lower()
    skin_keywords = ["rash","itch","redness","swelling","burn","skin"]
    env_keywords = ["dust","pollen","smoke","pollution","pet","mold","breathing"]
    food_keywords = ["milk","peanut","egg","fish","prawn","food","wheat","soy"]
    if any(k in text for k in skin_keywords):
        return "Skin Allergy"
    elif any(k in text for k in env_keywords):
        return "Environmental Allergy"
    elif any(k in text for k in food_keywords):
        return "Food Allergy"
    return "Environmental Allergy"

def severity_level(text):
    if not text:
        return "Low"
    text = text.lower()
    severe = ["breathing","vomiting","severe","anaphylaxis"]
    medium = ["rash","itch","hives","redness"]
    if any(k in text for k in severe):
        return "High"
    elif any(k in text for k in medium):
        return "Medium"
    return "Low"

trigger_keywords = {

# FOOD (20+)
"milk":"milk","cheese":"milk","butter":"milk","curd":"milk","paneer":"milk","yogurt":"milk",
"cream":"milk","peanut":"peanut","groundnut":"peanut","nut":"peanut","almond":"peanut",
"cashew":"peanut","egg":"egg","omelette":"egg","mayonnaise":"egg",
"prawn":"seafood","shrimp":"seafood","crab":"seafood","fish":"seafood","tuna":"seafood",
"wheat":"gluten","bread":"gluten","cake":"gluten","biscuit":"gluten","pasta":"gluten",
"soy":"soy","soybean":"soy","tofu":"soy",

# ENVIRONMENT (15+)
"dust":"dust","pollen":"pollen","smoke":"smoke","pollution":"pollution",
"vehicle smoke":"smoke","factory smoke":"smoke",
"pet":"pet","dog":"pet","cat":"pet","animal fur":"pet",
"mold":"mold","fungus":"mold","humidity":"mold",

# SKIN (15+)
"soap":"soap","detergent":"soap","shampoo":"shampoo","facewash":"soap",
"cosmetic":"cosmetic","makeup":"cosmetic","foundation":"cosmetic","lipstick":"cosmetic",
"perfume":"perfume","deodorant":"perfume",
"lotion":"cream","moisturizer":"cream",
"chemical":"chemical","acid":"chemical",
"metal":"metal","jewelry":"metal",
"fabric":"fabric","wool":"fabric","synthetic":"fabric"
}

def detect_triggers(text):
    if not text:
        return ["general"]

    text = text.lower()
    found = []

    for key in trigger_keywords:
        if key in text:
            found.append(trigger_keywords[key])

    return list(set(found)) if found else ["general"]

def get_recommendations(triggers):

    data = {
        "milk": ["Avoid dairy products","Check labels","Use plant milk","Avoid sweets","Consult doctor"],
        "peanut": ["Avoid peanuts","Read labels","Carry medicine","Avoid outside food","Inform others"],
        "seafood": ["Avoid seafood","Check restaurants","Avoid cross-contact","Monitor reactions","Consult doctor"],
        "dust": ["Avoid dust","Wear mask","Use purifier","Clean house","Close windows"],
        "pollen": ["Avoid outdoor exposure","Close windows","Take medicine","Wash face","Wear sunglasses"],
        "soap": ["Use mild soap","Avoid chemicals","Patch test","Use safe products","Limit use"]
    }

    result = []
    for t in triggers:
        if t in data:
            result.extend(data[t])

    return result if result else ["Avoid triggers","Monitor symptoms","Consult doctor"]

def get_lifestyle_tips(triggers):

    tips = {
        "milk": ["Use dairy-free diet","Eat calcium foods","Balanced diet","Avoid processed dairy","Track symptoms"],
        "peanut": ["Carry medicine","Avoid unknown foods","Educate family","Check ingredients","Eat safe"],
        "dust": ["Clean regularly","Wash bedsheets","Avoid carpets","Use vacuum","Maintain hygiene"],
        "pollen": ["Shower after outside","Avoid morning exposure","Use purifier","Stay indoors","Wear mask"],
        "soap": ["Use natural products","Avoid chemicals","Moisturize skin","Drink water","Maintain hygiene"]
    }

    result = []
    for t in triggers:
        if t in tips:
            result.extend(tips[t])

    return result if result else ["Maintain healthy lifestyle","Avoid triggers","Stay safe"]
def apply_features(text, username):
    if any('\u0B80'<=ch<='\u0BFF' for ch in text):
        try:
            text = GoogleTranslator(source='ta', target='en').translate(text)
        except:
            pass

    text = text.lower()
    ingredients = []
    if text in food_map:
        ingredients = food_map[text]
        text = " ".join(ingredients)

    allergy = classify_allergy(text)
    severity = severity_level(text)
    triggers = detect_triggers(text)
    recommendation = get_recommendations(triggers)
    lifestyle = get_lifestyle_tips(triggers)
    history_count = len(list(get_history(username)))
    score = risk_score(history_count, severity)
    reasons = explain_prediction(text)
    alert = "⚠️ EMERGENCY: Severe Allergy Detected!" if severity=="High" else None

    return allergy, severity, recommendation, lifestyle, score, reasons, ingredients, alert

# ---------------- LEVEL 2 FUNCTIONS ----------------
def frequent_trigger(username):
    records = list(get_history(username))
    counts = {}
    for r in records:
        t = r.get("allergy")
        counts[t] = counts.get(t,0)+1
    if not counts:
        return "None"
    return max(counts, key=counts.get)

def allergy_dna_profile(username):
    records = list(get_history(username))
    total = len(records)
    profile = {}
    for r in records:
        a = r["allergy"]
        profile[a] = profile.get(a,0)+1
    for k in profile:
        profile[k] = round((profile[k]/total)*100, 1) if total>0 else 0
    return profile

def trend_graph_data(username):
    records = list(get_history(username))
    chart_data = []
    for r in records:
        sev = r.get("severity")
        if sev=="High":
            chart_data.append(90)
        elif sev=="Medium":
            chart_data.append(60)
        else:
            chart_data.append(30)
    return chart_data

# ---------------- LEVEL 2 AI ADDITIONS ----------------

def smart_learning(username):
    records = list(get_history(username))
    if not records:
        return "No allergy history yet."
    high = sum(1 for r in records if r["severity"] == "High")
    medium = sum(1 for r in records if r["severity"] == "Medium")
    if high >= 3:
        return "⚠ Frequent severe allergies detected."
    elif medium >= 3:
        return "⚠ Moderate allergy pattern detected."
    else:
        return "✅ Allergy risk currently stable."

def risk_forecast(username):
    records = list(get_history(username))
    if len(records) < 2:
        return "Stable"
    last = records[0]["severity"]
    prev = records[1]["severity"]
    if last == "High" and prev == "Medium":
        return "Likely Increase"
    elif last == "Low":
        return "Low Risk"
    else:
        return "Moderate Risk"

# ---------------- LEVEL 3 AI FEATURES ----------------

def prevention_advisor(trigger):
    if trigger == "Food Allergy":
        return "Avoid dairy products, nuts, and processed foods."
    elif trigger == "Skin Allergy":
        return "Avoid chemical cosmetics and harsh soaps."
    elif trigger == "Environmental Allergy":
        return "Avoid dust and pollen exposure. Wear a mask outside."
    else:
        return "Monitor symptoms and avoid unknown triggers."

def emergency_alert_system(severity):
    if severity == "High":
        return "⚠ Emergency Alert: Severe allergy detected!"
    elif severity == "Medium":
        return "⚠ Moderate allergy risk. Take precautions."
    else:
        return "No emergency risk."

def recommendation_engine(allergy):
    if allergy == "Food Allergy":
        return ["Almond milk", "Soy milk", "Oat milk"]
    elif allergy == "Skin Allergy":
        return ["Aloe vera gel", "Hypoallergenic soap", "Organic cream"]
    elif allergy == "Environmental Allergy":
        return ["Air purifier", "Anti-allergy mask", "Dust filters"]
    else:
        return ["Avoid allergens", "Stay hydrated", "Consult doctor if symptoms increase"]

# ---------------- ROOT REDIRECT ----------------
@app.route("/")
def index():
    return redirect(url_for("login"))

# ---------------- LOGIN / LOGOUT ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["user"] = username
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ---------------- SIGNUP / REGISTER ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["user"] = username
            return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    return redirect(url_for("signup"))

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    history = list(get_history(username))
    if history:
        last_severity = history[-1]["severity"]
        risk = risk_score(len(history), last_severity)
    else:
        risk = 0
    frequent = frequent_trigger(username)
    dna_profile = allergy_dna_profile(username)
    trend_data = trend_graph_data(username)
    return render_template("dashboard.html", risk=risk, history=history, frequent=frequent, dna_profile=dna_profile, trend_data=trend_data)

# ---------------- PREDICT / VOICE / IMAGE ----------------
@app.route("/predict", methods=["GET","POST"])
def predict():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method=="POST":
        text=request.form.get("user_input")
        if not text:
            return render_template("predict.html")
        allergy, severity, recommendation, lifestyle, score, reasons, ingredients, alert = apply_features(text, session["user"])
        save_history({
            "username":session["user"],
            "input":text,
            "allergy":allergy,
            "severity":severity,
            "date":datetime.now().strftime("%d-%m-%Y %I:%M %p")
        })
        return render_template("result.html",
            allergy=allergy,
            severity=severity,
            score=score,
            reasons=reasons,
            ingredients=ingredients,
            alert=alert,
            recommendations=recommendation,
            lifestyle_tips=lifestyle
        )
    return render_template("predict.html")

@app.route("/voice", methods=["GET","POST"])
def voice():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method=="POST":
        text = request.form.get("voice_text")
        if not text:
            return render_template("voice.html", message="Voice not captured")
        allergy, severity, recommendation, lifestyle, score, reasons, ingredients, alert = apply_features(text, session["user"])
        save_history({
            "username": session["user"],
            "input": text,
            "allergy": allergy,
            "severity": severity,
            "date": datetime.now().strftime("%d-%m-%Y %I:%M %p")
        })
        return render_template("result.html",
            allergy=allergy,
            severity=severity,
            score=score,
            reasons=reasons,
            ingredients=ingredients,
            alert=alert,
            recommendations=recommendation,
            lifestyle_tips=lifestyle
        )
    return render_template("voice.html")

@app.route("/image", methods=["GET","POST"])
def image():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method=="POST":
        file=request.files.get("image")
        if file and file.filename:
            text=file.filename
            allergy, severity, recommendation, lifestyle, score, reasons, ingredients, alert = apply_features(text, session["user"])
            save_history({
                "username":session["user"],
                "input":text,
                "allergy":allergy,
                "severity":severity,
                "date":datetime.now().strftime("%d-%m-%Y %I:%M %p")
            })
            return render_template("result.html",
                allergy=allergy,
                severity=severity,
                score=score,
                reasons=reasons,
                ingredients=ingredients,
                alert=alert,
                recommendations=recommendation,
                lifestyle_tips=lifestyle
            )
    return render_template("image.html")

# ---------------- HISTORY / PROFILE ----------------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    records = list(get_history(username))
    return render_template("history.html", records=records)

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    total = len(list(get_history(username)))
    return render_template("profile.html", username=username, total=total)

# ---------------- CHATBOT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "")

    reply = get_bot_response(msg)

    return jsonify({"reply": reply})
# ---------------- RUN APP ----------------
if __name__ == "__main__":
    webbrowser.open("http://localhost:5050/login")
    app.run(debug=True, port=5050)

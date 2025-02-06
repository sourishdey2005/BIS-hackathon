import streamlit as st
import hashlib
import sqlite3
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract

# --- API CONFIGURATION --- (Using Gemini API Key for health risk prediction)
GEMINI_API_KEY = "AIzaSyDOvM48IMxod_4SvEttajKXcVDblmKHyPk"  # Replace with your actual Gemini API key
genai.configure(api_key=GEMINI_API_KEY)

# Database setup (Simulated)
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Register user
def register_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# Authenticate user
def authenticate_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    record = c.fetchone()
    conn.close()
    return record and record[0] == hash_password(password)

# Function to send data to Gemini AI for health risk prediction
def get_health_risk_prediction(user_data):
    model = genai.GenerativeModel("gemini-pro")
    prompt = (
        "Given the following health data, predict the health risk score (1-100), provide preventive tips, "
        "suggest a suitable diet plan and recommend an exercise routine: "
        f"Age: {user_data['age']}, Weight: {user_data['weight']} kg, Height: {user_data['height']} cm, "
        f"Smoking: {user_data['smoking']}, Alcohol: {user_data['alcohol']}, Exercise: {user_data['exercise']}, "
        f"Diet: {user_data['diet']}, Sleep Hours: {user_data['sleep_hours']}, Stress Level: {user_data['stress_level']}, "
        f"Medical History: {', '.join(user_data['medical_history'])}."
    )

    # Simulating API call (Placeholder for actual interaction with Gemini API)
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return {
                "risk_score": "Predicted risk score based on AI", 
                "preventive_tips": response.text.split("\n"),
                "diet_plan": "Recommended diet plan based on AI analysis",
                "exercise_plan": "Recommended exercise plan based on AI analysis"
            }
        else:
            return {"error": "Failed to fetch prediction from Gemini AI"}
    except Exception as e:
        return {"error": f"Error interacting with Gemini AI: {str(e)}"}

# Function to display health trends
def display_health_trends():
    data = {
        "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "Risk Score": [30, 40, 35, 50, 45, 55]
    }
    df = pd.DataFrame(data)
    plt.figure(figsize=(8, 4))
    plt.plot(df["Month"], df["Risk Score"], marker='o', linestyle='-', color='b')
    plt.xlabel("Month")
    plt.ylabel("Risk Score")
    plt.title("Health Risk Trends Over Time")
    st.pyplot(plt)

# Function to extract text from image
def extract_prescription_text(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return str(e)

# Streamlit UI
def main():
    st.title("Personalized Health Risk Predictor (Prototype with Gemini API)")

    # Apply custom styling for better UI
    st.markdown("""
        <style>
            .css-18e3th9 {padding-top: 20px; padding-bottom: 20px;}
        </style>
    """, unsafe_allow_html=True)

    init_db()
    menu = ["Login", "Register", "Predict", "Consult Doctor", "Upload Prescription"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Register":
        st.subheader("Create an Account (Prototype)")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(username, password):
                st.success("Registration successful! You can now log in.")
            else:
                st.error("Username already exists. Try another one.")
    
    elif choice == "Login":
        st.subheader("Login to Your Account (Prototype)")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Login successful!")
            else:
                st.error("Invalid credentials.")
    
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        st.sidebar.header("User Information")
        age = st.sidebar.number_input("Age", min_value=1, max_value=120, value=30)
        weight = st.sidebar.number_input("Weight (kg)", min_value=10, max_value=200, value=70)
        height = st.sidebar.number_input("Height (cm)", min_value=50, max_value=250, value=170)
        smoking = st.sidebar.selectbox("Smoking Habits", ["Non-Smoker", "Occasional Smoker", "Regular Smoker"])
        alcohol = st.sidebar.selectbox("Alcohol Consumption", ["No", "Occasionally", "Regularly"])
        exercise = st.sidebar.selectbox("Exercise Frequency", ["Sedentary", "Occasional", "Regular"])
        diet = st.sidebar.selectbox("Diet Type", ["Balanced", "High Sugar", "High Fat", "Vegan"])
        sleep_hours = st.sidebar.slider("Sleep Hours per Night", 3, 12, 7)
        stress_level = st.sidebar.slider("Stress Level (1-10)", 1, 10, 5)
        medical_history = st.sidebar.text_area("Medical History (comma separated)")

        user_data = {
            "age": age,
            "weight": weight,
            "height": height,
            "smoking": smoking,
            "alcohol": alcohol,
            "exercise": exercise,
            "diet": diet,
            "sleep_hours": sleep_hours,
            "stress_level": stress_level,
            "medical_history": medical_history.split(",")
        }

        if st.sidebar.button("Predict Health Risk"):
            result = get_health_risk_prediction(user_data)
            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader("Health Risk Prediction")
                st.write(f"Risk Score: {result.get('risk_score', 'N/A')}")
                st.write("Preventive Tips:")
                for tip in result.get("preventive_tips", []):
                    st.write(f"- {tip}")
                st.write(f"Diet Plan: {result.get('diet_plan', 'N/A')}")
                st.write(f"Exercise Plan: {result.get('exercise_plan', 'N/A')}")

        st.sidebar.header("Additional Features")
        if st.sidebar.button("View Health Trends"):
            display_health_trends()

        # Upload Prescription
        uploaded_file = st.file_uploader("Upload a Prescription (Image/PDF)", type=["jpg", "jpeg", "png", "pdf"])
        if uploaded_file:
            text = extract_prescription_text(uploaded_file)
            st.subheader("Extracted Prescription Details")
            st.write(text)

if __name__ == "__main__":
    main()

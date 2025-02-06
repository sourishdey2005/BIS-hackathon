import streamlit as st
import hashlib
import sqlite3
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import pytesseract
import random
import base64

# --- API CONFIGURATION --- (Using Gemini API Key for health risk prediction)
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Replace with your actual Gemini API key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Database
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY, username TEXT, hospital TEXT, doctor TEXT, 
                    date TEXT, time TEXT, status TEXT)""")
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

# Health Risk Prediction using Gemini AI
def get_health_risk_prediction(user_data):
    model = genai.GenerativeModel("gemini-pro")
    prompt = (
        "You are an AI health assistant. Based on the following health data, "
        "predict a health risk score (1-100), provide preventive tips, a diet plan, and an exercise routine.\n\n"
        f"Age: {user_data['age']}, Weight: {user_data['weight']} kg, Height: {user_data['height']} cm, "
        f"Smoking: {user_data['smoking']}, Alcohol: {user_data['alcohol']}, Exercise: {user_data['exercise']}, "
        f"Diet: {user_data['diet']}, Sleep Hours: {user_data['sleep_hours']}, Stress Level: {user_data['stress_level']}, "
        f"Medical History: {', '.join(user_data['medical_history'])}.\n\n"
        "Provide responses in this format:\n"
        "Risk Score: [Number]\n"
        "Preventive Tips:\n- Tip 1\n- Tip 2\n"
        "Diet Plan: [Diet details]\n"
        "Exercise Plan: [Exercise details]"
    )

    try:
        response = model.generate_content(prompt)
        if response and response.text:
            result = response.text.split("\n")
            risk_score = next((line.split(": ")[1] for line in result if line.startswith("Risk Score")), "N/A")
            preventive_tips = [line for line in result if line.startswith("- ")]
            diet_plan = next((line.split(": ")[1] for line in result if line.startswith("Diet Plan")), "N/A")
            exercise_plan = next((line.split(": ")[1] for line in result if line.startswith("Exercise Plan")), "N/A")

            return {
                "risk_score": risk_score,
                "preventive_tips": preventive_tips,
                "diet_plan": diet_plan,
                "exercise_plan": exercise_plan
            }
        else:
            return {"error": "Failed to fetch prediction from Gemini AI"}
    except Exception as e:
        return {"error": f"Error interacting with Gemini AI: {str(e)}"}

# Doctor Booking Function
def book_appointment(username, hospital, doctor, date, time):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO bookings (username, hospital, doctor, date, time, status) VALUES (?, ?, ?, ?, ?, ?)",
              (username, hospital, doctor, date, time, "Confirmed"))
    conn.commit()
    conn.close()
    return True

# Get User Bookings
def get_user_bookings(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT hospital, doctor, date, time, status FROM bookings WHERE username = ?", (username,))
    bookings = c.fetchall()
    conn.close()
    return bookings

# Process Payment (Simulation)
def process_payment():
    return random.choice(["Payment Successful", "Payment Failed"])

# Extract Text from Prescription Image
def extract_prescription_text(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return str(e)

# Generate Video Call Link
def generate_video_call_link():
    return "https://meet.jit.si/DoctorConsultationRoom"

# Streamlit UI
def main():
    st.title("Health Risk Predictor & Doctor Booking System")

    init_db()
    menu = ["Login", "Register", "Predict", "Consult Doctor", "Upload Prescription", "Video Call"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Register":
        st.subheader("Create an Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(username, password):
                st.success("Registration successful! You can now log in.")
            else:
                st.error("Username already exists. Try another one.")

    elif choice == "Login":
        st.subheader("Login to Your Account")
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
        username = st.session_state["username"]
        st.sidebar.header(f"Welcome, {username}")

        if choice == "Predict":
            st.subheader("Health Risk Prediction")
            user_data = {
                "age": st.number_input("Age", 1, 120, 30),
                "weight": st.number_input("Weight (kg)", 10, 200, 70),
                "height": st.number_input("Height (cm)", 50, 250, 170),
                "smoking": st.selectbox("Smoking", ["Non-Smoker", "Occasional Smoker", "Regular Smoker"]),
                "alcohol": st.selectbox("Alcohol", ["No", "Occasionally", "Regularly"]),
                "exercise": st.selectbox("Exercise", ["Sedentary", "Occasional", "Regular"]),
                "diet": st.selectbox("Diet", ["Balanced", "High Sugar", "High Fat", "Vegan"]),
                "sleep_hours": st.slider("Sleep Hours", 3, 12, 7),
                "stress_level": st.slider("Stress Level", 1, 10, 5),
                "medical_history": st.text_area("Medical History").split(","),
            }

            if st.button("Predict Health Risk"):
                result = get_health_risk_prediction(user_data)
                st.write(result)

        elif choice == "Upload Prescription":
            uploaded_file = st.file_uploader("Upload a Prescription", type=["jpg", "jpeg", "png"])
            if uploaded_file:
                text = extract_prescription_text(uploaded_file)
                st.subheader("Extracted Text")
                st.write(text)

        elif choice == "Video Call":
            st.subheader("Join a Doctor Video Consultation")
            st.markdown(f"[Click here to join](https://meet.jit.si/DoctorConsultationRoom)")

if __name__ == "__main__":
    main()

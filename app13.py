import streamlit as st
import hashlib
import sqlite3
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt
import easyocr
import random
import datetime
import webbrowser
import requests
import json

# --- API CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyDOvM48IMxod_4SvEttajKXcVDblmKHyPk"  # Replace with your actual Gemini API key
genai.configure(api_key=GEMINI_API_KEY)

# Database setup
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

# Doctor booking function
def book_appointment(username, hospital, doctor, date, time):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO bookings (username, hospital, doctor, date, time, status) VALUES (?, ?, ?, ?, ?, ?)",
              (username, hospital, doctor, date, time, "Confirmed"))
    conn.commit()
    conn.close()
    return True

# Function to display past bookings
def get_user_bookings(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT hospital, doctor, date, time, status FROM bookings WHERE username = ?", (username,))
    bookings = c.fetchall()
    conn.close()
    return bookings

# Payment simulation
def process_payment():
    return random.choice(["Payment Successful", "Payment Failed"])

# Function to extract text from prescription using EasyOCR
def extract_text_from_image(image):
    reader = easyocr.Reader(["en"])
    result = reader.readtext(image, detail=0)
    return "\n".join(result)

# Function to start video call using Jitsi Meet
def start_video_call():
    meeting_link = "https://meet.jit.si/DoctorConsultation"  # Fixed meeting link
    st.markdown(f"[Click here to start video call]({meeting_link})")
    webbrowser.open(meeting_link)

# Function to predict health risk using Gemini AI
def get_health_risk_prediction(user_data):
    model = genai.GenerativeModel("gemini-pro")

    prompt = (
        "You are an AI health assistant. Based on the following health data, "
        "predict a health risk score (1-100), give preventive tips, suggest a diet plan, and an exercise routine.\n\n"
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

        if choice == "Consult Doctor":
            st.subheader("Book a Doctor Appointment")

            hospitals = ["City Hospital", "Metro Care", "Sunshine Medical", "Greenfield Clinic", "Elite Healthcare",
                         "MediHope Hospital", "Wellness Center", "Global Hospital", "Apollo Med", "MedLife"]
            doctors = ["Dr. Smith", "Dr. Johnson", "Dr. Patel", "Dr. Brown", "Dr. Davis",
                       "Dr. Wilson", "Dr. Lee", "Dr. Martin", "Dr. Clark", "Dr. Lewis"]

            hospital = st.selectbox("Select Hospital", hospitals)
            doctor = st.selectbox("Select Doctor", doctors)
            date = st.date_input("Select Date", datetime.date.today())
            time = st.selectbox("Select Time", ["10:00 AM", "12:00 PM", "3:00 PM", "5:00 PM"])

            if st.button("Confirm Booking"):
                payment_status = process_payment()
                if payment_status == "Payment Successful":
                    book_appointment(username, hospital, doctor, date, time)
                    st.success(f"Booking Confirmed with {doctor} at {hospital} on {date} at {time}")
                else:
                    st.error("Payment Failed! Try again.")

        if choice == "Upload Prescription":
            st.subheader("Upload Prescription")
            uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
            if uploaded_file:
                extracted_text = extract_text_from_image(uploaded_file)
                st.subheader("Extracted Text")
                st.write(extracted_text)

        if choice == "Video Call":
            st.subheader("Start Video Consultation")
            start_video_call()

        if choice == "Predict":

            st.subheader("Personalized Health Risk Predictor")
    
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
            if st.button("Predict Health Risk"):
                result = get_health_risk_prediction(user_data)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.subheader("Health Risk Prediction")
                    st.write(f"Risk Score: {result.get('risk_score', 'N/A')}")
                    st.write("Preventive Tips:")
                    for tip in result.get("preventive_tips", []):
                        st.write(f"- {tip}")
            st.header("Additional Features")
            if st.button("View Health Trends"):
                display_health_trends()



if __name__ == "__main__":
    main()
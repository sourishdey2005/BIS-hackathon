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
import uuid  # For transaction IDs
from dataclasses import dataclass

# --- API CONFIGURATION ---
GEMINI_API_KEY = "YOUR_ACTUAL_API_KEY"  # Replace with your actual Gemini API key
genai.configure(api_key=GEMINI_API_KEY)

# --- Data Classes ---
@dataclass
class User:
    id: int
    username: str
    balance: float = 0.0

@dataclass
class Booking:
    id: int
    username: str
    hospital: str
    doctor: str
    date: str
    time: str
    status: str

# --- Session State Keys ---
SESSION_KEYS = {
    "logged_in": "logged_in",
    "username": "username",
    "user": "user",
    "booking_cost": "booking_cost",
}

# Database setup
def init_db():
    conn = sqlite3.connect("health_app.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, balance REAL DEFAULT 0.0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY, transaction_id TEXT, username TEXT, hospital TEXT, doctor TEXT, 
                    date TEXT, time TEXT, status TEXT, cost REAL)""")
    conn.commit()
    conn.close()

# --- Authentication & User Management ---
# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Register user
def register_user(username, password):
    conn = sqlite3.connect("health_app.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, hash_password(password), 100.0))  # Initial balance
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# Authenticate user
def authenticate_user(username, password):
    conn = sqlite3.connect("health_app.db")
    c = conn.cursor()
    c.execute("SELECT id, password, balance FROM users WHERE username = ?", (username,))
    record = c.fetchone()
    conn.close()
    if record and record[1] == hash_password(password):
        user = User(id=record[0], username=username, balance=record[2])
        return user
    return None

# --- Doctor Booking & Payment ---
def calculate_booking_cost(hospital, doctor):
    cost = random.randint(50, 200)
    return cost

# Doctor booking function
def book_appointment(username, hospital, doctor, date, time, cost):
    conn = sqlite3.connect("health_app.db")
    c = conn.cursor()
    transaction_id = str(uuid.uuid4())
    try:
        c.execute(
            "INSERT INTO bookings (transaction_id, username, hospital, doctor, date, time, status, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (transaction_id, username, hospital, doctor, date, time, "Confirmed", cost),
        )
        conn.commit()
        conn.close()
        return transaction_id, True
    except Exception as e:
        conn.rollback()
        conn.close()
        st.error(f"Error during booking: {e}")
        return None, False

# Function to display past bookings
def get_user_bookings(username):
    conn = sqlite3.connect("health_app.db")
    c = conn.cursor()
    c.execute("SELECT hospital, doctor, date, time, status, cost, transaction_id FROM bookings WHERE username = ?", (username,))
    bookings = c.fetchall()
    conn.close()
    return bookings

# --- EasyOCR for Prescription ---
def extract_text_from_image(image):
    reader = easyocr.Reader(["en"])
    try:
        result = reader.readtext(image, detail=0)
        return "\n".join(result)
    except Exception as e:
        return f"Error during OCR processing: {e}"

# --- Video Call with Jitsi Meet ---
def start_video_call():
    meeting_link = "https://meet.jit.si/DoctorConsultation"
    st.markdown(f"[Click here to start video call]({meeting_link})")
    webbrowser.open(meeting_link)

# --- Gemini AI for Health Risk Prediction ---
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

# --- Health Trend Visualization ---
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

# --- Nearby Pharmacy Suggestions ---
def suggest_nearby_pharmacies(user_location):
    pharmacies = ["Local Pharmacy A", "Drugstore B", "Wellness Pharmacy C"]
    st.write("Nearby Pharmacies:")
    for pharmacy in pharmacies:
        st.write(f"- {pharmacy}")

# --- Mental Wellness Tips ---
def provide_mental_wellness_tips():
    tips = [
        "Practice deep breathing exercises to reduce stress.",
        "Engage in regular physical activity for mood enhancement.",
        "Maintain a consistent sleep schedule.",
        "Practice mindfulness and meditation.",
        "Connect with friends and family for social support."
    ]
    st.write("Mental Wellness Tips:")
    for tip in tips:
        st.write(f"- {tip}")

# --- Medication Reminders (Basic) ---
def medication_reminders():
    medication = st.text_input("Medication Name:")
    time = st.time_input("Reminder Time:")
    if st.button("Set Reminder"):
        st.success(f"Reminder set for {medication} at {time.strftime('%I:%M %p')}")

# --- Payment Gateway Simulation ---
def fake_payment_gateway(card_number, expiry_date, cvv, cost):
    if not (len(card_number) == 16 and card_number.isdigit()):
        return False, "Invalid card number"

    if not (len(expiry_date) == 5 and expiry_date[2] == '/' and expiry_date[:2].isdigit() and expiry_date[3:].isdigit()):
        return False, "Invalid expiry date format (MM/YY)"

    if not (len(cvv) == 3 and cvv.isdigit()):
        return False, "Invalid CVV"

    if int(card_number[:2]) % 2 == 0 and int(cvv) < 200:
        return False, "Payment declined due to security check"
    return True, "Payment successful"

# Function to display transaction details
def display_transaction_details(transaction_id):
    st.success(f"Appointment booked successfully! Transaction ID: {transaction_id}")

# --- Main Streamlit Application ---
def main():
    st.title("Health Risk Predictor & Doctor Booking System")
    init_db()

    # --- Sidebar ---
    menu = ["Login", "Register", "Predict", "Consult Doctor", "Upload Prescription", "Video Call", "Settings"]
    choice = st.sidebar.selectbox("Menu", menu)

    # --- Login/Register ---
    if choice == "Register":
        st.subheader("Create an Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(username, password):
                st.success("Registration successful! You can now log in.")
            else:
                st.error("Username already exists. Please choose a different username.")

    elif choice == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = authenticate_user(username, password)
            if user:
                st.session_state[SESSION_KEYS["logged_in"]] = True
                st.session_state[SESSION_KEYS["username"]] = username
                st.session_state[SESSION_KEYS["user"]] = user
                st.success("Login successful!")
            else:
                st.error("Invalid credentials.")

    # --- Main App Content (Conditional on Login) ---
    if SESSION_KEYS["logged_in"] in st.session_state and st.session_state[SESSION_KEYS["logged_in"]]:
        username = st.session_state[SESSION_KEYS["username"]]
        user = st.session_state[SESSION_KEYS["user"]]
        
        st.sidebar.header(f"Welcome, {username} (Balance: ${user.balance:.2f})")

        # Consultation and booking flow
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

            cost = calculate_booking_cost(hospital, doctor)
            st.write(f"Estimated cost of this appointment: ${cost:.2f}")

            st.session_state[SESSION_KEYS["booking_cost"]] = cost
            if st.button("Confirm Booking"):
                with st.form("payment_form"):
                    st.subheader("Payment Information")
                    card_number = st.text_input("Card Number", type="password")
                    expiry_date = st.text_input("Expiry Date (MM/YY)")
                    cvv = st.text_input("CVV", type="password")

                    submitted = st.form_submit_button("Pay Now")
                    if submitted:
                        success, message = fake_payment_gateway(card_number, expiry_date, cvv, cost)
                        if success:
                            if user.balance >= cost:
                                transaction_id, booking_success = book_appointment(username, hospital, doctor, date, time, cost)
                                if transaction_id and booking_success:
                                    conn = sqlite3.connect("health_app.db")
                                    c = conn.cursor()
                                    c.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (cost, username))
                                    conn.commit()
                                    conn.close()
                                    st.success("Payment successful and appointment booked!")
                                    display_transaction_details(transaction_id)
                                else:
                                    st.error("Error booking appointment. Please try again.")
                            else:
                                st.error("Insufficient balance. Please refill your account.")
                        else:
                            st.error(f"Payment failed: {message}")

        # Past bookings
        st.subheader("Past Bookings")
        past_bookings = get_user_bookings(username)
        if past_bookings:
            st.write("Your past bookings:")
            for booking in past_bookings:
                st.write(f"- Transaction ID: {booking[6]}, Hospital: {booking[0]}, Doctor: {booking[1]}, Date: {booking[2]}, Time: {booking[3]}, Status: {booking[4]}, Cost: ${booking[5]:.2f}")
        else:
            st.write("No past bookings found.")

        # Upload Prescription
        if choice == "Upload Prescription":
            st.subheader("Upload Prescription")
            uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
            if uploaded_file:
                extracted_text = extract_text_from_image(uploaded_file)
                st.subheader("Extracted Text")
                st.write(extracted_text)

        # Video Call
        if choice == "Video Call":
            st.subheader("Start Video Consultation")
            start_video_call()

        # Health Risk Prediction
        if choice == "Predict":
            st.subheader("Personalized Health Risk Predictor")
            st.sidebar.header("User  Information")
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

            st.header("More Wellness Tools")
            if st.button("Nearby Pharmacies"):
                user_location = "Placeholder User Location"  
                suggest_nearby_pharmacies(user_location)
            if st.button("Mental Wellness Tips"):
                provide_mental_wellness_tips()
            st.subheader("Medication Reminders")
            medication_reminders()

        if choice == "Settings":
            st.subheader("Settings not available")

# Launch App
if __name__ == "__main__":
    init_db()  # Initialize the database once
    main()
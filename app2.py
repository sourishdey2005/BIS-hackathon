import streamlit as st
import random
import hashlib
import sqlite3
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import datetime
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt

# --- API CONFIGURATION ---
SENDGRID_API_KEY = "YOUR_SENDGRID_API_KEY"  # Replace with your actual SendGrid API Key
GEMINI_API_KEY = "AIzaSyDZfMZN51fqIhxjtSkkAM6eMDBvYdcCuvk"  # Replace with your actual Gemini API key
genai.configure(api_key=GEMINI_API_KEY)

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT
        )
    """)
    conn.commit()
    conn.close()

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Register user
def register_user(username, password, email):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, hash_password(password), email))
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

# Function to send email (using SendGrid)
def send_email(subject, body, recipient_email):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        from_email = Email("your-email@example.com")  # Your email
        to_email = To(recipient_email)
        content = Content("text/plain", body)
        mail = Mail(from_email, to_email, subject, content)
        response = sg.send(mail)
        st.success(f"Email sent to {recipient_email} with subject: {subject}")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# List of hospitals and doctors with their specialties
hospitals = [
    "Apollo Hospitals", "Fortis Healthcare", "Max Healthcare", "AIIMS", "Manipal Hospitals", "Medanta",
    "Kokilaben Dhirubhai Ambani Hospital", "Narayana Health", "Care Hospitals", "Lilavati Hospital"
]

doctors = [
    ("Dr. Anil Kumar", "Cardiologist"), ("Dr. Neelam Singh", "Neurologist"), ("Dr. Rajeev Sinha", "Orthopedist"),
    ("Dr. Priya Verma", "General Physician"), ("Dr. Arvind Gupta", "Pediatrician"), ("Dr. Seema Bhat", "Dermatologist"),
    ("Dr. Vinay Sharma", "Gynecologist"), ("Dr. Mohit Verma", "Oncologist"), ("Dr. Shubham Yadav", "Dentist"),
    ("Dr. Pooja Mehta", "ENT Specialist"), ("Dr. Rakesh Kumar", "Pulmonologist"), ("Dr. Shalini Rathi", "Nephrologist"),
    ("Dr. Vivek Joshi", "Orthopedic Surgeon"), ("Dr. Aarti Rao", "Gastroenterologist"), ("Dr. Sunil Agarwal", "Endocrinologist"),
    ("Dr. Meera Sharma", "Psychiatrist"), ("Dr. Karan Singh", "Plastic Surgeon"), ("Dr. Ranjan Verma", "Urologist"),
    ("Dr. Neha Jain", "Obstetrician"), ("Dr. Amit Kumar", "Cardiologist"), ("Dr. Isha Patel", "Anesthesiologist"),
    ("Dr. Harish Yadav", "Hematologist"), ("Dr. Rajat Soni", "General Surgeon"), ("Dr. Kritika Chauhan", "Rheumatologist"),
    ("Dr. Nitin Bansal", "Chiropractor"), ("Dr. Sanjeev Kumar", "Infectious Disease Specialist"), ("Dr. Meenal Kapoor", "Pulmonologist"),
    ("Dr. Kunal Ghosh", "Neurosurgeon"), ("Dr. Pallavi Sharma", "Hepatologist"), ("Dr. Kiran Ahuja", "Radiologist"),
    ("Dr. Rahul Gupta", "Endocrinologist"), ("Dr. Aarti Dubey", "Gynaecologist"), ("Dr. Subhash Chander", "Cardiothoracic Surgeon"),
    ("Dr. Nidhi Tiwari", "Obstetrician"), ("Dr. Ashish Mehta", "Neurologist"), ("Dr. Vishal Kapoor", "Psychologist"),
    ("Dr. Richa Agarwal", "Ophthalmologist"), ("Dr. Vikram Soni", "Pediatric Surgeon"), ("Dr. Surbhi Gupta", "Pulmonary Specialist"),
    ("Dr. Deepak Rani", "ENT Specialist")
]

# Function to generate random visit dates for doctors
def get_random_dates():
    start_date = datetime.datetime.now() - datetime.timedelta(days=365)
    random_days = random.randint(0, 365)
    return start_date + datetime.timedelta(days=random_days)

# Generating sample data for consultations
appointments = []
for _ in range(20):  # Generate 20 sample appointments
    hospital = random.choice(hospitals)
    doctor = random.choice(doctors)
    visit_date = get_random_dates().strftime('%Y-%m-%d')
    appointments.append({
        'hospital': hospital,
        'doctor': doctor[0],  # Doctor's name
        'specialty': doctor[1],  # Doctor's specialty
        'visit_date': visit_date
    })

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
    st.title("Personalized Health Risk Predictor")
    
    init_db()
    menu = ["Login", "Register", "Consultation", "Update Profile", "Predict", "Health Trends"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Register":
        st.subheader("Create an Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        email = st.text_input("Email")
        if st.button("Register"):
            if register_user(username, password, email):
                send_email("Registration Successful", "Welcome! Your account has been created.", email)
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
        st.sidebar.header("User Information")
        if choice == "Consultation":
            st.subheader("Book a Consultation")
            hospital = st.selectbox("Select Hospital", hospitals)
            doctor = st.selectbox("Select Doctor", [d[0] for d in doctors])
            visit_date = st.date_input("Select Visit Date", datetime.datetime.today())
            if st.button("Book Consultation"):
                st.success(f"Consultation booked with Dr. {doctor} at {hospital} on {visit_date}")
        
        elif choice == "Update Profile":
            st.subheader("Update Your Profile")
            new_username = st.text_input("New Username", value=st.session_state["username"])
            new_email = st.text_input("New Email")
            new_password = st.text_input("New Password", type="password")
            if st.button("Update Profile"):
                if new_email:
                    send_email("Profile Updated", "Your profile has been updated successfully.", new_email)
                st.success("Profile updated successfully.")
        
        elif choice == "Predict":
            st.subheader("Predict Your Health Risk")
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
        
        st.sidebar.header("Consultation History")
        for appointment in appointments:
            st.write(f"Hospital: {appointment['hospital']}")
            st.write(f"Doctor: {appointment['doctor']} - {appointment['specialty']}")
            st.write(f"Visit Date: {appointment['visit_date']}")
            st.write("---------------")
        
        st.sidebar.header("Health Trends")
        if st.sidebar.button("View Health Trends"):
            display_health_trends()

if __name__ == "__main__":
    main()

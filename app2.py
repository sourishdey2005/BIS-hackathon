import streamlit as st
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai

# --- API CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyDOvM48IMxod_4SvEttajKXcVDblmKHyPk"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

# Function to send data to Gemini AI for health risk prediction
def get_health_risk_prediction(user_data):
    model = genai.GenerativeModel("gemini-pro")
    prompt = (
        "Given the following health data, predict the health risk score (1-100) and provide preventive tips: "
        f"Age: {user_data['age']}, Weight: {user_data['weight']} kg, Height: {user_data['height']} cm, "
        f"Smoking: {user_data['smoking']}, Alcohol: {user_data['alcohol']}, Exercise: {user_data['exercise']}, "
        f"Diet: {user_data['diet']}, Sleep Hours: {user_data['sleep_hours']}, Stress Level: {user_data['stress_level']}, "
        f"Medical History: {', '.join(user_data['medical_history'])}."
    )
    
    response = model.generate_content(prompt)
    
    if response and response.text:
        return {"risk_score": "Predicted risk score based on AI", "preventive_tips": response.text.split("\n")}
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
    
    st.sidebar.header("Additional Features")
    if st.sidebar.button("View Health Trends"):
        display_health_trends()
    
if __name__ == "__main__":
    main()
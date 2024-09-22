import streamlit as st
import json
import pandas as pd
import numpy as np
import streamlit.components.v1 as components

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stTextInput, .stCheckbox, .stRadio, .stSlider {
        margin-bottom: 20px;
    }
    .stButton button {
        background-color: #0078d4;
        color: white;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 5px;
        cursor: pointer;
    }
    .stButton button:hover {
        background-color: #005a9e;
    }
    .stDataFrame {
        margin-top: 20px;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Mock data for hospital and doctor information
hospital_doctor_info = [
    {"hospital_name": "General Hospital", "doctor_name": "Dr. Smith", "hospital_address": "123 Main St", "zip_code": "12345", "hospital_rating": 4.5, "doctor_rating": 4.7, "distance": 5, "latitude": 40.7128, "longitude": -74.0060},
    {"hospital_name": "City Clinic", "doctor_name": "Dr. Johnson", "hospital_address": "456 Elm St", "zip_code": "67890", "hospital_rating": 4.2, "doctor_rating": 4.5, "distance": 10, "latitude": 34.0522, "longitude": -118.2437},
    {"hospital_name": "Health Center", "doctor_name": "Dr. Lee", "hospital_address": "789 Oak St", "zip_code": "54321", "hospital_rating": 4.0, "doctor_rating": 4.3, "distance": 15, "latitude": 41.8781, "longitude": -87.6298}
]

# Mock data for procedure information
procedure_info = {
    "99213": "Office or other outpatient visit",
    "99214": "Office or other outpatient visit, established patient",
    "99215": "Office or other outpatient visit, new patient",
    "45378": "Colonoscopy",
    "00810": "Anesthesia for lower intestinal endoscopic procedures",
    "70450": "CT Head/Brain",
    "73721": "MRI Lower Extremity"
}

# Mock data for doctor-procedure mapping
doctor_procedure_mapping = {
    "Dr. Smith": ["99213", "70450"],
    "Dr. Johnson": ["99214", "73721"],
    "Dr. Lee": ["99215", "45378", "00810"]
}

# Mock data for complimentary services
complimentary_services = {
    "45378": {"00810": 10},  # Colonoscopy and Anesthesia
    "99215": {"70450": 7},   # Office visit and CT Head/Brain
    "73721": {"70450": 8}    # MRI Lower Extremity and CT Head/Brain
}

# Mock data for service prices
service_prices = {
    "General Hospital": {"99213": 200, "70450": 500, "99214": 220, "73721": 700, "99215": 250, "45378": 800, "00810": 300},
    "City Clinic": {"99213": 180, "70450": 480, "99214": 210, "73721": 680, "99215": 240, "45378": 780, "00810": 290},
    "Health Center": {"99213": 190, "70450": 490, "99214": 215, "73721": 690, "99215": 245, "45378": 790, "00810": 295}
}

# Function to get procedure name from CPT code
def get_procedure_name(cpt_code):
    return procedure_info.get(cpt_code, "Unknown Procedure")

# Streamlit app
st.sidebar.title("Health Services Comparison Tool")

# Step 1: Enter procedure name or CPT code
procedure_input = st.sidebar.text_input("Enter Procedure Name or CPT Code")
if procedure_input:
    procedure_name = get_procedure_name(procedure_input)
    st.sidebar.write(f"Selected Procedure: {procedure_name}")

# Step 2: Enter zip code or detect location
zip_code = st.sidebar.text_input("Enter Zip Code")
if zip_code:
    st.sidebar.write(f"Using Zip Code: {zip_code}")

# Step 3: Limit radius of healthcare service provider locations
radius = st.sidebar.slider("Limit Radius (miles)", 1, 50, 10)

# Step 4: Complimentary services add-on
complimentary_addon = st.sidebar.checkbox("Include Complimentary Services")
selected_complimentary_services = []
if complimentary_addon and procedure_input in complimentary_services:
    st.sidebar.write("Complimentary Services:")
    for comp_cpt, rank in complimentary_services[procedure_input].items():
        if rank > 6:
            if st.sidebar.checkbox(f"{get_procedure_name(comp_cpt)} (CPT Code: {comp_cpt}, Frequency: {rank}/10)", key=comp_cpt):
                selected_complimentary_services.append(comp_cpt)

# Step 5: Show ratings
show_hospital_rating = st.sidebar.checkbox("Show Hospital Rating (>4 stars)")
show_doctor_rating = st.sidebar.checkbox("Show Doctor Rating (>4 stars)")

# Step 6: Display results
display_option = st.sidebar.radio("Display Results As", ("Table", "Map"))

# Filter providers based on inputs
filtered_providers = [p for p in hospital_doctor_info if p["distance"] <= radius]
if show_hospital_rating:
    filtered_providers = [p for p in filtered_providers if p["hospital_rating"] > 4]
if show_doctor_rating:
    filtered_providers = [p for p in filtered_providers if p["doctor_rating"] > 4]

# Calculate total cost for each provider and create price breakdown
for provider in filtered_providers:
    main_service_cost = service_prices[provider["hospital_name"]].get(procedure_input, 0)
    complimentary_service_cost = sum(service_prices[provider["hospital_name"]].get(comp, 0) for comp in selected_complimentary_services)
    provider["total_cost"] = main_service_cost + complimentary_service_cost
    provider["price_breakdown"] = {
        "Main Service": main_service_cost,
        **{get_procedure_name(comp): service_prices[provider["hospital_name"]].get(comp, 0) for comp in selected_complimentary_services}
    }

# Sort providers by total cost, then by distance, then by rating
filtered_providers.sort(key=lambda x: (x["total_cost"], x["distance"], -x["hospital_rating"], -x["doctor_rating"]))

# Display results
if display_option == "Table":
    df = pd.DataFrame(filtered_providers)
    df["total_cost"] = df.apply(lambda row: f"${row['total_cost']}<br><details><summary>Price Breakdown</summary>{'<br>'.join([f'{k}: ${v}' for k, v in row['price_breakdown'].items()])}</details>", axis=1)
    df = df.drop(columns=["price_breakdown", "latitude", "longitude"])
    st.write(df.to_html(escape=False), unsafe_allow_html=True)
else:
    components.iframe("http://localhost:3000", height=500)

# Note: In a real application, you would replace the mock data with actual data from TiC and other sources.

import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/classify"

st.set_page_config(page_title="CAPM Investor Classifier", layout="centered")
st.title("📊 CAPM Investor Classification")
st.write("Fill the form below to classify your investor profile.")


with st.form("investor_form"):
    age = st.number_input("Age", min_value=18, max_value=80, value=28)
    monthly_income = st.number_input("Monthly Income (INR)", min_value=0, value=120000, step=1000)
    monthly_emi = st.number_input("Monthly EMI (INR)", min_value=0, value=15000, step=1000)

    st.markdown("### Emergency Fund")
    emergency_choice = st.radio("Provide emergency fund as:", ["Months", "Amount+Expense"])
    emergency_fund_months = None
    emergency_fund_amount = None
    monthly_expense = None
    if emergency_choice == "Months":
        emergency_fund_months = st.number_input("Emergency Fund (in months)", min_value=0.0, value=4.0)
    else:
        emergency_fund_amount = st.number_input("Emergency Fund Amount (INR)", min_value=0, value=300000, step=1000)
        monthly_expense = st.number_input("Monthly Expense (INR)", min_value=0, value=75000, step=1000)

    st.markdown("### Insurance")
    has_health = st.checkbox("Has Health Insurance", value=True)
    has_life = st.checkbox("Has Life/Term Insurance", value=False)

    dependants = st.number_input("Number of Dependants", min_value=0, max_value=20, value=1)

    risk_attitude = st.slider("Risk Attitude (1=averse, 5=seeking)", min_value=1, max_value=5, value=3)
    investment_knowledge = st.slider("Investment Knowledge (1=novice, 5=expert)", min_value=1, max_value=5, value=3)
    drawdown_reaction = st.selectbox(
        "If portfolio drops 10% in a year, you would:",
        ["wait", "sell", "buy_more"]
    )

    submitted = st.form_submit_button("Classify Me 🚀")

if submitted:
    payload = {
        "age": age,
        "monthly_income": monthly_income,
        "monthly_emi": monthly_emi,
        "insurance": {"has_health": has_health, "has_life": has_life},
        "dependants": dependants,
        "risk_attitude": risk_attitude,
        "investment_knowledge": investment_knowledge,
        "drawdown_reaction": drawdown_reaction,
    }
    if emergency_choice == "Months":
        payload["emergency_fund_months"] = emergency_fund_months
    else:
        payload["emergency_fund_amount"] = emergency_fund_amount
        payload["monthly_expense"] = monthly_expense

    try:
        res = requests.post(BACKEND_URL, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            st.success(f"**Profile:** {data['profile']} | **Score:** {data['score']}")

            st.subheader("Factor Breakdown")
            for f in data["factors"]:
                st.write(f"- {f['name']}: {f['subscore']} (weight {f['weight']}, weighted {f['weighted']})")

            st.subheader("Suggested Allocation")
            if "suggestions" in data:
                alloc = data["suggestions"].get("asset_allocation", {})
                notes = data["suggestions"].get("notes", [])
                st.write("Asset Allocation %:")
                st.bar_chart(alloc)
                st.write("Notes:")
                for note in notes:
                    st.write(f"- {note}")
        else:
            st.error(f"Backend error {res.status_code}: {res.text}")
    except Exception as e:
        st.error(f"Could not reach backend: {e}")

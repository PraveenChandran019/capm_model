import streamlit as st
from typing import Optional, Dict, List, Literal
from pydantic import BaseModel

# -------------------------------
# Backend logic (from your FastAPI code)
# -------------------------------
class Insurance(BaseModel):
    has_health: Optional[bool] = False
    has_life: Optional[bool] = False

class InvestorInput(BaseModel):
    age: Optional[int] = 30
    monthly_income: Optional[int] = 0
    monthly_emi: Optional[int] = 0
    emergency_fund_months: Optional[float] = None
    emergency_fund_amount: Optional[int] = None
    monthly_expenses: Optional[int] = None
    insurance: Optional[Insurance] = None
    insurance_amount: Optional[int] = None
    dependants: Optional[int] = None
    risk_attitude: Optional[int] = None
    investment_knowledge: Optional[int] = None
    drawdown_reaction: Optional[Literal["sell", "wait", "buy_more"]] = None
    risk_tolerance: Optional[Literal["conservative", "moderate", "aggressive"]] = None
    time_horizon: Optional[int] = None
    return_expectation: Optional[float] = None

WEIGHTS = {
    "age": 0.25,
    "financial_stability": 0.30,
    "risk_tolerance": 0.20,
    "time_horizon": 0.15,
    "return_expectation": 0.10,
}

# --- Helper functions (same as your FastAPI code) ---
def get_age_score(age: int) -> float:
    if age <= 25: return 90.0
    if age <= 35: return 75.0
    if age <= 45: return 60.0
    if age <= 55: return 40.0
    if age <= 65: return 20.0
    return 10.0

def get_income_score_from_threshold(income: int) -> float:
    if income < 20000: return 30.0
    if income < 50000: return 40.0
    if income < 100000: return 50.0
    if income < 500000: return 60.0
    if income < 1000000: return 70.0
    if income < 1500000: return 80.0
    if income < 2400000: return 85.0
    if income < 5000000: return 90.0
    if income < 7500000: return 95.0
    if income < 10000000: return 97.0
    return 100.0

def get_emergency_score_from_ratio(ratio: float) -> float:
    if ratio > 1.4: return 90.0
    if ratio > 1: return 70.0
    if ratio > 0.75: return 60.0
    if ratio > 0.5: return 50.0
    return 30.0

def get_debt_score_from_ratio(emi_ratio: float) -> float:
    if emi_ratio < 5: return 90.0
    if emi_ratio < 15: return 75.0
    if emi_ratio < 25: return 60.0
    if emi_ratio < 50: return 45.0
    return 30.0

def get_risk_tolerance_score(risk_tolerance: str) -> float:
    mapping = {"conservative": 30.0, "moderate": 60.0, "aggressive": 90.0}
    return mapping.get(risk_tolerance, 60.0)

def get_time_horizon_score(time_horizon: int) -> float:
    if time_horizon <= 3: return 35.0
    if time_horizon <= 7: return 65.0
    return 90.0

def get_return_expectation_score(return_expectation: float) -> float:
    if return_expectation < 8: return 35.0
    if return_expectation < 12: return 60.0
    if return_expectation < 15: return 75.0
    return 90.0

def get_insurance_score(insurance_amount: Optional[int]) -> Optional[float]:
    if insurance_amount is None: return None
    if insurance_amount == 0: return 30.0
    if insurance_amount < 500000: return 40.0
    if insurance_amount < 2500000: return 60.0
    if insurance_amount < 10000000: return 75.0
    if insurance_amount < 50000000: return 90.0
    return 100.0

def get_dependants_score(dependants: Optional[int]) -> Optional[float]:
    if dependants is None: return None
    if dependants == 0: return 90.0
    if dependants <= 2: return 75.0
    if dependants <= 5: return 60.0
    if dependants <= 8: return 45.0
    return 30.0

# --- Classification ---
def classify_investor(data: InvestorInput) -> Dict:
    factors: List[Dict] = []
    score = 0.0

    # Age
    age_sub = get_age_score(data.age or 30)
    factors.append({"name": "age", "subscore": age_sub})
    score += age_sub * WEIGHTS["age"]

    # Financial Stability
    monthly_income = data.monthly_income or 1
    monthly_emi = data.monthly_emi or 0
    monthly_expenses = data.monthly_expenses or 0
    emi_ratio = (monthly_emi / monthly_income * 100) if monthly_income else 100.0
    debt_score = get_debt_score_from_ratio(emi_ratio)
    income_score = get_income_score_from_threshold(monthly_income)
    emergency_ratio = data.emergency_fund_months / 6 if data.emergency_fund_months else 0.0
    emergency_score = get_emergency_score_from_ratio(emergency_ratio)
    financial_sub = (income_score + emergency_score + debt_score) / 3
    factors.append({"name": "financial_stability", "subscore": round(financial_sub, 2)})
    score += financial_sub * WEIGHTS["financial_stability"]

    # Risk Tolerance
    likert = {1: 30.0, 2: 45.0, 3: 60.0, 4: 75.0, 5: 90.0}
    dd_map = {"sell": 30.0, "wait": 60.0, "buy_more": 90.0}
    risk_subs: List[float] = []
    if data.risk_tolerance:
        risk_tolerance_sub = get_risk_tolerance_score(data.risk_tolerance)
    else:
        if data.risk_attitude: risk_subs.append(likert.get(data.risk_attitude, 60.0))
        if data.investment_knowledge: risk_subs.append(likert.get(data.investment_knowledge, 60.0))
        if data.drawdown_reaction: risk_subs.append(dd_map.get(data.drawdown_reaction, 60.0))
        risk_tolerance_sub = sum(risk_subs)/len(risk_subs) if risk_subs else 60.0
    factors.append({"name": "risk_tolerance", "subscore": round(risk_tolerance_sub,2)})
    score += risk_tolerance_sub * WEIGHTS["risk_tolerance"]

    # Time Horizon
    time_sub = get_time_horizon_score(data.time_horizon or 5)
    factors.append({"name": "time_horizon", "subscore": time_sub})
    score += time_sub * WEIGHTS["time_horizon"]

    # Return Expectation
    return_sub = get_return_expectation_score(data.return_expectation or 10.0)
    factors.append({"name": "return_expectation", "subscore": return_sub})
    score += return_sub * WEIGHTS["return_expectation"]

    # Normalize & Profile
    score = round(min(100, max(0, score)), 2)
    if score <= 25: profile = "Ultra-Conservative"
    elif score <= 40: profile = "Conservative"
    elif score <= 60: profile = "Moderate"
    elif score <= 75: profile = "Moderate-Aggressive"
    elif score <= 90: profile = "Aggressive"
    else: profile = "Ultra-Aggressive"

    recommendation = "invest in equity > debt > gold" if score >= 70 else "invest in debt > equity > gold" if score >= 40 else "invest in debt > gold > equity"

    return {"score": score, "profile": profile, "recommendation": recommendation, "factors": factors}

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("CAPM Investor Classifier")

age = st.number_input("Age", 18, 100, 30)
monthly_income = st.number_input("Monthly Income", 0, 10000000, 50000)
monthly_emi = st.number_input("Monthly EMI", 0, 1000000, 5000)
monthly_expenses = st.number_input("Monthly Expenses", 0, 1000000, 20000)
risk_attitude = st.selectbox("Risk Attitude (1-5)", [1,2,3,4,5], index=2)
investment_knowledge = st.selectbox("Investment Knowledge (1-5)", [1,2,3,4,5], index=2)
drawdown_reaction = st.selectbox("Drawdown Reaction", ["sell", "wait", "buy_more"], index=1)
emergency_fund_months = st.number_input("Emergency Fund (Months)", 0.0, 24.0, 6.0)
time_horizon = st.number_input("Investment Time Horizon (Years)", 1, 50, 5)
return_expectation = st.number_input("Expected Return (%)", 0.0, 50.0, 10.0)

if st.button("Classify Investor"):
    data = InvestorInput(
        age=age,
        monthly_income=monthly_income,
        monthly_emi=monthly_emi,
        monthly_expenses=monthly_expenses,
        risk_attitude=risk_attitude,
        investment_knowledge=investment_knowledge,
        drawdown_reaction=drawdown_reaction,
        emergency_fund_months=emergency_fund_months,
        time_horizon=time_horizon,
        return_expectation=return_expectation
    )
    result = classify_investor(data)
    st.subheader("Investor Classification Result")
    st.json(result)

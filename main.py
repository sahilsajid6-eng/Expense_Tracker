from datetime import datetime
import streamlit as st
from Loginandprofile import User, AuthManager, login_signup_page, check_onboarding
from demographicandrecord import Expense, ExpenseDatabaseManager, charts_page, demographics_page

# Initialize backend database managers
db_mgr = ExpenseDatabaseManager(db_name="expenses_v2.db")
auth_mgr = AuthManager(db_name="expenses_v2.db")

# Streamlit Page Setup
st.set_page_config(page_title="FinTrack Pro - Expense Intelligence", page_icon="💳", layout="wide")

# Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 5px;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #F1F5F9;
        margin-bottom: 12px;
        border-left: 4px solid #3B82F6;
        padding-left: 10px;
    }
</style>
""", unsafe_allow_html=True)


def main_dashboard():
    """Renders executive summary dashboard."""
    user: User = st.session_state["user"]
    check_onboarding(db_mgr, user)

    demo = db_mgr.fetch_demographics(user.id)
    expenses = db_mgr.fetch_user_expenses(user.id)
    curr = demo.currency_symbol

    st.title("💸 Executive Dashboard")
    st.caption("Track, record, and manage personal expenses effortlessly.")

    # High-level Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    total_spent = sum(e.amount for e in expenses)
    avg_expense = (total_spent / len(expenses)) if expenses else 0.0

    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Total Expenditure</div><div class="metric-value">{curr}{total_spent:,.2f}</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Total Transactions</div><div class="metric-value">{len(expenses)}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Average Transaction</div><div class="metric-value">{curr}{avg_expense:,.2f}</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Country / Currency</div><div class="metric-value">{demo.country} ({curr})</div></div>', unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown('<div class="section-title">Log New Expense</div>', unsafe_allow_html=True)
        with st.form(key="expense_form", clear_on_submit=True):
            amount = st.number_input(f"Amount ({curr})", min_value=0.01, step=0.01)
            category = st.selectbox("Category", ["Food", "Travel", "Study", "Entertainment", "Bills", "Shopping"])
            expense_date = st.date_input("Date", datetime.now())
            if st.form_submit_button("Record Expense", type="primary", use_container_width=True):
                db_mgr.add_expense(Expense(amount=amount, category=category, date=expense_date, user_id=user.id))
                st.toast("Expense added successfully!", icon="✅")
                st.rerun()

    with col2:
        st.markdown('<div class="section-title">Recent Transactions</div>', unsafe_allow_html=True)
        if expenses:
            for exp in expenses[:5]:
                c1, c2, c3, c4 = st.columns([2, 2, 2, 0.8])
                c1.text(f"📅 {exp.date}")
                c2.text(f"🏷️ {exp.category}")
                c3.markdown(f"**{curr}{exp.amount:,.2f}**")
                if c4.button("🗑️", key=f"del_{exp.id}"):
                    db_mgr.delete_expense(exp.id, user.id)
                    st.rerun()
        else:
            st.info("No expense entries logged yet.")


# Navigation Router
if "user" not in st.session_state:
    page_login = st.Page(lambda: login_signup_page(auth_mgr), title="Portal", icon="🔐")
    pg = st.navigation([page_login])
else:
    user: User = st.session_state["user"]
    st.sidebar.markdown(f"### 👤 Active Account:\n**{user.username}**")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        del st.session_state["user"]
        st.rerun()

    st.sidebar.divider()

    page_main = st.Page(main_dashboard, title="Executive Dashboard", icon="💸", default=True)
    page_charts = st.Page(lambda: charts_page(db_mgr), title="Financial Analytics", icon="📊")
    page_demographics = st.Page(lambda: demographics_page(db_mgr), title="Demographics & Reports", icon="👤")
    
    pg = st.navigation({
        "Application Menu": [page_main, page_charts, page_demographics]
    })

pg.run()
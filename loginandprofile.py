import hashlib
import sqlite3
import streamlit as st


class User:
    """Represents an authenticated user account."""
    def __init__(self, username: str, user_id: int = None):
        self.id = user_id
        self.username = username


class UserDemographics:
    """Represents demographic metadata and preferred currency linked to a user."""
    def __init__(self, country: str, currency_symbol: str, age_group: str, occupation: str, user_id: int):
        self.user_id = user_id
        self.country = country
        self.currency_symbol = currency_symbol
        self.age_group = age_group
        self.occupation = occupation


class AuthManager:
    """Handles authentication and user database interactions."""
    def __init__(self, db_name="expenses_v2.db"):
        self.db_name = db_name

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username: str, password: str) -> bool:
        try:
            hashed_pw = self._hash_password(password)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username.strip(), hashed_pw)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username: str, password: str):
        hashed_pw = self._hash_password(password)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username FROM users WHERE username = ? AND password = ?",
                (username.strip(), hashed_pw)
            )
            row = cursor.fetchone()
            if row:
                return User(user_id=row[0], username=row[1])
            return None


def login_signup_page(auth_mgr: AuthManager):
    """Renders login and signup interface."""
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>💳 Login Portal</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tab1:
            login_user = st.text_input("Username", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            if st.button("Sign In", use_container_width=True, type="primary"):
                user = auth_mgr.authenticate_user(login_user, login_pass)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Invalid credentials provided.")

        with tab2:
            new_user = st.text_input("Choose Username", key="signup_user")
            new_pass = st.text_input("Choose Password", type="password", key="signup_pass")
            if st.button("Create Account", use_container_width=True):
                if new_user and new_pass:
                    if auth_mgr.create_user(new_user, new_pass):
                        st.success("Account created successfully! Please sign in.")
                    else:
                        st.error("Username already registered.")
                else:
                    st.warning("Please fill out all fields.")


def check_onboarding(db_mgr, user: User):
    """Enforces onboarding form on first-time user login."""
    demo = db_mgr.fetch_demographics(user.id)
    if not demo:
        st.warning("⚠️ **Profile Setup Required**: Please enter your profile details below to customize your app currency and setup.")
        with st.form("onboarding_form"):
            st.subheader("👤 First-Time User Profile Setup")
            
            c1, c2 = st.columns(2)
            country = c1.text_input("Country Name", placeholder="e.g., United States, Pakistan, UK")
            currency_symbol = c2.text_input("Currency Symbol", value="$", placeholder="e.g., $, €, £, ₹, ₨")
            
            c3, c4 = st.columns(2)
            age_group = c3.selectbox("Age Group", ["<18", "18-24", "25-34", "35-49", "50+"], index=1)
            occupation = c4.selectbox("Occupation", ["Student", "Employed", "Self-Employed", "Freelancer", "Other"])

            if st.form_submit_button("Complete Setup", type="primary", use_container_width=True):
                if country and currency_symbol:
                    db_mgr.save_demographics(UserDemographics(
                        country=country.strip(),
                        currency_symbol=currency_symbol.strip(),
                        age_group=age_group,
                        occupation=occupation,
                        user_id=user.id
                    ))
                    st.success("Profile saved! Redirecting to dashboard...")
                    st.rerun()
                else:
                    st.error("Please provide both Country and Currency Symbol.")
        st.stop()
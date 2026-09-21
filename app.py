import streamlit as st

from modules.student_home import show_student_home
from modules.recruiter_home import show_recruiter_home
from modules.recruitment_intelligence import show_recruitment_intelligence

from modules.role_intelligence import show_role_intelligence
from modules.admin_home import show_admin_home
from dotenv import load_dotenv

load_dotenv()


st.set_page_config(
    page_title="Recruitment Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="
        font-size:25px;
        font-weight:700;
    ">
        🎯 Recruitment<br>
        Intelligence
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    """
    <div style="
        font-size:14px;
        line-height:1.6;
        color:#b8bdc9;
    ">
        AI-Powered Recruitment Analytics &<br>
        Job Recommendation Platform
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.divider()

if st.query_params.get("page") == "student":
    default_navigation = "🎓 Student Home"
else:
    default_navigation = "🏠 Home"


page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🎓 Student Home",
        "⚙️ Admin Home"
    ],
    index=[
        "🏠 Home",
        "🎓 Student Home",
        "⚙️ Admin Home"
    ].index(default_navigation),
    key="main_navigation"
)

if page != "🎓 Student Home" and "page" in st.query_params:
    st.query_params.clear()

# ============================================================
# HOME
# ============================================================

# ============================================================
# HOME
# ============================================================

if page == "🏠 Home":

    st.markdown(
        """
        <div style="
            font-size:38px;
            font-weight:700;
            margin-bottom:4px;
        ">
            🎯 Recruitment Intelligence
        </div>

        <div style="
            font-size:18px;
            color:#8b93a7;
            margin-bottom:25px;
        ">
            AI-Powered Recruitment Analytics & Job Recommendation Platform
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.subheader("Welcome")

    st.write(
        "Explore job opportunities, personalized recommendations, "
        "applications and recruitment insights."
    )

    # ========================================================
    # QUICK ACTIONS
    # ========================================================

    st.markdown(
        '<div class="section-title">⚡ Quick Actions</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Choose an action to get started."
    )

    action_col1, action_col2, action_col3 = st.columns(3)

    # --------------------------------------------------------
    # ACTION HANDLER
    # --------------------------------------------------------

    def open_student_page(target_page): 

        # Move main navigation to Student Home
        st.session_state["main_navigation"] = "🎓 Student Home"

        if st.session_state.get("student_logged_in", False):

            # Student is already logged in
            st.session_state["student_page"] = target_page

        else:

            # Student is not logged in.
            # Remember the page they wanted to open after login.
            st.session_state["quick_action_page_after_login"] = target_page

            # Open Student Home authentication screen
            st.session_state["auth_mode"] = "Sign In"
            st.session_state["student_page"] = "Dashboard"
    # --------------------------------------------------------
    # ROW 1
    # --------------------------------------------------------

    st.button(
        "🔎 Find Jobs",
        width="stretch",
        key="quick_find_jobs",
        on_click=open_student_page,
        args=("Dashboard",)
    )

    st.button(
        "🤖 Recommended Jobs",
        width="stretch",
        key="quick_recommended_jobs",
        on_click=open_student_page,
        args=("Recommended Jobs",)
    )

    st.button(
        "⭐ Saved Jobs",
        width="stretch",
        key="quick_saved_jobs",
        on_click=open_student_page,
        args=("Saved Jobs",)
    )

    st.button(
        "📋 My Applications",
        width="stretch",
        key="quick_my_applications",
        on_click=open_student_page,
        args=("My Applications",)
    )

    st.button(
        "👤 My Profile",
        width="stretch",
        key="quick_my_profile",
        on_click=open_student_page,
        args=("My Profile",)
    )

    st.button(
        "🧠 Role Intelligence",
        width="stretch",
        key="quick_role_intelligence",
        on_click=open_student_page,
        args=("Role Intelligence",)
    )

    # ========================================================
    # PLATFORM OVERVIEW
    # ========================================================

    st.markdown(
        '<div class="section-title">📊 Platform Overview</div>',
        unsafe_allow_html=True
    )

    overview_col1, overview_col2, overview_col3 = st.columns(3)

    with overview_col1:
        st.metric(
            "Current Jobs",
            "—"
        )

    with overview_col2:
        st.metric(
            "Companies",
            "—"
        )

    with overview_col3:
        st.metric(
            "Roles",
            "—"
        )

    st.info(
        "💡 Login as a student to access personalized job "
        "recommendations, saved jobs, applications and your profile."
    )


# ============================================================
# RECRUITMENT INTELLIGENCE
# ============================================================

elif page == "🔎 Recruitment Intelligence":

    show_recruitment_intelligence()






# ============================================================
# STUDENT HOME
# ============================================================

elif page == "🎓 Student Home":

    show_student_home()





# ============================================================
# ADMIN HOME
# ============================================================

elif page == "⚙️ Admin Home":

    show_admin_home()
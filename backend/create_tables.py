

# Import all models so SQLAlchemy knows about them
from backend.database import Base, engine
from backend.models.student import Student
from backend.models.student_profile import StudentProfile
from backend.models.company import Company
from backend.models.job import Job
from backend.models.historical_recruitment import HistoricalRecruitment
from backend.models.job_market_history import JobMarketHistory
from backend.models.saved_job import SavedJob
from backend.models.application import Application
from backend.models.notification import Notification
from backend.models.live_job import LiveJob
from backend.models.otp_verification import OTPVerification
from backend.models.admin import Admin
from backend.models.company_contact import CompanyContact
print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("All database tables created successfully.")
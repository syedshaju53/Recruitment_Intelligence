import requests
import streamlit as st

import os
from dotenv import load_dotenv

load_dotenv()

try:
    BASE_URL = st.secrets["API_BASE_URL"]
except Exception:
    BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")



class APIClient:

    def __init__(self):
        self.base_url = BASE_URL
        self.token = st.session_state.get("access_token")

    # --------------------------------------------------
    # AUTH
    # --------------------------------------------------

    def set_token(self, token):
        self.token = token
        st.session_state["access_token"] = token

    def clear_token(self):
        self.token = None
        st.session_state.pop("access_token", None)

    def _headers(self):

        headers = {
            "Content-Type": "application/json"
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    # --------------------------------------------------
    # LOGIN
    # --------------------------------------------------

    def login(self, username, password):
        response = requests.post(
            f"{self.base_url}/students/login",
            params={
                "username": username,
                "password": password
            },
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()

            token = data.get("access_token")

            if token:
                self.set_token(token)

        return response

    # --------------------------------------------------
    # STUDENT PROFILE
    # --------------------------------------------------

    def get_student_profile(self):

        return requests.get(
            f"{self.base_url}/students/profile/me",
            headers=self._headers(),
            timeout=10,
        )
        
        # --------------------------------------------------
    # MY PROFILE
    # --------------------------------------------------

    def get_my_profile(self):

        return requests.get(
            f"{self.base_url}/students/profile/me",
            headers=self._headers(),
            timeout=10,
        )
        
    def update_my_profile(self, payload):

            return requests.put(
                f"{self.base_url}/students/profile/me",
                headers=self._headers(),
                json=payload,
                timeout=10,
            )

    # --------------------------------------------------
    # LIVE JOBS
    # --------------------------------------------------

    def get_live_job(self, live_job_id):
        return requests.get(
            f"{self.base_url}/live-jobs/live-jobs/{live_job_id}",
            headers=self._headers(),
            timeout=10,
        )
    # --------------------------------------------------
    # SAVE JOB
    # --------------------------------------------------

    def save_job(self, live_job_id):
        return requests.post(
            f"{self.base_url}/saved-jobs/saved-jobs",
            headers=self._headers(),
            json={
                "live_job_id": int(live_job_id)
            },
            timeout=10,
        )
    # --------------------------------------------------
    # SAVED JOBS
    # --------------------------------------------------

    def get_saved_jobs(self):
        return requests.get(
            f"{self.base_url}/saved-jobs/saved-jobs",
            headers=self._headers(),
            timeout=10,
        )
    
    def delete_saved_job(self, live_job_id):
        return requests.delete(
                f"{self.base_url}/saved-jobs/saved-jobs/live/{int(live_job_id)}",
                headers=self._headers(),
                timeout=10,
            )
    # --------------------------------------------------
    # APPLY
    # --------------------------------------------------

    # --------------------------------------------------
    # RESUME UPLOAD
    # --------------------------------------------------

    def upload_resume(self, file_name, file_data, mime_type=None):
        files = {
            "file": (
                file_name,
                file_data,
                mime_type or "application/octet-stream"
            )
        }

        headers = {}

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return requests.post(
            f"{self.base_url}/resumes/upload",
            headers=headers,
            files=files,
            timeout=30,
        )

    # --------------------------------------------------
    # APPLY
    # --------------------------------------------------

    def apply_for_job(
        self,
        job_id=None,
        live_job_id=None,
        cover_letter=None,
        resume_filename=None,
        resume_id=None,
    ):

        payload = {
            "job_id": job_id,
            "live_job_id": live_job_id,
            "cover_letter": cover_letter,
            "resume_filename": resume_filename,
            "resume_id": resume_id,
        }

        return requests.post(
            f"{self.base_url}/applications/applications",
            headers=self._headers(),
            json=payload,
            timeout=10,
        )

    # --------------------------------------------------
    # APPLICATIONS
    # --------------------------------------------------

    def get_my_applications(self):
       return requests.get(
        f"{self.base_url}/applications/applications",
        headers=self._headers(),
        timeout=10,
    )

    # --------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------

    def get_notifications(self):

        return requests.get(
            f"{self.base_url}/notifications/notifications",
            headers=self._headers(),
            timeout=10,
        )
        
       
from api.client import APIClient


client = APIClient()

response = client.login(
    "savedjobtest01",
    "Test@12345"
)

print("Status:", response.status_code)
print("Response:", response.json())

if response.status_code == 200:

    data = response.json()

    client.set_token(data["access_token"])

    profile_response = client.get_my_profile()

    print("Profile Status:", profile_response.status_code)
    print("Profile:", profile_response.json())

    jobs_response = client.get_jobs()

    print("Jobs Status:", jobs_response.status_code)
    print("Jobs:", jobs_response.json())
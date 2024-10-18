import requests
import json
from fastapi import FastAPI, HTTPException
from twilio.rest import Client
from time import time
import traceback

app = FastAPI()

WHEREBY_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmFwcGVhci5pbiIsImF1ZCI6Imh0dHBzOi8vYXBpLmFwcGVhci5pbi92MSIsImV4cCI6OTAwNzE5OTI1NDc0MDk5MSwiaWF0IjoxNzI5MjU3MzgyLCJvcmdhbml6YXRpb25JZCI6Mjc5ODM0LCJqdGkiOiI4OGQ3OTgzMS1lODBiLTRhZmYtODNmZC0xZmNhNzUyNmNhMWEifQ.0Dvs0aOEF4FOeeKX-UPE2p1lsJjWtvmh3pXXJTm3AYc"

# Twilio configuration
TWILIO_ACCOUNT_SID = 'AC8a0514493862a7c1b2357b4156b05ecb'
TWILIO_AUTH_TOKEN = '6d5022469449fdeeeca39f7adda3117e'
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def create_meeting_url():
    data = {
        "endDate": "2099-02-18T14:23:00.000Z",
        "fields": ["hostRoomUrl"],
    }

    headers = {
        "Authorization": f"Bearer {WHEREBY_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.whereby.dev/v1/meetings",
        headers=headers,
        json=data
    )

    print("Status code:", response.status_code)
    data = json.loads(response.text)
    print("Room URL:", data["roomUrl"])
    print("Host room URL:", data["hostRoomUrl"])
    return data["roomUrl"]

@app.post("/meet/start")
async def start_meet():
    try:
        # Create a new Zoom meeting via Zoom API
        whereby_meeting_link = create_meeting_url()

        return {"message": "Conference created and link.", "whereby_link": whereby_meeting_link}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050, reload=True)

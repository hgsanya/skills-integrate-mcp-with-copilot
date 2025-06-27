"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
import json
import jwt
import datetime
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Security
security = HTTPBearer(auto_error=False)
SECRET_KEY = "mergington-high-school-secret-key"  # In production, use environment variable

# Request models
class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    email: str

# Load teacher credentials
def load_teachers():
    try:
        with open(os.path.join(Path(__file__).parent, "teachers.json"), "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"teachers": {}}

def verify_teacher_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify teacher authentication token"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("username")
        teachers_data = load_teachers()
        if username in teachers_data["teachers"]:
            return username
    except jwt.InvalidTokenError:
        pass
    
    return None

def require_teacher_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Require teacher authentication"""
    teacher = verify_teacher_token(credentials)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Teacher authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return teacher

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

@app.post("/auth/login")
def login(request: LoginRequest):
    """Teacher login endpoint"""
    teachers_data = load_teachers()
    
    if (request.username in teachers_data["teachers"] and 
        teachers_data["teachers"][request.username]["password"] == request.password):
        
        # Create JWT token
        token_data = {
            "username": request.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "teacher_name": teachers_data["teachers"][request.username]["name"]
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

@app.get("/auth/verify")
def verify_auth(teacher: str = Depends(verify_teacher_token)):
    """Verify if current token is valid"""
    if teacher:
        teachers_data = load_teachers()
        return {
            "authenticated": True,
            "teacher_name": teachers_data["teachers"][teacher]["name"]
        }
    return {"authenticated": False}

@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, request: SignupRequest, teacher: str = Depends(require_teacher_auth)):
    """Sign up a student for an activity (teacher only)"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if request.email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(request.email)
    return {"message": f"Signed up {request.email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, teacher: str = Depends(require_teacher_auth)):
    """Unregister a student from an activity (teacher only)"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


# Load teacher credentials
def load_teachers():
    try:
        with open(os.path.join(Path(__file__).parent, "teachers.json"), "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"teachers": {}}

def verify_teacher_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify teacher authentication token"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("username")
        teachers_data = load_teachers()
        if username in teachers_data["teachers"]:
            return username
    except jwt.InvalidTokenError:
        pass
    
    return None

def require_teacher_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Require teacher authentication"""
    teacher = verify_teacher_token(credentials)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Teacher authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return teacher

@app.post("/auth/login")
def login(request: LoginRequest):
    """Teacher login endpoint"""
    teachers_data = load_teachers()
    
    if (request.username in teachers_data["teachers"] and 
        teachers_data["teachers"][request.username]["password"] == request.password):
        
        # Create JWT token
        token_data = {
            "username": request.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "teacher_name": teachers_data["teachers"][request.username]["name"]
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )


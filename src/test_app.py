from turtle import up

import pytest
from fastapi.testclient import TestClient
from app import app, root

client = TestClient(app)

def test_successful_signup():
    """Test that a student can sign up for an activity successfully."""
    response = client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
    assert response.status_code == 200
    assert "Signed up newstudent@mergington.edu for Chess Club" in response.json()["message"]
    
    # Verify the student was added
    activities_response = client.get("/activities")
    assert "newstudent@mergington.edu" in activities_response.json()["Chess Club"]["participants"]

def test_duplicate_signup_prevented():
    """Test that a student cannot sign up twice for the same activity (bug fix)."""
    # First signup
    response1 = client.post("/activities/Programming Class/signup?email=test@mergington.edu")
    assert response1.status_code == 200
    
    # Second signup with same email should fail
    response2 = client.post("/activities/Programming Class/signup?email=test@mergington.edu")
    assert response2.status_code == 400
    assert "Student already signed up for this activity" in response2.json()["detail"]
    
    # Verify only one instance in participants
    activities_response = client.get("/activities")
    participants = activities_response.json()["Programming Class"]["participants"]
    assert participants.count("test@mergington.edu") == 1

def test_signup_nonexistent_activity():
    """Test signing up for a non-existent activity returns 404."""
    response = client.post("/activities/Nonexistent Activity/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

def test_get_activities():
    """Test that GET /activities returns all activities with correct structure."""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "description" in data["Chess Club"]
    assert "participants" in data["Chess Club"]
    assert isinstance(data["Chess Club"]["participants"], list)

def test_signup_activity_full():
    """Test that signing up for a full activity is prevented (assuming max_participants check is added)."""
    # Assuming we add a check in signup: if len(activity["participants"]) >= activity["max_participants"]: raise HTTPException(400, "Activity is full")
    # For this test, use an activity that's already at max or sign up until full.
    # Example: Basketball Team has max 15, currently 1 participant.
    # But to test, we'd need to fill it up, which is tedious. Alternatively, mock or use a small max activity.
    # For simplicity, assume Programming Class has max 20, and we can test by filling it.
    # But since it's in-memory, perhaps add a test activity with small max.
    # For now, this is a placeholder; implement the check in app.py first.
    pass  # Replace with actual test once max check is added

#def test_root_redirect():
#    """Test that root path redirects to static index."""
    
#    response = client.get("/")
#    assert response.status_code == 307  # Redirect
#    assert response.headers["location"] == "/static/index.html"

def test_signup_multiple_activities():
    """Test that a student can sign up for multiple different activities."""
    email = "multi@mergington.edu"
    # Signup for two different activities
    resp1 = client.post("/activities/Gym Class/signup?email=" + email)
    assert resp1.status_code == 200
    resp2 = client.post("/activities/Tennis Club/signup?email=" + email)
    assert resp2.status_code == 200
    
    # Verify in both
    activities = client.get("/activities").json()
    assert email in activities["Gym Class"]["participants"]
    assert email in activities["Tennis Club"]["participants"]

def test_signup_invalid_email():
    """Test signup with invalid email (though currently no validation, this is for future enhancement)."""
    # Currently, the app accepts any string as email; add regex validation if needed.
    # For now, this passes as is.
    response = client.post("/activities/Chess Club/signup?email=invalid")
    assert response.status_code == 200  # Would be 400 if validation added

def test_unregister_participant():
    """Test that a participant can be unregistered from an activity."""
    email = "unregister_test@mergington.edu"
    
    # First, sign up the participant
    signup_response = client.post(f"/activities/Drama Club/signup?email={email}")
    assert signup_response.status_code == 200
    
    # Verify they were added
    activities_before = client.get("/activities").json()
    assert email in activities_before["Drama Club"]["participants"]
    
    # Now unregister them
    unregister_response = client.delete(f"/activities/Drama Club/signup?email={email}")
    assert unregister_response.status_code == 200
    assert "Unregistered" in unregister_response.json()["message"]
    
    # Verify they were removed
    activities_after = client.get("/activities").json()
    assert email not in activities_after["Drama Club"]["participants"]

def test_unregister_nonexistent_participant():
    """Test that unregistering a participant not signed up returns 400."""
    response = client.delete("/activities/Science Club/signup?email=notexist@mergington.edu")
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]

def test_unregister_from_nonexistent_activity():
    """Test that unregistering from a non-existent activity returns 404."""
    response = client.delete("/activities/Fake Activity/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

def test_unregister_updates_participant_count():
    """Test that participant count decreases after unregistering."""
    email = "count_test@mergington.edu"
    activity_name = "Art Studio"
    
    # Get initial count
    initial_activities = client.get("/activities").json()
    initial_count = len(initial_activities[activity_name]["participants"])
    
    # Sign up
    client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Verify count increased
    after_signup = client.get("/activities").json()
    assert len(after_signup[activity_name]["participants"]) == initial_count + 1
    
    # Unregister
    client.delete(f"/activities/{activity_name}/signup?email={email}")
    
    # Verify count returned to original
    after_unregister = client.get("/activities").json()
    assert len(after_unregister[activity_name]["participants"]) == initial_count
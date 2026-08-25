import requests
import time

API_URL = "http://127.0.0.1:8000"

def test_autonomous_research_loop():
    print("=== Testing DREAMNET Phase 6 Autonomous Research Loop ===")
    
    # 1. Create a Research Question
    question_payload = {
        "text": "Can quantization parameter INT8 scaling reduce model latency by >=20% without dropping accuracy by >1.5%?"
    }
    print(f"Registering Question: '{question_payload['text']}'")
    res = requests.post(f"{API_URL}/questions", json=question_payload)
    assert res.status_code == 201, f"Failed to create question: {res.text}"
    question = res.json()
    question_id = question["id"]
    print(f"Created Question ID: {question_id}")
    
    # 2. Get hypotheses generated automatically
    res = requests.get(f"{API_URL}/questions/{question_id}/hypotheses")
    assert res.status_code == 200
    hypotheses = res.json()
    print(f"Initial generated hypotheses count: {len(hypotheses)}")
    for idx, h in enumerate(hypotheses):
        print(f"  H{idx+1}: {h['statement']} (Status: {h['status']})")
    
    # 3. Create Research Session
    session_payload = {
        "question_id": question_id,
        "budget": 5
    }
    print("Creating Research Session...")
    res = requests.post(f"{API_URL}/research", json=session_payload)
    assert res.status_code == 201
    session = res.json()
    session_id = session["id"]
    print(f"Created Session ID: {session_id} (Status: {session['status']}, Iteration: {session['iteration']})")
    
    # 4. Start the loop
    print("Starting Research Session loop...")
    res = requests.post(f"{API_URL}/research/{session_id}/start")
    assert res.status_code == 200
    session = res.json()
    print(f"Session Status: {session['status']}")
    
    # Wait for loop to design and check policies
    time.sleep(1)
    
    # Fetch status again
    res = requests.get(f"{API_URL}/research/{session_id}")
    session = res.json()
    print(f"Polled Session Status (expected PAUSED for human approval): {session['status']}")
    
    # 5. Fetch experiment designed for the hypothesis
    h_id = hypotheses[0]["id"]
    res = requests.get(f"{API_URL}/hypotheses/{h_id}/experiment")
    assert res.status_code == 200
    experiment = res.json()
    print(f"Designed Experiment ID: {experiment['id']} (Approved: {experiment.get('approved')})")
    
    # 6. Approve the experiment to trigger sandbox run and evaluations
    print(f"Approving experiment {experiment['id']} (Human-in-the-Loop)...")
    res = requests.post(f"{API_URL}/experiments/{experiment['id']}/approve")
    assert res.status_code == 200
    approved_exp = res.json()
    print(f"Experiment Status: {approved_exp['status']} (Approved: {approved_exp.get('approved')})")
    
    # Give the background runner some time to complete sandbox execution and evaluation
    print("Waiting for sandbox execution and evaluation...")
    time.sleep(3)
    
    # 7. Check experiment results and evaluation outcome
    res = requests.get(f"{API_URL}/experiments/{experiment['id']}/results")
    assert res.status_code == 200
    result = res.json()
    print(f"Sandbox metrics extracted: {result['metrics']}")
    
    res = requests.get(f"{API_URL}/experiments/{experiment['id']}/evaluation")
    assert res.status_code == 200
    evaluation = res.json()
    print(f"Deterministic Verdict: {evaluation['verdict']} (Confidence: {evaluation['confidence']})")
    print(f"LLM Observations: {evaluation['observations']}")
    
    # 8. Check if loop is completed or next iteration hypothesis is added
    res = requests.get(f"{API_URL}/questions/{question_id}/hypotheses")
    new_hypotheses = res.json()
    print(f"Current hypotheses count (checks for refined follow-ups if rejected): {len(new_hypotheses)}")
    for idx, h in enumerate(new_hypotheses):
        print(f"  H{idx+1}: {h['statement']} (Status: {h['status']})")
        
    print("=== Phase 6 Autonomous Loop Integration Test Passed! ===")

if __name__ == "__main__":
    test_autonomous_research_loop()

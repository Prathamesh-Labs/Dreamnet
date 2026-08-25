import requests
import time

API_URL = "http://127.0.0.1:8000"

def test_rejected_followup():
    print("=== Testing DREAMNET Phase 6 Rejection Follow-up Hypothesis Generation ===")
    
    # 1. Create a Research Question that will fail criteria
    question_payload = {
        # This will fail because criteria is speedup >= 10.0x, but INT8 mock only gives 2.48x
        "text": "Can quantization scaling achieve speedup >= 10.0x and accuracy loss <= 0.1%?"
    }
    res = requests.post(f"{API_URL}/questions", json=question_payload)
    assert res.status_code == 201
    question = res.json()
    question_id = question["id"]
    
    # 2. Get hypotheses
    res = requests.get(f"{API_URL}/questions/{question_id}/hypotheses")
    hypotheses = res.json()
    h_id = hypotheses[0]["id"]
    
    # 3. Create Research Session
    session_payload = {
        "question_id": question_id,
        "budget": 5
    }
    res = requests.post(f"{API_URL}/research", json=session_payload)
    session = res.json()
    session_id = session["id"]
    
    # Delete alternate hypotheses from database to make H1 the only hypothesis
    import psycopg2
    conn = psycopg2.connect(host="localhost", port=5432, user="postgres", password="Brother@2008", database="dreamnet")
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hypotheses WHERE question_id = %s AND id != %s", (question_id, h_id))
    cursor.close()
    conn.close()

    # 4. Start session loop
    requests.post(f"{API_URL}/research/{session_id}/start")
    time.sleep(1)
    
    # Get designed experiment and approve it
    res = requests.get(f"{API_URL}/hypotheses/{h_id}/experiment")
    experiment = res.json()
    
    # Force the success criteria to be extremely strict so it rejects INT8 performance
    # Modify experiment success criteria to force a rejection
    conn = psycopg2.connect(host="localhost", port=5432, user="postgres", password="Brother@2008", database="dreamnet")
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("UPDATE experiments SET measurable_success_criteria = 'Inference speedup >= 10.0x' WHERE id = %s", (experiment['id'],))
    cursor.close()
    conn.close()

    
    # Re-fetch designed criteria to print
    res = requests.get(f"{API_URL}/hypotheses/{h_id}/experiment")
    experiment = res.json()
    print(f"Force-modified criteria: {experiment['measurable_success_criteria']}")

    
    print("Approving experiment...")
    requests.post(f"{API_URL}/experiments/{experiment['id']}/approve")
    
    print("Waiting for sandbox execution & evaluation...")
    time.sleep(3)
    
    # Check evaluation
    res = requests.get(f"{API_URL}/experiments/{experiment['id']}/evaluation")
    evaluation = res.json()
    print(f"Verdict: {evaluation['verdict']}")
    assert evaluation["verdict"] == "REJECTED", f"Expected REJECTED but got {evaluation['verdict']}"
    
    # 5. Resume or start loop again to let it check the rejection and generate H4!
    print("Resuming loop to trigger refinement generation...")
    res = requests.post(f"{API_URL}/research/{session_id}/resume")
    assert res.status_code == 200
    
    time.sleep(2.5) # Give it time to call MockProvider.generate_followup_hypothesis
    
    # 6. Fetch hypotheses list again to verify H4 exists!
    res = requests.get(f"{API_URL}/questions/{question_id}/hypotheses")
    new_hypotheses = res.json()
    print(f"Total hypotheses now: {len(new_hypotheses)}")
    for idx, h in enumerate(new_hypotheses):
        print(f"  H{idx+1}: {h['statement']} (Status: {h['status']})")
        
    assert len(new_hypotheses) > 1, "Expected a follow-up hypothesis to be generated!"
    print("=== Rejection Follow-up Hypothesis Generation Test Passed! ===")

if __name__ == "__main__":
    test_rejected_followup()

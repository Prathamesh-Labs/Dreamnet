import requests
import time

API_URL = "http://127.0.0.1:8000"

def test_full_e2e_discovery_and_spawn():
    print("=== Testing DREAMNET E2E Research Loop + Discovery Engine ===")

    # 1. Create a Question
    question_payload = {
        "text": "Optimize inference execution cost on custom datasets."
    }
    print(f"Registering Question: '{question_payload['text']}'")
    res = requests.post(f"{API_URL}/questions", json=question_payload)
    assert res.status_code == 201
    question = res.json()
    question_id = question["id"]

    # 2. Start Research Session
    session_payload = {
        "question_id": question_id,
        "budget": 3
    }
    res = requests.post(f"{API_URL}/research", json=session_payload)
    assert res.status_code == 201
    session = res.json()
    session_id = session["id"]

    # 3. Start loop execution
    res = requests.post(f"{API_URL}/research/{session_id}/start")
    assert res.status_code == 200
    time.sleep(1)

    # 4. Approve designed experiment (Human-in-the-Loop)
    res = requests.get(f"{API_URL}/questions/{question_id}/hypotheses")
    hypotheses = res.json()
    h_id = hypotheses[0]["id"]

    print("Waiting for experiment to be designed by loop engine...")
    experiment = None
    for _ in range(10):
        res = requests.get(f"{API_URL}/hypotheses/{h_id}/experiment")
        if res.status_code == 200:
            data = res.json()
            if data and "id" in data:
                experiment = data
                break
        time.sleep(1)
    
    assert experiment is not None, "Experiment was not designed in time."
    
    # Force modify criteria to guarantee unexpected magnitude discovery
    # e.g. latency_reduction_pct >= 5.0% (our mock script yields 28.5%, which is >20% delta above 5%)
    import psycopg2
    conn = psycopg2.connect(host="localhost", port=5432, user="postgres", password="Brother@2008", database="dreamnet")
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE experiments SET measurable_success_criteria = 'latency reduction >= 5.0%%' WHERE id = %s",
        (experiment['id'],)
    )
    cursor.close()
    conn.close()

    print("Approving experiment plan to initiate sandbox runner execution...")
    res = requests.post(f"{API_URL}/experiments/{experiment['id']}/approve")
    assert res.status_code == 200

    print("Waiting for runner execution, metrics evaluation, and discovery analysis...")
    time.sleep(4.5)

    # 5. Fetch generated discoveries for this session
    res = requests.get(f"{API_URL}/research/{session_id}/discoveries")
    assert res.status_code == 200
    discoveries = res.json()
    print(f"Detected discoveries count: {len(discoveries)}")
    assert len(discoveries) >= 1, "Expected at least one discovery candidate to be detected!"
    
    disc = discoveries[0]
    print(f"Discovery Candidate Found: '{disc['title']}'")
    print(f"  Confidence: {disc['confidence']} | Novelty: {disc['novelty_score']}")
    print(f"  LLM Explanation: {disc['observation']}")

    # 6. Validate Discovery (Confirm it)
    print(f"Confirming discovery candidate {disc['id']}...")
    res = requests.post(f"{API_URL}/discoveries/{disc['id']}/validate", json={"status": "CONFIRMED"})
    assert res.status_code == 200
    validated_disc = res.json()
    assert validated_disc["status"] == "CONFIRMED"

    # 7. Spawn new child research question from the validated discovery
    spawn_payload = {
        "question_text": f"Why does dynamic spatial scaling show unexpected latency magnitude of {disc['evidence'].get('observed', 0):.1f}%?"
    }
    print(f"Spawning child research question lead: '{spawn_payload['question_text']}'")
    res = requests.post(f"{API_URL}/discoveries/{disc['id']}/spawn_lead", json=spawn_payload)
    assert res.status_code == 201
    child_question = res.json()
    print(f"Successfully spawned child question ID: {child_question['id']}")

    # 8. Check that the child question has an idle research session generated automatically
    res = requests.get(f"{API_URL}/questions")
    questions = res.json()
    assert any(q["id"] == child_question["id"] for q in questions)
    
    print("=== Phase 7 & 8 E2E Research Loop + Discovery Integration Test Passed! ===")

if __name__ == "__main__":
    test_full_e2e_discovery_and_spawn()

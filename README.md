# DREAMNET: Autonomous Scientific Research & Hypothesis Loop

DREAMNET is an advanced, self-directed research engine designed to autonomously formulate, test, evaluate, and branch scientific inquiries. Centered around a closed-loop execution cycle, the system runs isolated sandboxed experiments, extracts quantitative metrics, evaluates evidence, and scans for emergent discoveries—spawned directly as new child threads in a research lineage network.

Integrated into the system is an **On-Board Computer (OBC) Flight Telemetry Simulator** that models spacecraft anomalies (such as solar flare exposures and thruster valve thermal drift), prompting the autonomous loop to execute real-time mitigation inquiry and launch corrective commands.

---

## 🔍 System Architecture & Workflow

DREAMNET operates as a multi-stage pipelines network:

```mermaid
graph TD
    A[Research Question Formulated] --> B[Generate Competing Hypotheses]
    B --> C[Design Experiment Specification]
    C --> D[Human-in-the-Loop Approval]
    D --> E[Isolated Sandbox Subprocess Execution]
    E --> F[Extract Quantitative Metrics & Logs]
    F --> G[Evidence Evaluation & Verdict Engine]
    G --> H{Emergent Discoveries Scanned?}
    H -- Yes (Validate & Confirm) --> I[Spawn Child Research Question]
    I --> A
    H -- No --> J[Iteration Complete]
```

### The Autonomous Loop Stages
1. **Question Formulation (`/questions`):** Initial target or telemetry-driven repair goals.
2. **Competing Hypotheses (`/hypotheses`):** Generates multiple competing statements with rationales and assumptions.
3. **Experiment Spec Design (`/experiments`):** Formulates objectives, independent/dependent variables, and verification assertions.
4. **Isolated Sandbox Execution:** Runs Python trial scripts within restricted subprocesses to guarantee host safety.
5. **Evidence Evaluation:** Compares sandbox metrics against success criteria to rule supported/rejected verdicts.
6. **Emergent Discovery Engine:** Scans logs for anomalous patterns, spawning child research questions to continue the investigation lineage.

---

## 🛠️ Repository Layout

```
DREAMNET/
├── backend/                  # FastAPI & SQLAlchemy Engine
│   ├── app/
│   │   ├── api/              # Route handlers (questions, telemetry, discoveries)
│   │   ├── core/             # Configuration & LLM settings
│   │   ├── database/         # PostgreSQL connection & migrations
│   │   ├── engines/          # Hypothesis & discovery heuristic controllers
│   │   ├── models/           # DB tables (Project, Hypothesis, Experiment, Discovery)
│   │   └── services/         # Sandbox runners & LLM API adapters (Gemini)
│   ├── requirements.txt      # Python dependencies
│   └── docker-compose.yml    # Anchored PostgreSQL database with pgvector
├── frontend/                 # Vite & React Workspace
│   ├── src/
│   │   ├── App.tsx           # Dashboard UI and controls
│   │   ├── App.css           # Custom CSS styling (Neon theme)
│   │   └── main.tsx          # React application entry point
│   └── package.json
└── README.md                 # Project Documentation
```

---

## 🚀 Getting Started

### 1. Database Setup
DREAMNET utilizes a **PostgreSQL** database with `pgvector` support.
If using Docker, run:
```bash
docker-compose up -d
```
Otherwise, ensure local PostgreSQL is running on port `5432` with a database named `dreamnet`. Configure your connection details in `backend/.env`.

### 2. Backend API Setup
Navigate to the `backend` directory and configure the environment:
1. Create or verify `backend/.env`:
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dreamnet
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
2. Activate your virtual environment and install dependencies:
   ```bash
   cd backend
   .venv\Scripts\activate       # Windows PowerShell/Command Prompt
   pip install -r requirements.txt
   ```
3. Start the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --port 8000
   ```
   The backend API will run on **`http://localhost:8000`**.

### 3. Frontend Dashboard Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   npm install
   ```
2. Launch the Vite development server:
   ```bash
   npm run dev
   ```
   Open **`http://localhost:5173/`** in your browser to interact with the Control Room.

---

## 🛠️ Flight Telemetry Simulator (OBC Integration)

The dashboard includes a real-time monitor simulating spacecraft subsystems:
* **Solar Flare Trigger:** Artificially induces valve temperature anomalies on thrusters.
* **Autonomous Mitigation:** The anomaly automatically registers a priority research question targeting duty-cycle calibration.
* **Loop Resolution:** Runs sandboxed optimizations and dispatches a cooling telecommand once a supported solution is verified.

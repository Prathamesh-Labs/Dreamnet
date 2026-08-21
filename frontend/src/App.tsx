import { useState, useEffect } from 'react'
import './App.css'

interface Question {
  id: string
  text: string
  project_id: string | null
  status: string
  created_at: string
}

function App() {
  const [questionText, setQuestionText] = useState('')
  const [questionsList, setQuestionsList] = useState<Question[]>([])
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline'>('offline')
  const [dbStatus, setDbStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking')
  const [dbError, setDbError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const API_URL = 'http://127.0.0.1:8000'

  // Fetch health status & check database
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`)
      if (res.ok) {
        const data = await res.json()
        setBackendStatus('online')
        if (data.database === 'connected') {
          setDbStatus('connected')
          setDbError(null)
        } else {
          setDbStatus('disconnected')
          setDbError(data.database_error || 'Database connection error.')
        }
      } else {
        setBackendStatus('offline')
        setDbStatus('disconnected')
      }
    } catch (err) {
      setBackendStatus('offline')
      setDbStatus('disconnected')
      setDbError('Could not contact the FastAPI backend server.')
    }
  }

  // Fetch previous questions
  const fetchQuestions = async () => {
    try {
      const res = await fetch(`${API_URL}/questions`)
      if (res.ok) {
        const data = await res.json()
        setQuestionsList(data)
      }
    } catch (err) {
      console.error('Error fetching questions:', err)
    }
  }

  useEffect(() => {
    checkHealth()
    fetchQuestions()
    const interval = setInterval(checkHealth, 5000) // Poll every 5s
    return () => clearInterval(interval)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!questionText.trim()) return

    setIsSubmitting(true)
    setMessage(null)

    try {
      const res = await fetch(`${API_URL}/questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: questionText,
        }),
      })

      if (res.ok) {
        const newQuestion = await res.json()
        setQuestionsList((prev) => [newQuestion, ...prev])
        setQuestionText('')
        setMessage('Research question submitted and registered successfully!')
      } else {
        const errData = await res.json()
        setMessage(`Error: ${errData.detail || 'Failed to register question.'}`)
      }
    } catch (err) {
      setMessage('Error: Failed to contact the backend server.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="dreamnet-container">
      {/* Header */}
      <header className="dreamnet-header">
        <div className="logo-section">
          <div className="logo-icon">🧠</div>
          <div className="logo-title">
            <h1>DREAMNET</h1>
            <p>Autonomous Scientific Research & Hypothesis Loop</p>
          </div>
        </div>
        <div className="system-status">
          <div className="status-item">
            <span className="status-label">Backend API:</span>
            <span className={`status-badge ${backendStatus}`}>
              <span className="status-dot"></span>
              {backendStatus.toUpperCase()}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">Database:</span>
            <span className={`status-badge ${dbStatus}`}>
              <span className="status-dot"></span>
              {dbStatus.toUpperCase()}
            </span>
          </div>
        </div>
      </header>

      {/* Main Panel */}
      <main className="dreamnet-workspace">
        <section className="control-panel">
          <div className="panel-header">
            <h2>Research Question Engine</h2>
            <p className="panel-desc">Formulate a scientific question to initiate hypothesis loop skeleton.</p>
          </div>

          <form onSubmit={handleSubmit} className="question-form">
            <div className="form-group">
              <label htmlFor="research-question">Enter Research Question or Problem statement</label>
              <textarea
                id="research-question"
                rows={5}
                placeholder="e.g., How can we reduce ML inference cost without significant accuracy loss?"
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                disabled={dbStatus !== 'connected'}
              />
            </div>

            <button
              type="submit"
              className="submit-btn"
              disabled={isSubmitting || !questionText.trim() || dbStatus !== 'connected'}
            >
              {isSubmitting ? 'Registering...' : 'Register Research Question'}
            </button>
          </form>

          {message && (
            <div className={`notification ${message.startsWith('Error') ? 'error' : 'success'}`}>
              {message}
            </div>
          )}

          {dbStatus !== 'connected' && (
            <div className="setup-alert">
              <h3>⚠️ Database Connection Required</h3>
              <p>PostgreSQL is running, but auth failed. To connect Postgres, configure the password in your backend env file:</p>
              <code>backend/.env</code>
              <pre className="env-guide">
                DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/dreamnet
              </pre>
              {dbError && (
                <div className="db-error-log">
                  <strong>Error details:</strong>
                  <p>{dbError}</p>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Saved Questions List */}
        <section className="data-explorer">
          <div className="panel-header">
            <h2>Registered Questions ({questionsList.length})</h2>
            <p className="panel-desc">Questions currently saved in the `research_questions` table.</p>
          </div>

          <div className="questions-feed">
            {questionsList.length === 0 ? (
              <div className="empty-state">
                <p>No questions registered yet. Submit a research question to see it saved in Postgres.</p>
              </div>
            ) : (
              questionsList.map((q) => (
                <div className="question-card" key={q.id}>
                  <div className="card-header">
                    <span className="question-id">ID: {q.id.substring(0, 8)}...</span>
                    <span className={`status-pill ${q.status}`}>{q.status}</span>
                  </div>
                  <p className="question-text">{q.text}</p>
                  <div className="card-footer">
                    <span className="timestamp">Created: {new Date(q.created_at).toLocaleString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App

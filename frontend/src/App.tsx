import { useState, useEffect } from 'react'
import './App.css'

interface Variables {
  independent: string[]
  dependent: string[]
  control: string[]
}

interface Experiment {
  id: string
  hypothesis_id: string
  objective: string
  baseline: string
  treatment: string
  variables: Variables
  dataset: string
  metrics: string[]
  procedure: string[]
  expected_outcome: string
  measurable_success_criteria: string
  status: string
  created_at: string
  updated_at: string
}

interface Hypothesis {
  id: string
  question_id: string
  statement: string
  rationale: string
  assumptions: string[]
  variables: string[]
  predicted_outcome: string
  confidence: number
  testability: string
  status: string
  created_at: string
}

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

  // Hypotheses details state
  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(null)
  const [hypothesesMap, setHypothesesMap] = useState<Record<string, Hypothesis[]>>({})
  const [loadingHypotheses, setLoadingHypotheses] = useState<Record<string, boolean>>({})
  const [regeneratingMap, setRegeneratingMap] = useState<Record<string, boolean>>({})

  // Experiment details state
  const [experimentsMap, setExperimentsMap] = useState<Record<string, Experiment>>({})
  const [loadingExperiments, setLoadingExperiments] = useState<Record<string, boolean>>({})
  const [designingMap, setDesigningMap] = useState<Record<string, boolean>>({})

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
        setMessage('Research question submitted and hypotheses generated successfully!')
        
        // Auto expand and fetch hypotheses for the newly created question
        setExpandedQuestionId(newQuestion.id)
        fetchHypotheses(newQuestion.id)
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

  const fetchExperiment = async (hypothesisId: string) => {
    setLoadingExperiments(prev => ({ ...prev, [hypothesisId]: true }))
    try {
      const res = await fetch(`${API_URL}/hypotheses/${hypothesisId}/experiment`)
      if (res.ok) {
        const data = await res.json()
        setExperimentsMap(prev => ({ ...prev, [hypothesisId]: data }))
      } else {
        // Clear from map if it doesn't exist (e.g. was deleted or new hypothesis)
        setExperimentsMap(prev => {
          const updated = { ...prev }
          delete updated[hypothesisId]
          return updated
        })
      }
    } catch (err) {
      console.error('Error fetching experiment:', err)
    } finally {
      setLoadingExperiments(prev => ({ ...prev, [hypothesisId]: false }))
    }
  }

  const fetchHypotheses = async (questionId: string) => {
    setLoadingHypotheses(prev => ({ ...prev, [questionId]: true }))
    try {
      const res = await fetch(`${API_URL}/questions/${questionId}/hypotheses`)
      if (res.ok) {
        const data = await res.json()
        setHypothesesMap(prev => ({ ...prev, [questionId]: data }))
        
        // Fetch experiment for each hypothesis automatically
        data.forEach((h: Hypothesis) => {
          fetchExperiment(h.id)
        })
      }
    } catch (err) {
      console.error('Error fetching hypotheses:', err)
    } finally {
      setLoadingHypotheses(prev => ({ ...prev, [questionId]: false }))
    }
  }

  const handleToggleExpand = (questionId: string) => {
    if (expandedQuestionId === questionId) {
      setExpandedQuestionId(null)
      return
    }
    setExpandedQuestionId(questionId)
    if (!hypothesesMap[questionId]) {
      fetchHypotheses(questionId)
    }
  }

  const handleRegenerateHypotheses = async (e: React.MouseEvent, questionId: string) => {
    e.stopPropagation() // Prevent collapsing the card
    setRegeneratingMap(prev => ({ ...prev, [questionId]: true }))
    try {
      const res = await fetch(`${API_URL}/questions/${questionId}/hypotheses/generate`, {
        method: 'POST'
      })
      if (res.ok) {
        const data = await res.json()
        setHypothesesMap(prev => ({ ...prev, [questionId]: data }))
        
        // Clear experiments map and fetch for new hypotheses
        data.forEach((h: Hypothesis) => {
          fetchExperiment(h.id)
        })
      }
    } catch (err) {
      console.error('Error regenerating hypotheses:', err)
    } finally {
      setRegeneratingMap(prev => ({ ...prev, [questionId]: false }))
    }
  }

  const handleDesignExperiment = async (hypothesisId: string) => {
    setDesigningMap(prev => ({ ...prev, [hypothesisId]: true }))
    try {
      const res = await fetch(`${API_URL}/hypotheses/${hypothesisId}/experiment`, {
        method: 'POST'
      })
      if (res.ok) {
        const data = await res.json()
        setExperimentsMap(prev => ({ ...prev, [hypothesisId]: data }))
      }
    } catch (err) {
      console.error('Error designing experiment:', err)
    } finally {
      setDesigningMap(prev => ({ ...prev, [hypothesisId]: false }))
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
            <p className="panel-desc">Click any card to explore generated competing hypotheses.</p>
          </div>

          <div className="questions-feed">
            {questionsList.length === 0 ? (
              <div className="empty-state">
                <p>No questions registered yet. Submit a research question to see it saved in Postgres.</p>
              </div>
            ) : (
              questionsList.map((q) => (
                <div 
                  className={`question-card clickable ${expandedQuestionId === q.id ? 'expanded' : ''}`} 
                  key={q.id}
                  onClick={() => handleToggleExpand(q.id)}
                >
                  <div className="card-header">
                    <span className="question-id">ID: {q.id.substring(0, 8)}...</span>
                    <span className={`status-pill ${q.status}`}>{q.status}</span>
                  </div>
                  <p className="question-text">{q.text}</p>
                  <div className="card-footer">
                    <span className="timestamp">Created: {new Date(q.created_at).toLocaleString()}</span>
                    <span className="expand-hint">
                      {expandedQuestionId === q.id ? '▲ Hide Hypotheses' : '▼ Show Hypotheses'}
                    </span>
                  </div>

                  {/* Expanded Hypotheses Section */}
                  {expandedQuestionId === q.id && (
                    <div className="hypotheses-section" onClick={(e) => e.stopPropagation()}>
                      <div className="hypotheses-title-row">
                        <h3>🧬 Competing Hypotheses</h3>
                        <button
                          className="regenerate-btn"
                          onClick={(e) => handleRegenerateHypotheses(e, q.id)}
                          disabled={regeneratingMap[q.id]}
                        >
                          {regeneratingMap[q.id] ? 'Regenerating...' : '🔄 Regenerate'}
                        </button>
                      </div>

                      {loadingHypotheses[q.id] ? (
                        <div className="shimmer-wrapper">
                          {[1, 2, 3].map((i) => (
                            <div className="shimmer-card" key={i}>
                              <div className="shimmer-line title"></div>
                              <div className="shimmer-line body-1"></div>
                              <div className="shimmer-line body-2"></div>
                              <div className="shimmer-line meta"></div>
                            </div>
                          ))}
                        </div>
                      ) : !hypothesesMap[q.id] || hypothesesMap[q.id].length === 0 ? (
                        <div className="empty-state">
                          <p>No hypotheses generated for this question. Click regenerate to create them.</p>
                        </div>
                      ) : (
                        <div className="hypotheses-grid">
                          {hypothesesMap[q.id].map((h, idx) => (
                            <div className="hypothesis-card" key={h.id}>
                              <div className="hypothesis-title-section">
                                <p className="hypothesis-statement">
                                  <strong>H{idx + 1}:</strong> {h.statement}
                                </p>
                              </div>
                              <p className="hypothesis-rationale">
                                <strong>Rationale:</strong> {h.rationale}
                              </p>
                              <p className="hypothesis-rationale">
                                <strong>Predicted Outcome:</strong> {h.predicted_outcome}
                              </p>

                              <hr className="hypothesis-divider" />

                              <div className="hypothesis-details-grid">
                                <div className="details-block">
                                  <span className="details-label">Boundary Assumptions</span>
                                  <ul className="details-list">
                                    {h.assumptions && h.assumptions.length > 0 ? (
                                      h.assumptions.map((item, key) => (
                                        <li className="details-tag" key={key}>{item}</li>
                                      ))
                                    ) : (
                                      <span className="details-tag">None</span>
                                    )}
                                  </ul>
                                </div>
                                <div className="details-block">
                                  <span className="details-label">Key Variables</span>
                                  <ul className="details-list">
                                    {h.variables && h.variables.length > 0 ? (
                                      h.variables.map((item, key) => (
                                        <li className="details-tag" key={key}>{item}</li>
                                      ))
                                    ) : (
                                      <span className="details-tag">None</span>
                                    )}
                                  </ul>
                                </div>
                              </div>

                              <hr className="hypothesis-divider" />

                              <div className="hypothesis-meta-row">
                                <div className="confidence-section">
                                  <span className="confidence-label">Confidence:</span>
                                  <div className="confidence-bar-container">
                                    <div 
                                      className="confidence-bar-fill" 
                                      style={{ width: `${h.confidence * 100}%` }}
                                    ></div>
                                  </div>
                                  <span className="confidence-value">{(h.confidence * 100).toFixed(0)}%</span>
                                </div>

                                <span className={`badge-testability ${h.testability}`}>
                                  {h.testability}
                                </span>

                                <span className="badge-status">
                                  {h.status}
                                </span>
                              </div>

                              {/* Experiment Specification Section */}
                              <div className="experiment-section">
                                <div className="experiment-header-row">
                                  <div className="experiment-title">
                                    <span>🧪 Experiment Specification</span>
                                  </div>
                                  {experimentsMap[h.id] && (
                                    <button 
                                      className="redesign-exp-btn"
                                      onClick={() => handleDesignExperiment(h.id)}
                                      disabled={designingMap[h.id]}
                                    >
                                      {designingMap[h.id] ? 'Designing...' : '🔄 Redesign'}
                                    </button>
                                  )}
                                </div>

                                {loadingExperiments[h.id] || designingMap[h.id] ? (
                                  <div className="shimmer-card" style={{ padding: '1rem', gap: '0.5rem' }}>
                                    <div className="shimmer-line title" style={{ width: '40%' }}></div>
                                    <div className="shimmer-line body-1"></div>
                                    <div className="shimmer-line body-2" style={{ width: '80%' }}></div>
                                  </div>
                                ) : !experimentsMap[h.id] ? (
                                  <div className="no-exp-state">
                                    <p>No experiment specification designed for this hypothesis yet.</p>
                                    <button 
                                      className="design-exp-btn"
                                      onClick={() => handleDesignExperiment(h.id)}
                                    >
                                      Design Experiment Spec
                                    </button>
                                  </div>
                                ) : (
                                  <div className="experiment-container">
                                    <div className="experiment-header-row" style={{ margin: 0 }}>
                                      <div className="experiment-block">
                                        <span className="experiment-block-label">Status</span>
                                        <span className={`experiment-status-pill ${experimentsMap[h.id].status}`}>
                                          {experimentsMap[h.id].status}
                                        </span>
                                      </div>
                                      <div className="experiment-block" style={{ alignItems: 'flex-end' }}>
                                        <span className="experiment-block-label">Dataset</span>
                                        <p className="experiment-block-text" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                                          {experimentsMap[h.id].dataset}
                                        </p>
                                      </div>
                                    </div>

                                    <div className="experiment-block">
                                      <span className="experiment-block-label">Objective</span>
                                      <p className="experiment-block-text">{experimentsMap[h.id].objective}</p>
                                    </div>

                                    <div className="experiment-comparison-grid">
                                      <div className="comparison-card baseline">
                                        <span className="experiment-block-label">Baseline Configuration</span>
                                        <p className="experiment-block-text">{experimentsMap[h.id].baseline}</p>
                                      </div>
                                      <div className="comparison-card treatment">
                                        <span className="experiment-block-label">Experimental Treatment</span>
                                        <p className="experiment-block-text">{experimentsMap[h.id].treatment}</p>
                                      </div>
                                    </div>

                                    <div className="variables-tag-group">
                                      <div className="variable-row">
                                        <span className="variable-row-label">Independent</span>
                                        <div className="variable-tags">
                                          {experimentsMap[h.id].variables.independent?.map((v, key) => (
                                            <span className="variable-tag independent" key={key}>{v}</span>
                                          )) || <span className="variable-tag">None</span>}
                                        </div>
                                      </div>
                                      <div className="variable-row">
                                        <span className="variable-row-label">Dependent</span>
                                        <div className="variable-tags">
                                          {experimentsMap[h.id].variables.dependent?.map((v, key) => (
                                            <span className="variable-tag dependent" key={key}>{v}</span>
                                          )) || <span className="variable-tag">None</span>}
                                        </div>
                                      </div>
                                      <div className="variable-row">
                                        <span className="variable-row-label">Control</span>
                                        <div className="variable-tags">
                                          {experimentsMap[h.id].variables.control?.map((v, key) => (
                                            <span className="variable-tag" key={key}>{v}</span>
                                          )) || <span className="variable-tag">None</span>}
                                        </div>
                                      </div>
                                    </div>

                                    <div className="experiment-block">
                                      <span className="experiment-block-label">Target Metrics</span>
                                      <div className="variable-tags" style={{ marginTop: '0.2rem' }}>
                                        {experimentsMap[h.id].metrics?.map((m, key) => (
                                          <span className="details-tag" key={key} style={{ textTransform: 'none' }}>{m}</span>
                                        )) || <span className="details-tag">None</span>}
                                      </div>
                                    </div>

                                    <div className="experiment-success-criteria">
                                      <span className="experiment-block-label">Measurable Success Criteria</span>
                                      <p className="experiment-block-text" style={{ fontWeight: 600 }}>
                                        🎯 {experimentsMap[h.id].measurable_success_criteria}
                                      </p>
                                    </div>

                                    <div className="experiment-block">
                                      <span className="experiment-block-label">Expected Outcome</span>
                                      <p className="experiment-block-text">{experimentsMap[h.id].expected_outcome}</p>
                                    </div>

                                    <div className="experiment-block">
                                      <span className="experiment-block-label">Step-by-Step Procedure</span>
                                      <ol className="procedure-steps">
                                        {experimentsMap[h.id].procedure?.map((step, key) => (
                                          <li key={key}>{step}</li>
                                        )) || <li>No procedure steps defined.</li>}
                                      </ol>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
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



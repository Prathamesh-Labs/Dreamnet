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

  // Sandbox execution & evaluation state
  const [resultsMap, setResultsMap] = useState<Record<string, any>>({})
  const [loadingResults, setLoadingResults] = useState<Record<string, boolean>>({})
  const [runningMap, setRunningMap] = useState<Record<string, boolean>>({})
  const [evaluatingMap, setEvaluatingMap] = useState<Record<string, boolean>>({})

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

  const fetchExperimentResult = async (experimentId: string) => {
    setLoadingResults(prev => ({ ...prev, [experimentId]: true }))
    try {
      const res = await fetch(`${API_URL}/experiments/${experimentId}/results`)
      if (res.ok) {
        const data = await res.json()
        setResultsMap(prev => ({ ...prev, [experimentId]: data }))
      } else {
        setResultsMap(prev => {
          const updated = { ...prev }
          delete updated[experimentId]
          return updated
        })
      }
    } catch (err) {
      console.error('Error fetching experiment result:', err)
    } finally {
      setLoadingResults(prev => ({ ...prev, [experimentId]: false }))
    }
  }

  const fetchExperiment = async (hypothesisId: string) => {
    setLoadingExperiments(prev => ({ ...prev, [hypothesisId]: true }))
    try {
      const res = await fetch(`${API_URL}/hypotheses/${hypothesisId}/experiment`)
      if (res.ok) {
        const data = await res.json()
        setExperimentsMap(prev => ({ ...prev, [hypothesisId]: data }))
        if (data.status === 'COMPLETED' || data.status === 'FAILED') {
          fetchExperimentResult(data.id)
        }
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

  const handleRunExperiment = async (experimentId: string, hypothesisId: string) => {
    setRunningMap(prev => ({ ...prev, [experimentId]: true }))
    
    // Optimistically update parent status locally
    setExperimentsMap(prev => {
      if (prev[hypothesisId]) {
        return {
          ...prev,
          [hypothesisId]: { ...prev[hypothesisId], status: 'RUNNING' }
        }
      }
      return prev
    })

    try {
      const res = await fetch(`${API_URL}/experiments/${experimentId}/run`, {
        method: 'POST'
      })
      if (res.ok) {
        const resultData = await res.json()
        setResultsMap(prev => ({ ...prev, [experimentId]: resultData }))
        
        // Refresh experiment status from server
        const expRes = await fetch(`${API_URL}/hypotheses/${hypothesisId}/experiment`)
        if (expRes.ok) {
          const expData = await expRes.json()
          setExperimentsMap(prev => ({ ...prev, [hypothesisId]: expData }))
        }
      }
    } catch (err) {
      console.error('Error running experiment:', err)
      // Revert status to READY on fail
      fetchExperiment(hypothesisId)
    } finally {
      setRunningMap(prev => ({ ...prev, [experimentId]: false }))
    }
  }

  const handleEvaluateExperiment = async (experimentId: string, hypothesisId: string) => {
    setEvaluatingMap(prev => ({ ...prev, [experimentId]: true }))
    try {
      const res = await fetch(`${API_URL}/experiments/${experimentId}/evaluate`, {
        method: 'POST'
      })
      if (res.ok) {
        const data = await res.json()
        setResultsMap(prev => ({ ...prev, [experimentId]: data }))
      }
    } catch (err) {
      console.error('Error evaluating experiment:', err)
    } finally {
      setEvaluatingMap(prev => ({ ...prev, [experimentId]: false }))
    }
  }

  const renderEvaluationChecks = (result: any, criteria: string) => {
    if (!result || !result.metrics) return null
    const metrics = result.metrics
    const checks: React.ReactNode[] = []

    if (metrics.p_value !== undefined) {
      const passed = metrics.p_value < 0.05
      checks.push(
        <div className={`check-item ${passed ? 'passed' : 'failed'}`} key="p_value">
          <span className="check-status-icon">{passed ? '✓' : '✗'}</span>
          <span className="check-text">p-value &lt; 0.05 (Observed: {metrics.p_value.toFixed(4)})</span>
        </div>
      )
    }
    
    if (metrics.improvement_percentage !== undefined) {
      const passed = metrics.improvement_percentage >= 10
      checks.push(
        <div className={`check-item ${passed ? 'passed' : 'failed'}`} key="imp">
          <span className="check-status-icon">{passed ? '✓' : '✗'}</span>
          <span className="check-text">improvement &gt;= 10% (Observed: {metrics.improvement_percentage.toFixed(1)}%)</span>
        </div>
      )
    }

    if (metrics.latency_reduction_pct !== undefined) {
      const passed = metrics.latency_reduction_pct >= 20
      checks.push(
        <div className={`check-item ${passed ? 'passed' : 'failed'}`} key="lat">
          <span className="check-status-icon">{passed ? '✓' : '✗'}</span>
          <span className="check-text">latency reduction &gt;= 20% (Observed: {metrics.latency_reduction_pct.toFixed(1)}%)</span>
        </div>
      )
    }

    if (metrics.accuracy_delta !== undefined) {
      const passed = metrics.accuracy_delta < 2
      checks.push(
        <div className={`check-item ${passed ? 'passed' : 'failed'}`} key="acc">
          <span className="check-status-icon">{passed ? '✓' : '✗'}</span>
          <span className="check-text">accuracy loss &lt; 2% (Observed: {metrics.accuracy_delta.toFixed(2)}%)</span>
        </div>
      )
    }

    if (metrics.accuracy_gain !== undefined) {
      const passed = metrics.accuracy_gain >= 5
      checks.push(
        <div className={`check-item ${passed ? 'passed' : 'failed'}`} key="acc_gain">
          <span className="check-status-icon">{passed ? '✓' : '✗'}</span>
          <span className="check-text">accuracy gain &gt;= 5% (Observed: {metrics.accuracy_gain.toFixed(2)}%)</span>
        </div>
      )
    }

    if (checks.length === 0) return null

    return (
      <div className="checks-checklist">
        <span className="checklist-title">Verification Assertions Checklist</span>
        <div className="checklist-grid">
          {checks}
        </div>
      </div>
    )
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
                                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    {experimentsMap[h.id] && (experimentsMap[h.id].status === 'READY' || experimentsMap[h.id].status === 'FAILED') && (
                                      <button 
                                        className="run-exp-btn"
                                        onClick={() => handleRunExperiment(experimentsMap[h.id].id, h.id)}
                                        disabled={runningMap[experimentsMap[h.id].id]}
                                      >
                                        {runningMap[experimentsMap[h.id].id] ? 'Running...' : '🚀 Run Experiment'}
                                      </button>
                                    )}
                                    {experimentsMap[h.id] && (
                                      <button 
                                        className="redesign-exp-btn"
                                        onClick={() => handleDesignExperiment(h.id)}
                                        disabled={designingMap[h.id] || experimentsMap[h.id].status === 'RUNNING' || runningMap[experimentsMap[h.id].id]}
                                      >
                                        {designingMap[h.id] ? 'Designing...' : '🔄 Redesign'}
                                      </button>
                                    )}
                                  </div>
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

                                    {/* Sandbox Console / Execution Log Viewer */}
                                    {(experimentsMap[h.id].status === 'RUNNING' || resultsMap[experimentsMap[h.id].id]) && (
                                      <div className="sandbox-logs-section">
                                        <span className="experiment-block-label">Sandbox Terminal Execution Logs</span>
                                        
                                        <div className="terminal-window">
                                          <div className="terminal-header">
                                            <div className="terminal-buttons">
                                              <span className="term-btn red"></span>
                                              <span className="term-btn yellow"></span>
                                              <span className="term-btn green"></span>
                                            </div>
                                            <span className="terminal-title">dreamnet-sandbox-run.log</span>
                                            <span className="terminal-timer">
                                              {resultsMap[experimentsMap[h.id].id] ? `${(resultsMap[experimentsMap[h.id].id].execution_time_ms).toFixed(1)}ms` : 'RUNNING...'}
                                            </span>
                                          </div>
                                          
                                          <pre className="terminal-content">
                                            {experimentsMap[h.id].status === 'RUNNING' ? (
                                              <code className="pulsing-text">
                                                [DREAMNET SANDBOX] Initializing isolated subprocess environment...
                                                [DREAMNET SANDBOX] Parsing AST verification tree...
                                                [DREAMNET SANDBOX] AST Validation: SUCCESS (No dangerous modules or operations detected).
                                                [DREAMNET SANDBOX] Running Python script in restricted subprocess...
                                                [DREAMNET SANDBOX] Waiting for execution output...
                                              </code>
                                            ) : (
                                              <code>
                                                {resultsMap[experimentsMap[h.id].id].stdout && (
                                                  <span style={{ color: 'var(--text-main)' }}>{resultsMap[experimentsMap[h.id].id].stdout}</span>
                                                )}
                                                {resultsMap[experimentsMap[h.id].id].stderr && (
                                                  <span style={{ color: 'var(--status-red)' }}>{resultsMap[experimentsMap[h.id].id].stderr}</span>
                                                )}
                                              </code>
                                            )}
                                          </pre>
                                        </div>

                                        {/* Extracted Metrics Block */}
                                        {resultsMap[experimentsMap[h.id].id] && resultsMap[experimentsMap[h.id].id].metrics && (
                                          <div className="extracted-metrics-container">
                                            <span className="experiment-block-label" style={{ color: 'var(--status-green)' }}>Extracted Quantitative Metrics</span>
                                            <div className="metrics-pill-grid">
                                              {Object.entries(resultsMap[experimentsMap[h.id].id].metrics).map(([key, val]) => (
                                                <div className="metric-pill-item" key={key}>
                                                  <span className="metric-key">{key.replace(/_/g, ' ')}</span>
                                                  <span className="metric-val">
                                                    {typeof val === 'number' ? val.toFixed(2) : String(val)}
                                                  </span>
                                                </div>
                                              ))}
                                            </div>
                                          </div>
                                        )}

                                        {/* Evaluate Evidence Trigger */}
                                        {resultsMap[experimentsMap[h.id].id] && !resultsMap[experimentsMap[h.id].id].verdict && (
                                          <button 
                                            className="evaluate-btn"
                                            onClick={() => handleEvaluateExperiment(experimentsMap[h.id].id, h.id)}
                                            disabled={evaluatingMap[experimentsMap[h.id].id]}
                                            style={{ marginTop: '0.5rem', width: '100%' }}
                                          >
                                            {evaluatingMap[experimentsMap[h.id].id] ? 'Evaluating Evidence...' : '🧠 Evaluate Evidence & Generate Verdict'}
                                          </button>
                                        )}

                                        {/* Evaluation Outcomes Panel */}
                                        {resultsMap[experimentsMap[h.id].id] && resultsMap[experimentsMap[h.id].id].verdict && (
                                          <div className="evaluation-summary-section">
                                            <span className="experiment-block-label">Evaluation Engine Outcome</span>
                                            
                                            <div className={`verdict-banner ${resultsMap[experimentsMap[h.id].id].verdict.toLowerCase()}`}>
                                              <div className="verdict-icon">
                                                {resultsMap[experimentsMap[h.id].id].verdict === 'SUPPORTED' ? '🛡️' : 
                                                 resultsMap[experimentsMap[h.id].id].verdict === 'REJECTED' ? '⚠️' : '❓'}
                                              </div>
                                              <div className="verdict-text-group">
                                                <span className="verdict-title">VERDICT: {resultsMap[experimentsMap[h.id].id].verdict}</span>
                                                <span className="verdict-confidence">Confidence: {(resultsMap[experimentsMap[h.id].id].evaluation_confidence * 100).toFixed(0)}%</span>
                                              </div>
                                            </div>

                                            {/* Dynamic Assertions Checklist */}
                                            {renderEvaluationChecks(resultsMap[experimentsMap[h.id].id], experimentsMap[h.id].measurable_success_criteria)}

                                            {/* LLM Observation summary box */}
                                            {resultsMap[experimentsMap[h.id].id].evaluation_summary && (
                                              <div className="observation-box">
                                                <span className="observation-title">📋 Observation Interpretation Summary</span>
                                                <p className="observation-text">
                                                  {resultsMap[experimentsMap[h.id].id].evaluation_summary}
                                                </p>
                                              </div>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    )}
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

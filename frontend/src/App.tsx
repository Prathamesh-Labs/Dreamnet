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
  approved: boolean
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
  peer_review?: any[]
  created_at: string
}

interface Question {
  id: string
  text: string
  project_id: string | null
  status: string
  created_at: string
}

interface TelemetryState {
  thruster_temp: number
  solar_current: number
  battery_voltage: number
  gyro_drift: number
  propellant_pressure: number
  avionics_temp: number
  status: string
}

interface DiscoveryCardProps {
  discovery: any
  questionId: string
  sessionId: string
  onValidate: (id: string, status: string, questionId: string, sessionId: string) => void
  onSpawnLead: (id: string, text: string) => void
}

function DiscoveryCard({ discovery, questionId, sessionId, onValidate, onSpawnLead }: DiscoveryCardProps) {
  const [showSpawnForm, setShowSpawnForm] = useState(false)
  const [spawnQuestionText, setSpawnQuestionText] = useState('')

  const handleOpenSpawn = () => {
    setShowSpawnForm(true)
    setSpawnQuestionText(`Follow-up: Investigate root cause of '${discovery.title}' observed during trials.`)
  }

  return (
    <div className={`discovery-card ${discovery.status.toLowerCase()}`}>
      <div className="discovery-header">
        <span className="discovery-type-badge">{(discovery.pattern_type || 'Emergent_Finding').replace(/_/g, ' ')}</span>
        <span className={`discovery-status-badge ${discovery.status.toLowerCase()}`}>{discovery.status}</span>
      </div>
      
      <h4 className="discovery-title">{discovery.title}</h4>
      <p className="discovery-observation">{discovery.observation}</p>

      {discovery.evidence && Object.keys(discovery.evidence).length > 0 && (
        <div className="discovery-evidence-box">
          <span className="evidence-box-label">Scanned Evidence</span>
          <pre className="evidence-raw">
            {JSON.stringify(discovery.evidence, null, 2)}
          </pre>
        </div>
      )}

      {/* Metrics Row */}
      <div className="discovery-metrics-row">
        <div className="metric-indicator">
          <span className="metric-label">Novelty</span>
          <span className="metric-value">{(discovery.novelty_score * 100).toFixed(0)}%</span>
        </div>
        <div className="metric-indicator">
          <span className="metric-label">Confidence</span>
          <span className="metric-value">{(discovery.confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="metric-indicator">
          <span className="metric-label">Significance</span>
          <span className="metric-value">{(discovery.significance * 100).toFixed(0)}%</span>
        </div>
      </div>

      <div className="discovery-actions">
        {discovery.status === 'CANDIDATE' && (
          <>
            <button className="disc-btn confirm" onClick={() => onValidate(discovery.id, 'CONFIRMED', questionId, sessionId)}>
              ✓ Confirm Findings
            </button>
            <button className="disc-btn dismiss" onClick={() => onValidate(discovery.id, 'DISMISSED', questionId, sessionId)}>
              ✗ Dismiss
            </button>
          </>
        )}

        {discovery.status === 'CONFIRMED' && !showSpawnForm && (
          <button className="disc-btn spawn-trigger" onClick={handleOpenSpawn}>
            🎯 Spawn Child Research Question
          </button>
        )}
      </div>

      {showSpawnForm && (
        <form 
          className="spawn-lead-form" 
          onSubmit={(e) => {
            e.preventDefault()
            onSpawnLead(discovery.id, spawnQuestionText)
            setShowSpawnForm(false)
          }}
        >
          <div className="form-group-spawn">
            <label>Child Question Statement</label>
            <textarea
              rows={3}
              value={spawnQuestionText}
              onChange={(e) => setSpawnQuestionText(e.target.value)}
              placeholder="Enter spawned research question..."
            />
          </div>
          <div className="spawn-form-actions">
            <button type="submit" className="spawn-submit-btn">
              Launch Child Thread
            </button>
            <button type="button" className="spawn-cancel-btn" onClick={() => setShowSpawnForm(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

function App() {
  const [questionText, setQuestionText] = useState('')
  const [questionsList, setQuestionsList] = useState<Question[]>([])
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline'>('offline')
  const [dbStatus, setDbStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking')
  const [dbError, setDbError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  // Telemetry Simulator state
  const [telemetry, setTelemetry] = useState<TelemetryState>({
    thruster_temp: 24.5,
    solar_current: 8.4,
    battery_voltage: 28.2,
    gyro_drift: 0.01,
    propellant_pressure: 1.2,
    avionics_temp: 18.2,
    status: 'NOMINAL'
  })
  const [isTelemetryLoading, setIsTelemetryLoading] = useState(false)

  // Selected Question & state tracking
  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(null)
  const [hypothesesMap, setHypothesesMap] = useState<Record<string, Hypothesis[]>>({})
  const [loadingHypotheses, setLoadingHypotheses] = useState<Record<string, boolean>>({})
  const [regeneratingMap, setRegeneratingMap] = useState<Record<string, boolean>>({})

  // Collapsible state for hypotheses cards
  const [hypothesesCollapsed, setHypothesesCollapsed] = useState<Record<string, boolean>>({})

  // Discoveries state
  const [discoveriesMap, setDiscoveriesMap] = useState<Record<string, any[]>>({})
  const [allDiscoveries, setAllDiscoveries] = useState<any[]>([])

  // Experiment details state
  const [experimentsMap, setExperimentsMap] = useState<Record<string, Experiment>>({})
  const [loadingExperiments, setLoadingExperiments] = useState<Record<string, boolean>>({})
  const [designingMap, setDesigningMap] = useState<Record<string, boolean>>({})

  // Sandbox execution & evaluation state
  const [resultsMap, setResultsMap] = useState<Record<string, any>>({})
  const [evaluationsMap, setEvaluationsMap] = useState<Record<string, any>>({})
  const [loadingResults, setLoadingResults] = useState<Record<string, boolean>>({})
  const [runningMap, setRunningMap] = useState<Record<string, boolean>>({})
  const [evaluatingMap, setEvaluatingMap] = useState<Record<string, boolean>>({})

  // Research Loop session state
  const [sessionsMap, setSessionsMap] = useState<Record<string, any>>({})
  const [loadingSessions, setLoadingSessions] = useState<Record<string, boolean>>({})
  const [approvingMap, setApprovingMap] = useState<Record<string, boolean>>({})

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

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

  // Fetch all discoveries globally
  const fetchAllDiscoveries = async () => {
    try {
      const res = await fetch(`${API_URL}/discoveries`)
      if (res.ok) {
        const data = await res.json()
        setAllDiscoveries(data)
      }
    } catch (err) {
      console.error('Error fetching all discoveries:', err)
    }
  }

  // Fetch session-specific discoveries
  const fetchDiscoveries = async (questionId: string, sessionId: string) => {
    try {
      const res = await fetch(`${API_URL}/research/${sessionId}/discoveries`)
      if (res.ok) {
        const data = await res.json()
        setDiscoveriesMap(prev => ({ ...prev, [questionId]: data }))
      }
    } catch (err) {
      console.error('Error fetching session discoveries:', err)
    }
  }

  // Fetch Spacecraft Telemetry Status
  const fetchTelemetryStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/telemetry/status`)
      if (res.ok) {
        const data = await res.json()
        setTelemetry(data)
      }
    } catch (err) {
      console.error('Error fetching telemetry:', err)
    }
  }

  // Auto-fetch research session when question card expands
  const fetchResearchSession = async (questionId: string) => {
    setLoadingSessions(prev => ({ ...prev, [questionId]: true }))
    try {
      const res = await fetch(`${API_URL}/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: questionId, budget: 5 })
      })
      if (res.ok) {
        const data = await res.json()
        setSessionsMap(prev => ({ ...prev, [questionId]: data }))
        fetchDiscoveries(questionId, data.id)
      }
    } catch (err) {
      console.error('Error fetching research session:', err)
    } finally {
      setLoadingSessions(prev => ({ ...prev, [questionId]: false }))
    }
  }

  // Refresh research session details periodically if running
  const refreshResearchSessionStatus = async (questionId: string, sessionId: string) => {
    try {
      const res = await fetch(`${API_URL}/research/${sessionId}`)
      if (res.ok) {
        const data = await res.json()
        setSessionsMap(prev => ({ ...prev, [questionId]: data }))
        if (data.status === 'RUNNING' || data.status === 'PAUSED' || data.status === 'COMPLETED') {
          fetchHypotheses(questionId)
          fetchDiscoveries(questionId, sessionId)
          fetchAllDiscoveries()
        }
      }
    } catch (err) {
      console.error('Error refreshing session status:', err)
    }
  }

  useEffect(() => {
    checkHealth()
    fetchQuestions()
    fetchAllDiscoveries()
    fetchTelemetryStatus()
    const interval = setInterval(() => {
      checkHealth()
      fetchTelemetryStatus()
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  // Poll active research sessions to keep loop iteration counts fresh
  useEffect(() => {
    const activeQuestions = Object.keys(sessionsMap).filter(
      qId => sessionsMap[qId] && (sessionsMap[qId].status === 'RUNNING' || sessionsMap[qId].status === 'PAUSED')
    )
    if (activeQuestions.length === 0) return

    const interval = setInterval(() => {
      activeQuestions.forEach(qId => {
        refreshResearchSessionStatus(qId, sessionsMap[qId].id)
      })
    }, 3000)

    return () => clearInterval(interval)
  }, [sessionsMap])

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
        
        // Auto expand and fetch hypotheses/session for the newly created question
        setExpandedQuestionId(newQuestion.id)
        fetchHypotheses(newQuestion.id)
        fetchResearchSession(newQuestion.id)
        fetchAllDiscoveries()
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

  // Telemetry event handlers
  const handleTriggerTelemetryAnomaly = async () => {
    setIsTelemetryLoading(true)
    try {
      const res = await fetch(`${API_URL}/telemetry/anomaly`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setTelemetry(data)
        
        // Formulate and auto-submit the repair question!
        const autoQuestionText = "Resolve Spacecraft Thruster Solenoid Thermal Drift: Optimize duty-cycle to reduce thruster temperature to safe levels (<75.0C) without increasing thruster latency by >10%."
        setQuestionText(autoQuestionText)
        setMessage("🚨 CRITICAL TELEMETRY DRIFT DETECTED! Initializing emergency research question to resolve thruster thermal malfunction...")
        
        // Auto-submit the form
        setTimeout(async () => {
          try {
            const qRes = await fetch(`${API_URL}/questions`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text: autoQuestionText })
            })
            if (qRes.ok) {
              const newQuestion = await qRes.json()
              setQuestionsList(prev => [newQuestion, ...prev])
              setQuestionText('')
              setExpandedQuestionId(newQuestion.id)
              fetchHypotheses(newQuestion.id)
              fetchResearchSession(newQuestion.id)
              fetchAllDiscoveries()
              
              // Immediately start the loop for this question
              setTimeout(async () => {
                try {
                  const sRes = await fetch(`${API_URL}/research`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question_id: newQuestion.id, budget: 5 })
                  })
                  if (sRes.ok) {
                    const sData = await sRes.json()
                    setSessionsMap(prev => ({ ...prev, [newQuestion.id]: sData }))
                    // Trigger the loop start
                    await fetch(`${API_URL}/research/${sData.id}/start`, { method: 'POST' })
                    const activeRes = await fetch(`${API_URL}/research/${sData.id}`)
                    if (activeRes.ok) {
                      const activeData = await activeRes.json()
                      setSessionsMap(prev => ({ ...prev, [newQuestion.id]: activeData }))
                    }
                  }
                } catch (err) {
                  console.error('Error starting research session loop:', err)
                }
              }, 1000)
            }
          } catch (err) {
            console.error('Error registering emergency question:', err)
          }
        }, 1500)
      }
    } catch (err) {
      console.error('Error triggering anomaly:', err)
    } finally {
      setIsTelemetryLoading(false)
    }
  }

  const handleResolveTelemetryAnomaly = async () => {
    setIsTelemetryLoading(true)
    try {
      const res = await fetch(`${API_URL}/telemetry/resolve`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setTelemetry(data)
        setMessage("✓ Spacecraft telemetry returned to nominal baselines. Thruster cooling active.")
      }
    } catch (err) {
      console.error('Error resolving anomaly:', err)
    } finally {
      setIsTelemetryLoading(false)
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

  const fetchExperimentEvaluation = async (experimentId: string) => {
    try {
      const res = await fetch(`${API_URL}/experiments/${experimentId}/evaluation`)
      if (res.ok) {
        const data = await res.json()
        setEvaluationsMap(prev => ({ ...prev, [experimentId]: data }))
      } else {
        setEvaluationsMap(prev => {
          const updated = { ...prev }
          delete updated[experimentId]
          return updated
        })
      }
    } catch (err) {
      console.error('Error fetching evaluation:', err)
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
          fetchExperimentEvaluation(data.id)
        }
      } else {
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
    fetchResearchSession(questionId)
  }

  const handleRegenerateHypotheses = async (e: React.MouseEvent, questionId: string) => {
    e.stopPropagation()
    setRegeneratingMap(prev => ({ ...prev, [questionId]: true }))
    try {
      const res = await fetch(`${API_URL}/questions/${questionId}/hypotheses/generate`, {
        method: 'POST'
      })
      if (res.ok) {
        const data = await res.json()
        setHypothesesMap(prev => ({ ...prev, [questionId]: data }))
        
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
        
        const expRes = await fetch(`${API_URL}/hypotheses/${hypothesisId}/experiment`)
        if (expRes.ok) {
          const expData = await expRes.json()
          setExperimentsMap(prev => ({ ...prev, [hypothesisId]: expData }))
        }
      }
    } catch (err) {
      console.error('Error running experiment:', err)
      fetchExperiment(hypothesisId)
    } finally {
      setRunningMap(prev => ({ ...prev, [experimentId]: false }))
    }
  }

  const handleEvaluateExperiment = async (experimentId: string, _hypothesisId: string) => {
    setEvaluatingMap(prev => ({ ...prev, [experimentId]: true }))
    try {
      const res = await fetch(`${API_URL}/experiments/${experimentId}/evaluate`, {
        method: 'POST'
      })
      if (res.ok) {
        const data = await res.json()
        setEvaluationsMap(prev => ({ ...prev, [experimentId]: data }))
      }
    } catch (err) {
      console.error('Error evaluating experiment:', err)
    } finally {
      setEvaluatingMap(prev => ({ ...prev, [experimentId]: false }))
    }
  }

  // Research Loop Controllers
  const handleControlSession = async (action: 'start' | 'pause' | 'resume' | 'stop', questionId: string, sessionId: string) => {
    try {
      const res = await fetch(`${API_URL}/research/${sessionId}/${action}`, {
        method: 'POST'
      })
      if (res.ok) {
        const data = await res.json()
        setSessionsMap(prev => ({ ...prev, [questionId]: data }))
        fetchHypotheses(questionId)
        fetchDiscoveries(questionId, sessionId)
        fetchAllDiscoveries()
      }
    } catch (err) {
      console.error(`Error performing ${action} on session:`, err)
    }
  }

  const handleApproveExperiment = async (experimentId: string, _hypothesisId: string, questionId: string) => {
    setApprovingMap(prev => ({ ...prev, [experimentId]: true }))
    try {
      const res = await fetch(`${API_URL}/experiments/${experimentId}/approve`, {
        method: 'POST'
      })
      if (res.ok) {
        fetchHypotheses(questionId)
        const session = sessionsMap[questionId]
        if (session) {
          const sRes = await fetch(`${API_URL}/research/${session.id}`)
          if (sRes.ok) {
            const sData = await sRes.json()
            setSessionsMap(prev => ({ ...prev, [questionId]: sData }))
            fetchDiscoveries(questionId, session.id)
            fetchAllDiscoveries()
          }
        }
      }
    } catch (err) {
      console.error('Error approving experiment:', err)
    } finally {
      setApprovingMap(prev => ({ ...prev, [experimentId]: false }))
    }
  }

  // Handle validating discovery candidates
  const handleValidateDiscovery = async (discoveryId: string, status: string, questionId: string, sessionId: string) => {
    try {
      const res = await fetch(`${API_URL}/discoveries/${discoveryId}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      })
      if (res.ok) {
        fetchDiscoveries(questionId, sessionId)
        fetchAllDiscoveries()
      }
    } catch (err) {
      console.error('Error validating discovery candidate:', err)
    }
  }

  // Handle spawning child research questions
  const handleSpawnLead = async (discoveryId: string, questionTextVal: string) => {
    try {
      const res = await fetch(`${API_URL}/discoveries/${discoveryId}/spawn_lead`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_text: questionTextVal })
      })
      if (res.ok) {
        setMessage('Successfully spawned child research inquiry lead!')
        fetchQuestions()
        fetchAllDiscoveries()
      }
    } catch (err) {
      console.error('Error spawning research lead:', err)
    }
  }

  const toggleHypothesisCollapse = (hypothesisId: string) => {
    setHypothesesCollapsed(prev => ({
      ...prev,
      [hypothesisId]: prev[hypothesisId] === undefined ? false : !prev[hypothesisId]
    }))
  }

  const renderEvaluationChecks = (evaluation: any) => {
    if (!evaluation || !evaluation.evidence) return null
    return (
      <div className="checks-checklist">
        <span className="checklist-title">Verification Assertions Checklist</span>
        <div className="checklist-grid">
          {evaluation.evidence.map((c: any, idx: number) => (
            <div className={`check-item ${c.passed ? 'passed' : 'failed'}`} key={idx}>
              <span className="check-status-icon">{c.passed ? '✓' : '✗'}</span>
              <span className="check-text">
                {c.rule} (Observed: {typeof c.observed === 'number' ? c.observed.toFixed(4) : String(c.observed)})
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Get active step index for pipeline stepper
  const getActivePipelineStep = (questionId: string) => {
    let step = 0 // Question formulated
    const hypotheses = hypothesesMap[questionId] || []
    if (hypotheses.length > 0) {
      step = 1 // Hypotheses generated
      const hasExperiment = hypotheses.some(h => experimentsMap[h.id])
      if (hasExperiment) {
        step = 2 // Experiment designed
        const hasEvaluation = hypotheses.some(h => {
          const exp = experimentsMap[h.id]
          return exp && evaluationsMap[exp.id]
        })
        if (hasEvaluation) {
          step = 3 // Evidence evaluated
          const discoveries = discoveriesMap[questionId] || []
          if (discoveries.length > 0) {
            step = 4 // Emergent discoveries scanned
          }
        }
      }
    }
    return step
  }

  // Helper to render step progress
  const renderPipelineStepper = (questionId: string) => {
    const activeStep = getActivePipelineStep(questionId)
    const steps = [
      { label: 'Question Formulated', icon: '❓' },
      { label: 'Competing Hypotheses', icon: '🧬' },
      { label: 'Experiment Spec Designed', icon: '🧪' },
      { label: 'Evidence Evaluated', icon: '🔍' },
      { label: 'Emergent Discoveries', icon: '🎯' }
    ]

    return (
      <div className="pipeline-stepper-container">
        <div className="stepper-header-title">Research Pipeline Status</div>
        <div className="pipeline-stepper">
          {steps.map((s, idx) => {
            const isCompleted = idx < activeStep
            const isActive = idx === activeStep
            const isPending = idx > activeStep
            return (
              <div className={`stepper-step ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''} ${isPending ? 'pending' : ''}`} key={idx}>
                <div className="step-circle">
                  <span className="step-icon">{s.icon}</span>
                  {isCompleted && <span className="step-check">✓</span>}
                </div>
                <span className="step-label">{s.label}</span>
                {idx < steps.length - 1 && <div className="step-connector"></div>}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderControlRoom = (qId: string) => {
    const session = sessionsMap[qId]
    if (loadingSessions[qId]) {
      return <div className="shimmer-line body-1" style={{ margin: '1rem 0' }}></div>
    }
    if (!session) return null

    return (
      <div className="research-control-room">
        <div className="control-room-header">
          <span className="control-room-icon">🔬</span>
          <h4>Research Control Room</h4>
          <span className={`session-status-badge ${session.status.toLowerCase()}`}>
            {session.status}
          </span>
        </div>

        <div className="control-room-details">
          <div className="detail-stat">
            <span className="stat-label">Iteration Loop:</span>
            <span className="stat-value">{session.iteration} / {session.budget}</span>
          </div>
          <div className="detail-stat">
            <span className="stat-label">Hypotheses Tracked:</span>
            <span className="stat-value">{hypothesesMap[qId]?.length || 0}</span>
          </div>
          <div className="detail-stat">
            <span className="stat-label">Evaluation Engine Verdicts:</span>
            <span className="stat-value">
              {hypothesesMap[qId]?.filter(h => h.status === 'SUPPORTED').length || 0} Supported |{' '}
              {hypothesesMap[qId]?.filter(h => h.status === 'REJECTED').length || 0} Rejected
            </span>
          </div>

          <div className="control-room-actions">
            {session.status === 'IDLE' && (
              <button className="ctrl-btn start" onClick={() => handleControlSession('start', qId, session.id)}>
                ▶ Start Loop
              </button>
            )}
            {session.status === 'RUNNING' && (
              <button className="ctrl-btn pause" onClick={() => handleControlSession('pause', qId, session.id)}>
                ⏸ Pause Loop
              </button>
            )}
            {session.status === 'PAUSED' && (
              <button className="ctrl-btn resume" onClick={() => handleControlSession('resume', qId, session.id)}>
                ▶ Resume Loop
              </button>
            )}
            {session.status !== 'STOPPED' && session.status !== 'COMPLETED' && (
              <button className="ctrl-btn stop" onClick={() => handleControlSession('stop', qId, session.id)}>
                ⏹ Stop Loop
              </button>
            )}
            {(session.status === 'STOPPED' || session.status === 'COMPLETED') && (
              <button className="ctrl-btn start" onClick={() => handleControlSession('start', qId, session.id)}>
                🔄 Restart Loop
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  const renderExperimentSpec = (h: Hypothesis) => {
    const exp = experimentsMap[h.id]
    if (loadingExperiments[h.id] || designingMap[h.id]) {
      return (
        <div className="shimmer-card" style={{ padding: '1rem', gap: '0.5rem', marginTop: '1rem' }}>
          <div className="shimmer-line title" style={{ width: '40%' }}></div>
          <div className="shimmer-line body-1"></div>
          <div className="shimmer-line body-2" style={{ width: '80%' }}></div>
        </div>
      )
    }

    if (!exp) {
      return (
        <div className="no-exp-state" style={{ marginTop: '1rem' }}>
          <p>No experiment designed yet.</p>
          <button 
            className="design-exp-btn"
            onClick={() => handleDesignExperiment(h.id)}
          >
            Design Experiment Spec
          </button>
        </div>
      )
    }

    const res = resultsMap[exp.id]
    const val = evaluationsMap[exp.id]

    return (
      <div className="experiment-section" style={{ marginTop: '1.2rem' }}>
        <div className="experiment-header-row">
          <div className="experiment-title">
            <span>🧪 Experiment Specification</span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {exp.approved && (exp.status === 'READY' || exp.status === 'FAILED') && (
              <button 
                className="run-exp-btn"
                onClick={() => handleRunExperiment(exp.id, h.id)}
                disabled={runningMap[exp.id]}
              >
                {runningMap[exp.id] ? 'Running...' : '🚀 Run Experiment'}
              </button>
            )}
            <button 
              className="redesign-exp-btn"
              onClick={() => handleDesignExperiment(h.id)}
              disabled={designingMap[h.id] || exp.status === 'RUNNING' || runningMap[exp.id]}
            >
              {designingMap[h.id] ? 'Designing...' : '🔄 Redesign'}
            </button>
          </div>
        </div>

        <div className="experiment-container">
          {/* Human-in-the-Loop Approval prompt */}
          {!exp.approved && (
            <div className="approval-required-container">
              <div className="approval-header">
                <span className="warning-icon">👤</span>
                <span>Human Approval Required</span>
              </div>
              <p className="approval-desc">
                Review this experiment plan before allowing DREAMNET sandbox run:
              </p>
              <button 
                className="approve-run-btn"
                onClick={() => handleApproveExperiment(exp.id, h.id, h.question_id)}
                disabled={approvingMap[exp.id]}
              >
                {approvingMap[exp.id] ? 'Approving...' : '✓ Approve Plan & Execute'}
              </button>
            </div>
          )}

          <div className="experiment-header-row" style={{ margin: 0, paddingBottom: '0.5rem' }}>
            <div className="experiment-block">
              <span className="experiment-block-label">Status</span>
              <span className={`experiment-status-pill ${exp.status}`}>
                {exp.status}
              </span>
            </div>
            <div className="experiment-block" style={{ alignItems: 'flex-end' }}>
              <span className="experiment-block-label">Dataset</span>
              <p className="experiment-block-text" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', margin: 0 }}>
                {exp.dataset}
              </p>
            </div>
          </div>

          <div className="experiment-block">
            <span className="experiment-block-label">Objective</span>
            <p className="experiment-block-text">{exp.objective}</p>
          </div>

          <div className="experiment-comparison-grid">
            <div className="comparison-card baseline">
              <span className="experiment-block-label">Baseline Configuration</span>
              <p className="experiment-block-text">{exp.baseline}</p>
            </div>
            <div className="comparison-card treatment">
              <span className="experiment-block-label">Experimental Treatment</span>
              <p className="experiment-block-text">{exp.treatment}</p>
            </div>
          </div>

          <div className="variables-tag-group">
            <div className="variable-row">
              <span className="variable-row-label">Independent</span>
              <div className="variable-tags">
                {exp.variables.independent?.map((v, key) => (
                  <span className="variable-tag independent" key={key}>{v}</span>
                )) || <span className="variable-tag">None</span>}
              </div>
            </div>
            <div className="variable-row">
              <span className="variable-row-label">Dependent</span>
              <div className="variable-tags">
                {exp.variables.dependent?.map((v, key) => (
                  <span className="variable-tag dependent" key={key}>{v}</span>
                )) || <span className="variable-tag">None</span>}
              </div>
            </div>
          </div>

          <div className="experiment-success-criteria">
            <span className="experiment-block-label">Measurable Success Criteria</span>
            <p className="experiment-block-text" style={{ fontWeight: 600 }}>
              🎯 {exp.measurable_success_criteria}
            </p>
          </div>

          {/* Sandbox Console / Execution Log Viewer */}
          {(exp.status === 'RUNNING' || res) && (
            <div className="sandbox-logs-section" style={{ marginTop: '1rem' }}>
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
                    {res ? `${(res.execution_time_ms).toFixed(1)}ms` : 'RUNNING...'}
                  </span>
                </div>
                
                <pre className="terminal-content">
                  {exp.status === 'RUNNING' ? (
                    <code className="pulsing-text">
                      [DREAMNET SANDBOX] Initializing isolated subprocess environment...
                      [DREAMNET SANDBOX] Parsing AST verification tree...
                      [DREAMNET SANDBOX] AST Validation: SUCCESS (No dangerous modules or operations detected).
                      [DREAMNET SANDBOX] Running Python script in restricted subprocess...
                      [DREAMNET SANDBOX] Waiting for execution output...
                    </code>
                  ) : (
                    <code>
                      {res?.raw_output && (
                        <span style={{ color: 'var(--text-main)' }}>{res.raw_output}</span>
                      )}
                    </code>
                  )}
                </pre>
              </div>
            </div>
          )}

          {/* Extracted Metrics Block */}
          {res && res.metrics && (
            <div className="extracted-metrics-container" style={{ marginTop: '1rem' }}>
              <span className="experiment-block-label" style={{ color: 'var(--status-green)' }}>Extracted Quantitative Metrics</span>
              <div className="metrics-pill-grid">
                {Object.entries(res.metrics).map(([key, val]) => (
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
          {res && !val && (
            <button 
              className="evaluate-btn"
              onClick={() => handleEvaluateExperiment(exp.id, h.id)}
              disabled={evaluatingMap[exp.id]}
              style={{ marginTop: '0.5rem', width: '100%' }}
            >
              {evaluatingMap[exp.id] ? 'Evaluating Evidence...' : '🧠 Evaluate Evidence & Generate Verdict'}
            </button>
          )}

          {/* Evaluation Outcomes Panel */}
          {val && (
            <div className="evaluation-summary-section" style={{ marginTop: '1rem' }}>
              <span className="experiment-block-label">Evaluation Engine Outcome</span>
              
              <div className={`verdict-banner ${val.verdict.toLowerCase()}`}>
                <div className="verdict-icon">
                  {val.verdict === 'SUPPORTED' ? '🛡️' : 
                   val.verdict === 'REJECTED' ? '⚠️' : '❓'}
                </div>
                <div className="verdict-text-group">
                  <span className="verdict-title">VERDICT: {val.verdict}</span>
                  <span className="verdict-confidence">Confidence: {(val.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>

              {/* Dynamic Assertions Checklist */}
              {renderEvaluationChecks(val)}

              {/* LLM Observation summary box */}
              {val.observations && (
                <div className="observation-box" style={{ marginTop: '0.5rem' }}>
                  <span className="observation-title">📋 Observation Interpretation Summary</span>
                  <p className="observation-text">
                    {val.observations}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  // Renders ④ Discovery panel
  const renderDiscoveryPanel = (questionId: string) => {
    const discoveries = discoveriesMap[questionId] || []
    const session = sessionsMap[questionId]
    if (!session) return null

    return (
      <div className="discoveries-section">
        <div className="panel-header-discoveries">
          <span className="discoveries-icon">🎯</span>
          <h3>Emergent Discovery Engine ({discoveries.length})</h3>
          <p className="panel-desc">DREAMNET real-time anomalous patterns scanned from sandbox execution.</p>
        </div>

        {discoveries.length === 0 ? (
          <div className="discovery-empty-state">
            <p>No anomalous patterns detected yet. Launch loop and execute experiments to scan for discoveries.</p>
          </div>
        ) : (
          <div className="discoveries-grid">
            {discoveries.map(d => (
              <DiscoveryCard 
                key={d.id} 
                discovery={d} 
                questionId={questionId} 
                sessionId={session.id} 
                onValidate={handleValidateDiscovery}
                onSpawnLead={handleSpawnLead}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  const getSpawnedQuestionId = (recommendedAction: string | null): string | null => {
    if (!recommendedAction) return null
    const match = recommendedAction.match(/Child Question Spawned:\s*([\w-]+)/)
    return match ? match[1] : null
  }

  // Renders ⑤ Research Lineage Graph tree nodes
  const renderLineageTree = (questionId: string, level = 0) => {
    const question = questionsList.find(q => q.id === questionId)
    if (!question) return null

    // Find discoveries for this question's active session
    const discoveries = allDiscoveries.filter(d => d.question_id === questionId)

    return (
      <div className="lineage-tree-level" key={questionId} style={{ marginLeft: level > 0 ? '1.5rem' : '0' }}>
        <div className="lineage-node-connector-group">
          {level > 0 && <div className="connector-horizontal-arm"></div>}
          <div className={`lineage-node-question ${expandedQuestionId === questionId ? 'active' : ''}`} onClick={() => handleToggleExpand(questionId)}>
            <span className="lineage-node-icon">❓</span>
            <div className="lineage-node-content">
              <span className="lineage-node-title">Question {question.id.substring(0, 8)}</span>
              <p className="lineage-node-text">{question.text}</p>
            </div>
          </div>
        </div>

        {discoveries.length > 0 && (
          <div className="lineage-branches-container">
            <div className="connector-vertical-spine"></div>
            {discoveries.map(d => {
              const childQuestionId = getSpawnedQuestionId(d.recommended_action)
              return (
                <div className="lineage-discovery-branch" key={d.id}>
                  <div className="lineage-discovery-card-wrapper">
                    <div className="connector-horizontal-arm-discovery"></div>
                    <div className={`lineage-node-discovery ${d.status.toLowerCase()}`}>
                      <span className="lineage-node-icon">🎯</span>
                      <div className="lineage-node-content">
                        <span className="lineage-node-title">Discovery: {d.title}</span>
                        <p className="lineage-node-text">{(d.observation || '').substring(0, 100)}...</p>
                        <span className="lineage-node-badge">{d.status}</span>
                      </div>
                    </div>
                  </div>

                  {childQuestionId && renderLineageTree(childQuestionId, level + 1)}
                </div>
              )
            })}
          </div>
        )}
      </div>
    )
  }

  // Renders ⑤ Research Lineage Graph tree panel
  const renderGlobalLineageGraph = () => {
    // Find all child question IDs to identify root questions
    const childQuestionIds = new Set<string>()
    allDiscoveries.forEach(d => {
      const childId = getSpawnedQuestionId(d.recommended_action)
      if (childId) {
        childQuestionIds.add(childId)
      }
    })

    const rootQuestions = questionsList.filter(q => !childQuestionIds.has(q.id))

    return (
      <section className="global-lineage-section">
        <div className="panel-header-lineage">
          <span className="lineage-header-icon">🌐</span>
          <h2>Global Research Lineage Network</h2>
          <p className="panel-desc">A visual representation of how initial research questions branched into discoveries and spawned new child inquiries.</p>
        </div>

        <div className="lineage-graph-container">
          {rootQuestions.length === 0 ? (
            <div className="lineage-empty-state">
              <p>No research questions registered to build the lineage network.</p>
            </div>
          ) : (
            <div className="lineage-forest">
              {rootQuestions.map(q => renderLineageTree(q.id))}
            </div>
          )}
        </div>
      </section>
    )
  }

  // Renders spacecraft telemetry simulator panel
  const renderTelemetryControlCenter = () => {
    const isAnomalous = telemetry.status !== 'NOMINAL'
    return (
      <div className={`telemetry-control-center ${isAnomalous ? 'alarm-active' : ''}`}>
        <div className="telemetry-header-row">
          <div className="telemetry-header-title-group">
            <span className="telemetry-satellite-icon">🛰️</span>
            <div>
              <h3>Flight Telemetry Control Center (OBC Simulator)</h3>
              <span className="telemetry-satellite-id">INSAT-4B // Telecommand Active Node</span>
            </div>
          </div>
          <div className="telemetry-status-block">
            <span className={`telemetry-status-pill ${telemetry.status.toLowerCase()}`}>
              <span className="pulsing-dot-telemetry"></span>
              {telemetry.status.replace(/_/g, ' ')}
            </span>
          </div>
        </div>

        <div className="telemetry-grid">
          {/* Thruster Temp */}
          <div className={`telemetry-card-sensor ${telemetry.thruster_temp > 75 ? 'warning' : ''} ${telemetry.thruster_temp > 100 ? 'critical' : ''}`}>
            <span className="sensor-label">Thruster Valve Temp</span>
            <div className="sensor-value-group">
              <span className="sensor-value">{telemetry.thruster_temp.toFixed(1)}°C</span>
              <span className="sensor-threshold">Max Safe: 75.0°C</span>
            </div>
            <div className="sensor-meter-track">
              <div className="sensor-meter-fill" style={{ width: `${Math.min(100, (telemetry.thruster_temp / 130) * 100)}%` }}></div>
            </div>
          </div>

          {/* Propellant Pressure */}
          <div className={`telemetry-card-sensor ${telemetry.propellant_pressure > 2.0 ? 'critical' : ''}`}>
            <span className="sensor-label">Propellant Pressure</span>
            <div className="sensor-value-group">
              <span className="sensor-value">{telemetry.propellant_pressure.toFixed(2)} MPa</span>
              <span className="sensor-threshold">Max Safe: 2.00 MPa</span>
            </div>
            <div className="sensor-meter-track">
              <div className="sensor-meter-fill" style={{ width: `${Math.min(100, (telemetry.propellant_pressure / 3.5) * 100)}%` }}></div>
            </div>
          </div>

          {/* Gyro Attitude Drift */}
          <div className={`telemetry-card-sensor ${telemetry.gyro_drift > 0.10 ? 'warning' : ''}`}>
            <span className="sensor-label">Attitude Gyro Drift</span>
            <div className="sensor-value-group">
              <span className="sensor-value">{telemetry.gyro_drift.toFixed(3)} deg/h</span>
              <span className="sensor-threshold">Max Safe: 0.100 deg/h</span>
            </div>
            <div className="sensor-meter-track">
              <div className="sensor-meter-fill" style={{ width: `${Math.min(100, (telemetry.gyro_drift / 0.3) * 100)}%` }}></div>
            </div>
          </div>

          {/* Solar Panel Current */}
          <div className="telemetry-card-sensor nominal">
            <span className="sensor-label">Solar Array Current</span>
            <div className="sensor-value-group">
              <span className="sensor-value">{telemetry.solar_current.toFixed(1)} A</span>
              <span className="sensor-threshold">Nominal: 8.5 A</span>
            </div>
            <div className="sensor-meter-track">
              <div className="sensor-meter-fill" style={{ width: `${Math.min(100, (telemetry.solar_current / 10) * 100)}%` }}></div>
            </div>
          </div>
        </div>

        <div className="telemetry-control-actions">
          {isAnomalous ? (
            <button 
              className="telemetry-btn resolve-btn"
              onClick={handleResolveTelemetryAnomaly}
              disabled={isTelemetryLoading}
            >
              ✓ Dispatch Thermal Cooling Telecommand
            </button>
          ) : (
            <button 
              className="telemetry-btn trigger-btn"
              onClick={handleTriggerTelemetryAnomaly}
              disabled={isTelemetryLoading}
            >
              ⚠️ Simulate Solar Flare & Thruster Anomaly
            </button>
          )}
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

      {/* Flight Telemetry Control Center (OBC Simulator) */}
      {renderTelemetryControlCenter()}

      {/* ① Full-Width Hero Panel */}
      <section className="hero-panel">
        <div className="hero-content">
          <h2>Autonomous Scientific Research Engine</h2>
          <p className="hero-desc">Formulate a scientific question or target. DREAMNET will automatically structure competing hypotheses, design specs, run isolated sandboxed execution trials, evaluate quantitative metrics, and scan for emergent discoveries.</p>
        </div>
        <form onSubmit={handleSubmit} className="question-form-hero">
          <div className="form-group-hero">
            <textarea
              id="research-question"
              rows={3}
              placeholder="e.g., Can quantization parameter INT8 scaling reduce model latency by >=20% without dropping accuracy by >1.5%?"
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              disabled={dbStatus !== 'connected'}
            />
          </div>
          <button
            type="submit"
            className="submit-btn-hero"
            disabled={isSubmitting || !questionText.trim() || dbStatus !== 'connected'}
          >
            {isSubmitting ? 'Initializing Agent Loop...' : '🚀 Launch Autonomous Research Loop'}
          </button>
        </form>

        {message && (
          <div className={`notification ${message.startsWith('Error') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}

        {dbStatus !== 'connected' && (
          <div className="setup-alert-hero">
            <span>⚠️ Database offline or authentication failed. Check credentials in <code>backend/.env</code></span>
            {dbError && <p className="db-error-desc" style={{ marginTop: '0.5rem', opacity: 0.8, fontSize: '0.8rem' }}>{dbError}</p>}
          </div>
        )}
      </section>

      {/* Main Workspace Layout */}
      <div className="workspace-container">
        {/* Left Column: sidebar list of questions */}
        <aside className="workspace-sidebar">
          <div className="sidebar-header">
            <h3>Registered Questions ({questionsList.length})</h3>
          </div>
          <div className="sidebar-feed">
            {questionsList.length === 0 ? (
              <div className="sidebar-empty">
                <p>No questions registered.</p>
              </div>
            ) : (
              questionsList.map(q => (
                <div 
                  key={q.id} 
                  className={`sidebar-card ${expandedQuestionId === q.id ? 'active' : ''}`}
                  onClick={() => handleToggleExpand(q.id)}
                >
                  <div className="sidebar-card-top">
                    <span className="sidebar-card-id">ID: {q.id.substring(0, 8)}</span>
                    <span className={`status-pill ${q.status}`}>{q.status}</span>
                  </div>
                  <p className="sidebar-card-text">{q.text}</p>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* Right Column: Active Research Workspace detail panel */}
        <main className="workspace-detail">
          {expandedQuestionId ? (
            <div className="active-workspace-panel">
              {/* Selected question text banner */}
              <div className="active-question-banner">
                <span className="banner-label">Active Scientific inquiry</span>
                <h2>{questionsList.find(q => q.id === expandedQuestionId)?.text}</h2>
              </div>

              {/* ② Research Pipeline Stepper Progress */}
              {renderPipelineStepper(expandedQuestionId)}

              {/* Loop Controls */}
              {renderControlRoom(expandedQuestionId)}

              {/* ③ Hypotheses Grid */}
              <div className="hypotheses-pipeline-block">
                <div className="pipeline-block-header">
                  <h3>🧬 Competing Hypotheses Pipeline</h3>
                  <button
                    className="regenerate-btn"
                    onClick={(e) => handleRegenerateHypotheses(e, expandedQuestionId)}
                    disabled={regeneratingMap[expandedQuestionId] || (sessionsMap[expandedQuestionId] && sessionsMap[expandedQuestionId].status === 'RUNNING')}
                  >
                    {regeneratingMap[expandedQuestionId] ? 'Resetting...' : '🔄 Reset Pipeline'}
                  </button>
                </div>

                {loadingHypotheses[expandedQuestionId] ? (
                  <div className="shimmer-wrapper">
                    {[1, 2].map((i) => (
                      <div className="shimmer-card" key={i}>
                        <div className="shimmer-line title"></div>
                        <div className="shimmer-line body-1"></div>
                      </div>
                    ))}
                  </div>
                ) : !hypothesesMap[expandedQuestionId] || hypothesesMap[expandedQuestionId].length === 0 ? (
                  <div className="empty-state">
                    <p>No hypotheses in this loop yet. Start loop or click reset.</p>
                  </div>
                ) : (
                  <div className="hypotheses-grid">
                    {hypothesesMap[expandedQuestionId].map((h, idx) => {
                      const isCollapsed = hypothesesCollapsed[h.id] !== false
                      return (
                        <div 
                          key={h.id} 
                          className={`hypothesis-card ${h.status.toLowerCase()} ${isCollapsed ? 'collapsed' : 'expanded'}`}
                          onClick={() => toggleHypothesisCollapse(h.id)}
                        >
                          <div className="hypothesis-card-header">
                            <div className="hypothesis-header-left">
                              <span className="hypothesis-tag">H{idx + 1}</span>
                              <span className={`badge-status ${h.status.toLowerCase()}`}>{h.status}</span>
                            </div>
                            <div className="hypothesis-header-right">
                              <div className="confidence-meter-mini">
                                <span className="confidence-meter-label">Confidence:</span>
                                <span className="confidence-meter-value">{(h.confidence * 100).toFixed(0)}%</span>
                              </div>
                              <span className="toggle-chevron">{isCollapsed ? '▼' : '▲'}</span>
                            </div>
                          </div>

                          <div className="hypothesis-statement-block">
                            <p className="hypothesis-statement">{h.statement}</p>
                          </div>

                          {!isCollapsed && (
                            <div className="hypothesis-expanded-content" onClick={(e) => e.stopPropagation()}>
                              <div className="expanded-details-grid">
                                <p className="hypothesis-rationale">
                                  <strong>Rationale:</strong> {h.rationale}
                                </p>
                                <p className="hypothesis-rationale">
                                  <strong>Predicted Outcome:</strong> {h.predicted_outcome}
                                </p>
                              </div>

                              <div className="hypothesis-details-grid" style={{ marginTop: '1rem' }}>
                                <div className="details-block">
                                  <span className="details-label">Boundary Assumptions</span>
                                  <ul className="details-list">
                                    {h.assumptions?.map((item, key) => (
                                      <li className="details-tag" key={key}>{item}</li>
                                    )) || <span className="details-tag">None</span>}
                                  </ul>
                                </div>
                                <div className="details-block">
                                  <span className="details-label">Key Variables</span>
                                  <ul className="details-list">
                                    {h.variables?.map((item, key) => (
                                      <li className="details-tag" key={key}>{item}</li>
                                    )) || <span className="details-tag">None</span>}
                                  </ul>
                                </div>
                              </div>

                              {/* Peer Review Council Dialogue Swarm */}
                              {h.peer_review && h.peer_review.length > 0 && (
                                <div className="peer-review-dialogue-box" style={{ marginTop: '1.2rem' }}>
                                  <span className="details-label" style={{ color: 'var(--accent-purple)' }}>🔬 Scientific Council Peer Review Dialogue</span>
                                  <div className="peer-review-chat-container">
                                    {h.peer_review.map((msg: any, mIdx: number) => (
                                      <div className="chat-bubble-row" key={mIdx}>
                                        <div className="chat-bubble-avatar">{msg.avatar || '👤'}</div>
                                        <div className="chat-bubble-content-block">
                                          <span className="chat-bubble-sender">{msg.sender}</span>
                                          <p className="chat-bubble-message">{msg.message}</p>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Experiment Specification details block */}
                              {renderExperimentSpec(h)}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* ④ Discovery / Unexpected Observation Panel */}
              {renderDiscoveryPanel(expandedQuestionId)}
            </div>
          ) : (
            <div className="no-question-selected-panel">
              <div className="brain-animation-container">🧠</div>
              <h2>DREAMNET Loop Engine Standby</h2>
              <p>Select a registered inquiry from the left sidebar panel or launch a new research question at the top to initiate autonomous discovery execution pipelines.</p>
            </div>
          )}
        </main>
      </div>

      {/* ⑤ Research Lineage Graph */}
      {renderGlobalLineageGraph()}
      {Object.keys(loadingResults).length > 0 && <span style={{display: 'none'}} />}
    </div>
  )
}

export default App

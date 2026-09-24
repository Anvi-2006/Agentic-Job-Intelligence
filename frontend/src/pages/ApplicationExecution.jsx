import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  Circle,
  ExternalLink,
  FileCheck2,
  Loader2,
  Play,
  ShieldCheck,
  UserRound,
} from 'lucide-react'

import {
  approveApplicationSubmission,
  createApplicationExecution,
  executeApplicationBrowser,
  getApplicationExecution,
  getExecutionEvents,
  requestSubmissionApproval,
  resumeApplicationExecution,
  startApplicationExecution,
  markApplicationSubmitted,
} from '../services/api'

const STATUS_LABELS = {
  ready: 'Ready',
  executing: 'Executing',
  needs_human: 'Needs your attention',
  submitted: 'Submitted',
  failed: 'Failed',
}

const EVENT_LABELS = {
  EXECUTION_STARTED: 'Execution started',
  EXECUTION_RESUMED: 'Execution resumed',
  BROWSER_ACTION_EXECUTED: 'Browser action completed',
  BROWSER_FIELDS_COMPLETED: 'Application fields completed',
  BROWSER_HUMAN_INTERVENTION_REQUIRED:
    'Human intervention required',
  SUBMISSION_APPROVAL_REQUIRED:
    'Submission approval required',
  SUBMISSION_APPROVED: 'Submission approved',
  APPLICATION_SUBMITTED: 'Application submitted',
}

function formatDate(value) {
  if (!value) return ''

  return new Date(value).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function getStatusClass(status) {
  return `execution-status execution-status-${status}`
}

function ApplicationExecution() {
  const { applicationId } = useParams()

  const [execution, setExecution] = useState(null)
  const [events, setEvents] = useState([])
  const [applicationUrl, setApplicationUrl] = useState('')
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [browserMessage, setBrowserMessage] = useState('')

  const loadExecution = useCallback(async () => {
    try {
        setError('')

        const [executionData, eventsData] = await Promise.all([
        getApplicationExecution(applicationId),
        getExecutionEvents(applicationId),
        ])

        setExecution(executionData)
        setEvents(eventsData)
    } catch (requestError) {
        setError(
        requestError.response?.data?.detail ||
            'Unable to load application execution.',
        )
    } finally {
        setLoading(false)
    }
    }, [applicationId])

  useEffect(() => {
    let cancelled = false

    async function load() {
        try {
        setError('')

        const [executionData, eventsData] =
            await Promise.all([
            getApplicationExecution(applicationId),
            getExecutionEvents(applicationId),
            ])

        if (cancelled) return

        setExecution(executionData)
        setEvents(eventsData)
        } catch (requestError) {
        if (cancelled) return

        setError(
            requestError.response?.data?.detail ||
            'Unable to load application execution.',
        )
        } finally {
        if (!cancelled) {
            setLoading(false)
        }
        }
    }

    load()

    return () => {
        cancelled = true
    }
    }, [applicationId])

  async function handleCreateExecution() {
    try {
      setWorking(true)
      setError('')

      const data = await createApplicationExecution(applicationId)

      setExecution(data)
      await loadExecution()
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          'Unable to create application execution.',
      )
    } finally {
      setWorking(false)
    }
  }

  async function handleStartExecution() {
    try {
      setWorking(true)
      setError('')

      const data = await startApplicationExecution(applicationId)

      setExecution(data)
      await loadExecution()
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          'Unable to start application execution.',
      )
    } finally {
      setWorking(false)
    }
  }

  async function handleBrowserExecution() {
    if (!applicationUrl.trim()) {
      setError('Enter the application page URL first.')
      return
    }

    try {
      setWorking(true)
      setError('')
      setBrowserMessage('Opening the application and completing supported fields…')

      await executeApplicationBrowser(
        applicationId,
        applicationUrl.trim(),
        true,
      )

      await loadExecution()
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          'Browser execution could not be completed.',
      )
    } finally {
      setWorking(false)
      setBrowserMessage('')
    }
  }

  async function handleResume() {
    try {
      setWorking(true)
      setError('')

      await resumeApplicationExecution(applicationId)
      await loadExecution()
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          'Unable to resume execution.',
      )
    } finally {
      setWorking(false)
    }
  }

  async function handleRequestSubmissionApproval() {
    try {
      setWorking(true)
      setError('')

      await requestSubmissionApproval(applicationId)
      await loadExecution()
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          'Unable to request submission approval.',
      )
    } finally {
      setWorking(false)
    }
  }

  async function handleApproveSubmission() {
    try {
      setWorking(true)
      setError('')

      await approveApplicationSubmission(applicationId)
      await loadExecution()
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          'Unable to approve application submission.',
      )
    } finally {
      setWorking(false)
    }
  }

  async function handleMarkSubmitted() {
  try {
    setWorking(true)
    setError('')

    await markApplicationSubmitted(applicationId)
    await loadExecution()
  } catch (err) {
    setError(
      err.response?.data?.detail ||
        'Unable to mark the application as submitted.',
    )
  } finally {
    setWorking(false)
  }
}

  const completedEvents = useMemo(
    () =>
      events.filter(
        (event) =>
          event.success !== false,
      ),
    [events],
  )

  if (loading) {
    return (
      <div className="execution-page">
        <div className="execution-loading panel">
          <Loader2 size={22} className="spin" />
          <span>Loading application execution…</span>
        </div>
      </div>
    )
  }

  if (!execution) {
    return (
      <div className="execution-page">
        <div className="execution-header">
          <Link
            to="/applications"
            className="back-link"
          >
            <ChevronLeft size={17} />
            Applications
          </Link>
        </div>

        <div className="panel execution-empty">
          <FileCheck2 size={34} />
          <h2>Application execution is not ready</h2>
          <p>
            Create an execution session for this approved
            application to begin.
          </p>

          <button
            className="primary-button"
            onClick={handleCreateExecution}
            disabled={working}
          >
            {working ? (
              <>
                <Loader2 size={16} className="spin" />
                Creating…
              </>
            ) : (
              <>
                <Play size={16} />
                Create execution
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="execution-error">
            <AlertCircle size={18} />
            {error}
          </div>
        )}
      </div>
    )
  }

  const status = execution.status
  const needsHuman =
    status === 'needs_human'

  const submissionApprovalRequired =
    needsHuman &&
    execution.current_action ===
      'submission_approval_required'

  const browserInterventionRequired =
    needsHuman &&
    execution.current_action ===
      'browser_human_intervention'

  const fieldsCompleted =
    execution.current_action ===
      'browser_fields_completed' ||
    completedEvents.some(
      (event) =>
        event.event_type ===
        'BROWSER_FIELDS_COMPLETED',
    )

  return (
    <div className="execution-page">
      <div className="execution-header">
        <Link
          to="/applications"
          className="back-link"
        >
          <ChevronLeft size={17} />
          Applications
        </Link>

        <div>
          <div className="eyebrow">
            Application execution
          </div>
          <h1>Apply on your behalf</h1>
          <p>
            ApplyIQ can complete supported application
            fields, but submission always remains under
            your control.
          </p>
        </div>

        <div className={getStatusClass(status)}>
          {status === 'executing' && (
            <Loader2 size={15} className="spin" />
          )}
          {status === 'submitted' && (
            <CheckCircle2 size={15} />
          )}
          {status === 'needs_human' && (
            <UserRound size={15} />
          )}
          {STATUS_LABELS[status] || status}
        </div>
      </div>

      {error && (
        <div className="execution-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {browserMessage && (
        <div className="execution-info">
          <Loader2 size={17} className="spin" />
          {browserMessage}
        </div>
      )}

      <div className="execution-layout">
        <main>
          <section className="panel execution-hero">
            <div className="execution-hero-icon">
              <ShieldCheck size={25} />
            </div>

            <div>
              <span className="section-kicker">
                Human-controlled automation
              </span>
              <h2>
                Your application stays under your control
              </h2>
              <p>
                The browser agent can open the application,
                fill supported fields, and upload your
                application materials. It cannot submit
                the application by itself.
              </p>
            </div>
          </section>

          {status === 'ready' && (
            <section className="panel execution-action-card">
              <div>
                <span className="section-kicker">
                  Step 1
                </span>
                <h2>Start execution</h2>
                <p>
                  Start the approved application execution
                  session.
                </p>
              </div>

              <button
                className="primary-button"
                onClick={handleStartExecution}
                disabled={working}
              >
                {working ? (
                  <>
                    <Loader2
                      size={16}
                      className="spin"
                    />
                    Starting…
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    Start execution
                  </>
                )}
              </button>
            </section>
          )}

          {status === 'executing' && (
            <section className="panel execution-action-card">
              <div>
                <span className="section-kicker">
                  Browser execution
                </span>
                <h2>Open the application</h2>
                <p>
                  Provide the application page URL. ApplyIQ
                  will inspect the page and complete the
                  supported fields.
                </p>
              </div>

              <div className="execution-url-form">
                <label htmlFor="application-url">
                  Application page URL
                </label>

                <div className="execution-url-row">
                  <input
                    id="application-url"
                    type="url"
                    value={applicationUrl}
                    onChange={(event) =>
                      setApplicationUrl(
                        event.target.value,
                      )
                    }
                    placeholder="https://company.com/careers/apply/..."
                  />

                  <button
                    className="primary-button"
                    onClick={handleBrowserExecution}
                    disabled={working}
                  >
                    {working ? (
                      <>
                        <Loader2
                          size={16}
                          className="spin"
                        />
                        Running…
                      </>
                    ) : (
                      <>
                        <ExternalLink size={16} />
                        Run browser agent
                      </>
                    )}
                  </button>
                </div>
              </div>
            </section>
          )}

          {browserInterventionRequired && (
            <section className="panel execution-human-card">
              <div className="human-card-icon">
                <UserRound size={21} />
              </div>

              <div className="human-card-content">
                <span className="section-kicker">
                  Human intervention
                </span>

                <h2>
                  The browser agent needs your help
                </h2>

                <p>
                  ApplyIQ could not continue automatically.
                  Resolve the issue on the application page,
                  then provide the page URL again so execution
                  can continue.
                </p>

                <label htmlFor="human-application-url">
                  Application page URL
                </label>

                <div className="execution-url-row">
                  <input
                    id="human-application-url"
                    type="url"
                    value={applicationUrl}
                    onChange={(event) =>
                      setApplicationUrl(
                        event.target.value,
                      )
                    }
                    placeholder="https://company.com/careers/apply/..."
                  />

                  <button
                    className="primary-button"
                    onClick={handleResume}
                    disabled={working}
                  >
                    {working ? (
                      <>
                        <Loader2
                          size={16}
                          className="spin"
                        />
                        Resuming…
                      </>
                    ) : (
                      'Resume execution'
                    )}
                  </button>
                </div>
              </div>
            </section>
          )}

          {submissionApprovalRequired && (
            <section className="panel execution-approval-card">
              <div className="approval-card-icon">
                <ShieldCheck size={23} />
              </div>

              <div>
                <span className="section-kicker">
                  Final human approval
                </span>

                <h2>
                  Review before submission
                </h2>

                <p>
                  The supported application fields are
                  complete. ApplyIQ will not submit until
                  you explicitly approve the submission.
                </p>

                <div className="approval-actions">
                  <button
                    className="primary-button"
                    onClick={handleApproveSubmission}
                    disabled={working}
                  >
                    {working ? (
                      <>
                        <Loader2
                          size={16}
                          className="spin"
                        />
                        Approving…
                      </>
                    ) : (
                      <>
                        <ShieldCheck size={16} />
                        Approve submission
                      </>
                    )}
                  </button>
                </div>
              </div>
            </section>
          )}

          {execution.submission_approved &&
            status === 'executing' && (
                <section className="panel execution-action-card">
                <div>
                    <span className="section-kicker">
                    Submission approved
                    </span>

                    <h2>
                    Ready for final submission
                    </h2>

                    <p>
                    Your application is approved for submission.
                    Submit it on the employer's application page,
                    then confirm below so ApplyIQ can record the
                    application as submitted.
                    </p>
                </div>

                <button
                    className="primary-button"
                    onClick={handleMarkSubmitted}
                    disabled={working}
                >
                    {working ? (
                    <>
                        <Loader2
                        size={16}
                        className="spin"
                        />
                        Recordingâ€¦
                    </>
                    ) : (
                    <>
                        <CheckCircle2 size={16} />
                        I submitted the application
                    </>
                    )}
                </button>
                </section>
            )}

          {status === 'executing' &&
            fieldsCompleted &&
            !execution.submission_approved && (
              <section className="panel execution-action-card">
                <div>
                  <span className="section-kicker">
                    Browser step complete
                  </span>

                  <h2>
                    Application fields are complete
                  </h2>

                  <p>
                    Review the application in the browser.
                    When you are ready, request the final
                    human submission approval.
                  </p>
                </div>

                <button
                  className="primary-button"
                  onClick={
                    handleRequestSubmissionApproval
                  }
                  disabled={working}
                >
                  {working ? (
                    <>
                      <Loader2
                        size={16}
                        className="spin"
                      />
                      Requesting…
                    </>
                  ) : (
                    <>
                      <ShieldCheck size={16} />
                      Request submission approval
                    </>
                  )}
                </button>
              </section>
            )}

          {status === 'submitted' && (
            <section className="panel execution-success-card">
              <CheckCircle2 size={30} />

              <div>
                <span className="section-kicker">
                  Completed
                </span>
                <h2>Application submitted</h2>
                <p>
                  The execution workflow has been completed
                  and the application is marked as submitted.
                </p>
              </div>
            </section>
          )}

          <section className="panel execution-timeline-card">
            <div className="section-heading">
              <div>
                <span className="section-kicker">
                  Execution history
                </span>
                <h2>Activity timeline</h2>
              </div>

              <span className="timeline-count">
                {events.length} events
              </span>
            </div>

            {events.length === 0 ? (
              <div className="timeline-empty">
                <Circle size={18} />
                No execution events yet.
              </div>
            ) : (
              <div className="execution-timeline">
                {events.map((event) => (
                  <div
                    className="timeline-item"
                    key={event.event_id}
                  >
                    <div className="timeline-marker">
                      {event.success === false ? (
                        <AlertCircle size={16} />
                      ) : (
                        <CheckCircle2 size={16} />
                      )}
                    </div>

                    <div className="timeline-content">
                      <div className="timeline-topline">
                        <strong>
                          {EVENT_LABELS[
                            event.event_type
                          ] ||
                            event.event_type}
                        </strong>

                        <span>
                          {formatDate(
                            event.created_at,
                          )}
                        </span>
                      </div>

                      <p>{event.details}</p>

                      {event.action && (
                        <span className="timeline-action">
                          {event.action}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </main>

        <aside>
          <section className="panel execution-progress-card">
            <div className="section-heading">
              <div>
                <span className="section-kicker">
                  Progress
                </span>
                <h2>Application workflow</h2>
              </div>
            </div>

            <div className="execution-progress">
              <ProgressStep
                label="Execution created"
                active
                complete={status !== 'ready'}
              />

              <ProgressStep
                label="Browser execution"
                active={status !== 'ready'}
                complete={fieldsCompleted}
              />

              <ProgressStep
                label="Human review"
                active={
                  needsHuman ||
                  fieldsCompleted
                }
                complete={
                  execution.submission_approved
                }
              />

              <ProgressStep
                label="Submitted"
                active={
                  execution.submission_approved ||
                  status === 'submitted'
                }
                complete={status === 'submitted'}
              />
            </div>
          </section>

          <section className="panel execution-meta-card">
            <span className="section-kicker">
              Execution details
            </span>

            <dl>
              <div>
                <dt>Status</dt>
                <dd>
                  {STATUS_LABELS[status] || status}
                </dd>
              </div>

              <div>
                <dt>Current step</dt>
                <dd>
                  {execution.current_step}
                </dd>
              </div>

              <div>
                <dt>Current action</dt>
                <dd>
                  {execution.current_action ||
                    '—'}
                </dd>
              </div>

              <div>
                <dt>Submission approval</dt>
                <dd>
                  {execution.submission_approved
                    ? 'Approved'
                    : 'Not approved'}
                </dd>
              </div>
            </dl>
          </section>

          <Link
            to={`/review/${execution.application_id}`}
            className="secondary-button execution-review-link"
          >
            <FileCheck2 size={16} />
            View application review
          </Link>
        </aside>
      </div>
    </div>
  )
}

function ProgressStep({
  label,
  active,
  complete,
}) {
  return (
    <div
      className={`progress-step ${
        active ? 'progress-step-active' : ''
      } ${complete ? 'progress-step-complete' : ''}`}
    >
      <div className="progress-step-icon">
        {complete ? (
          <CheckCircle2 size={16} />
        ) : active ? (
          <Circle size={16} />
        ) : (
          <Circle size={14} />
        )}
      </div>

      <span>{label}</span>
    </div>
  )
}

export default ApplicationExecution
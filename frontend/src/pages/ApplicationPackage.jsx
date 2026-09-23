import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  FileText,
  LoaderCircle,
  Sparkles,
  XCircle,
} from 'lucide-react'

import {
  generateApplicationPackage,
  getApplicationPackage,
} from '../services/api'

function ApplicationPackage() {
  const { jobId } = useParams()
  const navigate = useNavigate()

  const [packageData, setPackageData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadExistingPackage() {
      try {
        setLoading(true)
        setError('')

        const data = await getApplicationPackage(jobId)

        if (!cancelled) {
          setPackageData(data)
        }
      } catch (err) {
        if (!cancelled) {
          // 404 simply means this package has not been generated yet.
          if (err.response?.status !== 404) {
            setError(
              err.response?.data?.detail ||
                'Unable to load the application package.',
            )
          }
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadExistingPackage()

    return () => {
      cancelled = true
    }
  }, [jobId])

  async function handleGenerate() {
    try {
      setGenerating(true)
      setError('')

      const data = await generateApplicationPackage(jobId)
      setPackageData(data)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Unable to prepare the application package.',
      )
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="state-card">
        <LoaderCircle className="loading-spinner" size={24} />
        <h3>Loading application package</h3>
        <p>Checking whether this application is already prepared.</p>
      </div>
    )
  }

  if (!packageData) {
    return (
      <div className="application-package-page">
        <Link to={`/jobs/${jobId}`} className="back-link">
          <ArrowLeft size={16} />
          Back to job
        </Link>

        <section className="package-intro panel">
          <div className="package-intro-icon">
            <Sparkles size={22} />
          </div>

          <p className="eyebrow">Application intelligence</p>

          <h1>Prepare your application</h1>

          <p>
            ApplyIQ will use your verified candidate evidence and the job
            requirements to prepare a tailored application package for your
            review.
          </p>

          <button
            type="button"
            className="primary-button"
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? (
              <>
                <LoaderCircle className="loading-spinner" size={16} />
                Preparing application...
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Prepare application
              </>
            )}
          </button>

          {error && (
            <div className="package-error">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}
        </section>
      </div>
    )
  }

  return (
    <div className="application-package-page">
      <Link to={`/jobs/${jobId}`} className="back-link">
        <ArrowLeft size={16} />
        Back to job
      </Link>

      <section className="package-header">
        <div>
          <p className="eyebrow">Application package</p>
          <h1>{packageData.job_title}</h1>
          <p>{packageData.company}</p>
        </div>

        <div className="package-header-actions">
            <div className="readiness-card">
                <span>Readiness</span>
                <strong>{Math.round(packageData.readiness_score)}%</strong>
                <small>{packageData.recommendation}</small>
            </div>

            <button
                type="button"
                className="secondary-button"
                onClick={handleGenerate}
                disabled={generating}
            >
                {generating ? (
                <>
                    <LoaderCircle className="loading-spinner" size={16} />
                    Regenerating...
                </>
                ) : (
                <>
                    <Sparkles size={16} />
                    Regenerate
                </>
                )}
            </button>
            </div>
      </section>

      {!packageData.is_valid && (
        <div className="validation-warning">
          <AlertCircle size={18} />
          <div>
            <strong>This package needs attention</strong>
            <p>
              Review the validation issues before continuing with the
              application.
            </p>
          </div>
        </div>
      )}

      {packageData.is_valid && (
        <div className="validation-success">
          <CheckCircle2 size={18} />
          <span>Application package passed validation.</span>
        </div>
      )}

      <div className="package-layout">
        <main className="package-main">
          <section className="panel package-section">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Profile</p>
                <h2>Tailored summary</h2>
              </div>
              <FileText size={20} />
            </div>

            <p className="generated-text">
              {packageData.tailored_summary}
            </p>
          </section>

          <section className="panel package-section">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Application letter</p>
                <h2>Cover letter</h2>
              </div>
            </div>

            <div className="cover-letter">
              {packageData.cover_letter
                .split('\n')
                .map((paragraph, index) =>
                  paragraph.trim() ? (
                    <p key={index}>{paragraph}</p>
                  ) : (
                    <div key={index} className="letter-spacing" />
                  ),
                )}
            </div>
          </section>

          <section className="panel package-section">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Preparation</p>
                <h2>Application questions</h2>
              </div>
            </div>

            <div className="questions-list">
              {packageData.application_questions?.map(
                (item, index) => (
                  <article className="question-card" key={index}>
                    <span className="question-number">
                      {index + 1}
                    </span>

                    <div>
                      <h3>{item.question}</h3>
                      <p>{item.answer}</p>

                      {item.evidence_used?.length > 0 && (
                        <div className="evidence-tags">
                          {item.evidence_used.map((evidence) => (
                            <span key={evidence}>
                              {evidence}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </article>
                ),
              )}
            </div>
          </section>
        </main>

        <aside className="package-sidebar">
          <section className="panel package-section">
            <p className="eyebrow">Why you match</p>
            <h2>Key strengths</h2>

            <div className="strength-list">
              {packageData.key_strengths?.map((strength) => (
                <div className="strength-item" key={strength}>
                  <CheckCircle2 size={17} />
                  <span>{strength}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="panel package-section">
            <p className="eyebrow">Gaps</p>
            <h2>Needs attention</h2>

            {packageData.missing_requirements?.length ? (
              <div className="missing-list">
                {packageData.missing_requirements.map(
                  (requirement) => (
                    <div
                      className="missing-item"
                      key={requirement}
                    >
                      <XCircle size={17} />
                      <span>{requirement}</span>
                    </div>
                  ),
                )}
              </div>
            ) : (
              <p className="muted-text">
                No missing requirements identified.
              </p>
            )}
          </section>

          <section className="panel package-section">
            <p className="eyebrow">Grounding</p>
            <h2>Evidence used</h2>

            <div className="evidence-list">
              {packageData.evidence_used?.map((evidence) => (
                <span className="evidence-tag" key={evidence}>
                  {evidence}
                </span>
              ))}
            </div>
          </section>

          {packageData.unsupported_claims?.length > 0 && (
            <section className="panel package-section">
              <p className="eyebrow">Validation</p>
              <h2>Issues detected</h2>

              <div className="issue-list">
                {packageData.unsupported_claims.map((issue) => (
                  <div className="issue-item" key={issue}>
                    <AlertCircle size={16} />
                    <span>{issue}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          <button
            type="button"
            className="primary-button review-button"
            disabled={!packageData.is_valid}
            onClick={() =>
                navigate(`/review/${packageData.application_id}`)
            }
            >
            Continue to review
            </button>

          {!packageData.is_valid && (
            <p className="coming-note">
              Resolve the validation issues before continuing.
            </p>
          )}
        </aside>
      </div>
    </div>
  )
}

export default ApplicationPackage
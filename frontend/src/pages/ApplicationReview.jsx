import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  FileText,
  LoaderCircle,
  XCircle,
} from 'lucide-react'

import {
  getApplicationReview,
  reviewApplication,
} from '../services/api'

function ApplicationReview() {
  const { applicationId } = useParams()

  const [packageData, setPackageData] = useState(null)
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    async function loadReview() {
      if (!applicationId) {
        setError('Application ID is missing.')
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        setError('')

        const data = await getApplicationReview(applicationId)

        setPackageData(data)
        setNote(data.reviewer_note || '')
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            'Unable to load the application review.',
        )
      } finally {
        setLoading(false)
      }
    }

    loadReview()
  }, [applicationId])

  async function handleDecision(decision) {
    if (!packageData) {
      setError('Application review data is unavailable.')
      return
    }

    try {
      setSubmitting(true)
      setError('')
      setSuccess('')

      const result = await reviewApplication(
        packageData.candidate_id,
        packageData.job_id,
        decision,
        note,
      )

      setPackageData((current) => ({
        ...current,
        status: result.status,
        reviewer_note: result.reviewer_note,
      }))

      setSuccess(
        `Application ${result.status.replaceAll('_', ' ')} successfully.`,
      )
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Unable to update the application review.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="state-card">
        <LoaderCircle className="loading-spinner" size={24} />
        <h3>Loading application review</h3>
        <p>Preparing the application for your review.</p>
      </div>
    )
  }

  if (error && !packageData) {
    return (
      <div className="state-card error-state">
        <div className="state-icon">
          <AlertCircle size={22} />
        </div>
        <h3>Review unavailable</h3>
        <p>{error}</p>
        <Link to="/applications" className="secondary-button">
          <ArrowLeft size={15} />
          Back to applications
        </Link>
      </div>
    )
  }

  return (
    <div className="review-page">
      <Link to="/applications" className="back-link">
        <ArrowLeft size={16} />
        Back to applications
      </Link>

      <section className="review-header">
        <div>
          <p className="eyebrow">Human review</p>
          <h1>Review your application</h1>
          <p>
            Check the AI-prepared package before deciding whether it
            should proceed.
          </p>
        </div>

        <div className="review-status">
          <FileText size={18} />
          <span>Human approval required</span>
        </div>
      </section>

      {error && (
        <div className="validation-warning">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="validation-success">
          <CheckCircle2 size={18} />
          <span>{success}</span>
        </div>
      )}

      {packageData && (
        <div className="review-layout">
          <main className="review-main">
            <section className="panel review-section">
              <p className="eyebrow">Opportunity</p>
              <h2>{packageData.job_title}</h2>
              <p className="review-company">
                {packageData.company}
              </p>
            </section>

            <section className="panel review-section">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Profile</p>
                  <h2>Tailored summary</h2>
                </div>
              </div>

              <p className="generated-text">
                {packageData.tailored_summary}
              </p>
            </section>

            <section className="panel review-section">
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
                      <div
                        key={index}
                        className="letter-spacing"
                      />
                    ),
                  )}
              </div>
            </section>

            <section className="panel review-section">
              <p className="eyebrow">Preparation</p>
              <h2>Application questions</h2>

              <div className="questions-list">
                {packageData.application_questions?.map(
                  (item, index) => (
                    <article
                      className="question-card"
                      key={index}
                    >
                      <span className="question-number">
                        {index + 1}
                      </span>

                      <div>
                        <h3>{item.question}</h3>
                        <p>{item.answer}</p>
                      </div>
                    </article>
                  ),
                )}
              </div>
            </section>
          </main>

          <aside className="review-sidebar">
            <section className="panel review-section">
              <p className="eyebrow">Decision</p>
              <h2>What should happen next?</h2>

              <div className="review-current-status">
                Current status: <strong>{packageData.status}</strong>
              </div>

              {!packageData.is_valid && (
                <div className="review-blocked">
                  <XCircle size={18} />
                  <span>
                    This package failed validation and cannot be
                    approved yet.
                  </span>
                </div>
              )}

              <label className="review-note-label">
                Reviewer note
                <textarea
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                  placeholder="Add a note about your decision..."
                  rows={5}
                />
              </label>

              <div className="review-actions">
                <button
                  type="button"
                  className="primary-button"
                  disabled={
                    submitting ||
                    !packageData.is_valid ||
                    packageData.status === 'approved' ||
                    packageData.status === 'rejected'
                  }
                  onClick={() => handleDecision('APPROVED')}
                >
                  <CheckCircle2 size={17} />
                  Approve application
                </button>

                <button
                  type="button"
                  className="secondary-button"
                  disabled={
                    submitting ||
                    packageData.status === 'approved' ||
                    packageData.status === 'rejected'
                  }
                  onClick={() =>
                    handleDecision('EDIT_REQUIRED')
                  }
                >
                  <FileText size={17} />
                  Request edits
                </button>

                <button
                  type="button"
                  className="danger-button"
                  disabled={
                    submitting ||
                    packageData.status === 'approved' ||
                    packageData.status === 'rejected'
                  }
                  onClick={() =>
                    handleDecision('REJECTED')
                  }
                >
                  <XCircle size={17} />
                  Reject application
                </button>
              </div>

              {submitting && (
                <div className="review-submitting">
                  <LoaderCircle
                    className="loading-spinner"
                    size={17}
                  />
                  Updating application...
                </div>
              )}
            </section>
          </aside>
        </div>
      )}
    </div>
  )
}

export default ApplicationReview
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  ExternalLink,
  FileSearch,
  LoaderCircle,
  MapPin,
  ShieldCheck,
  Sparkles,
  XCircle,
} from 'lucide-react'

import { getJobIntelligence } from '../services/api'

function getStatusIcon(status) {
  if (status === 'matched') {
    return <CheckCircle2 size={17} />
  }

  if (status === 'partial') {
    return <Sparkles size={17} />
  }

  return <XCircle size={17} />
}

function getStatusLabel(status) {
  if (status === 'matched') {
    return 'Matched'
  }

  if (status === 'partial') {
    return 'Partial match'
  }

  return 'Missing'
}

function getStatusClass(status) {
  if (status === 'matched') {
    return 'matched'
  }

  if (status === 'partial') {
    return 'partial'
  }

  return 'missing'
}

function formatConfidence(value) {
  return `${Math.round((value || 0) * 100)}%`
}

function JobDetails() {
  const { jobId } = useParams()

  const [intelligence, setIntelligence] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadIntelligence() {
      try {
        setLoading(true)
        setError('')

        const data = await getJobIntelligence(jobId)

        if (!cancelled) {
          setIntelligence(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err.response?.data?.detail ||
              'Unable to load job intelligence.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadIntelligence()

    return () => {
      cancelled = true
    }
  }, [jobId])

  if (loading) {
    return (
      <div className="state-card">
        <LoaderCircle
          className="loading-spinner"
          size={24}
        />

        <h3>Building job intelligence</h3>

        <p>
          Analyzing the role, candidate evidence, requirements,
          and fit.
        </p>
      </div>
    )
  }

  if (error || !intelligence) {
    return (
      <div className="state-card error-state">
        <div className="state-icon">
          <AlertCircle size={22} />
        </div>

        <h3>We couldn't analyze this job</h3>

        <p>
          {error || 'This opportunity could not be analyzed.'}
        </p>

        <Link
          to="/jobs"
          className="secondary-button"
        >
          <ArrowLeft size={15} />
          Back to jobs
        </Link>
      </div>
    )
  }

  const { job, verification, fit, requirements, skill_gaps } =
    intelligence

  return (
    <div className="job-details-page">
      <Link
        to="/jobs"
        className="back-link"
      >
        <ArrowLeft size={16} />
        Back to jobs
      </Link>

      {/* -------------------------------------------------- */}
      {/* JOB HEADER                                         */}
      {/* -------------------------------------------------- */}

      <section className="job-details-header">
        <div className="company-logo large">
          {job.company?.charAt(0)?.toUpperCase() || 'J'}
        </div>

        <div className="job-details-heading">
          <p className="eyebrow">
            Job intelligence
          </p>

          <h1>{job.title}</h1>

          <div className="job-details-company">
            <strong>{job.company}</strong>

            <span>
              <MapPin size={15} />
              {job.location || 'Location not specified'}
            </span>
          </div>
        </div>

        <div className="job-header-actions">
          <span className="job-source detail-source">
            {job.source}
          </span>

          {job.job_url && (
            <a
              href={job.job_url}
              target="_blank"
              rel="noreferrer"
              className="secondary-button"
            >
              <ExternalLink size={15} />
              Original listing
            </a>
          )}
        </div>
      </section>

      {/* -------------------------------------------------- */}
      {/* INTELLIGENCE SUMMARY                               */}
      {/* -------------------------------------------------- */}

      <section className="intelligence-summary-grid">
        <div className="intelligence-score-card panel">
          <div className="score-card-top">
            <div>
              <p className="eyebrow">
                Candidate fit
              </p>

              <h2>
                {Math.round(fit.score)}%
              </h2>
            </div>

            <div className="score-icon">
              <Sparkles size={21} />
            </div>
          </div>

          <div className="score-progress">
            <div
              className="score-progress-fill"
              style={{
                width: `${Math.min(
                  Math.max(fit.score, 0),
                  100,
                )}%`,
              }}
            />
          </div>

          <div className="score-meta">
            <span>
              {fit.matched_requirements} of{' '}
              {fit.total_requirements} requirements
              directly matched
            </span>

            <strong>
              {fit.recommendation?.replaceAll('_', ' ')}
            </strong>
          </div>
        </div>

        <div className="intelligence-verification-card panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">
                Opportunity verification
              </p>

              <h3>
                {verification.verification_status}
              </h3>
            </div>

            <ShieldCheck size={21} />
          </div>

          <p>
            {verification.verification_reason}
          </p>

          <div className="verification-confidence">
            Verification confidence:{' '}
            <strong>
              {formatConfidence(
                verification.verification_confidence,
              )}
            </strong>
          </div>
        </div>
      </section>

      {/* -------------------------------------------------- */}
      {/* MAIN INTELLIGENCE GRID                             */}
      {/* -------------------------------------------------- */}

      <div className="job-intelligence-layout">
        {/* LEFT COLUMN */}

        <section className="job-intelligence-main">
          <div className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">
                  Requirement intelligence
                </p>

                <h2>
                  Why you match this role
                </h2>
              </div>

              <FileSearch size={21} />
            </div>

            <div className="intelligence-requirements">
              {requirements.map((requirement) => (
                <div
                  key={requirement.id}
                  className={`intelligence-requirement ${getStatusClass(
                    requirement.match_status,
                  )}`}
                >
                  <div className="requirement-status-icon">
                    {getStatusIcon(
                      requirement.match_status,
                    )}
                  </div>

                  <div className="requirement-content">
                    <div className="requirement-title-row">
                      <div>
                        <h3>
                          {requirement.requirement}
                        </h3>

                        <div className="requirement-tags">
                          <span>
                            {requirement.category}
                          </span>

                          <span>
                            {requirement.importance}
                          </span>
                        </div>
                      </div>

                      <div className="requirement-confidence">
                        <strong>
                          {formatConfidence(
                            requirement.confidence,
                          )}
                        </strong>

                        <span>
                          {getStatusLabel(
                            requirement.match_status,
                          )}
                        </span>
                      </div>
                    </div>

                    <p className="requirement-context">
                      {requirement.context}
                    </p>

                    <div className="requirement-reason">
                      <CircleAlert size={15} />

                      <span>
                        {requirement.reason}
                      </span>
                    </div>

                    {requirement.evidence_ids?.length >
                      0 && (
                      <div className="requirement-evidence">
                        <span className="evidence-label">
                          Supporting evidence
                        </span>

                        <span className="evidence-count">
                          {requirement.evidence_ids.length}{' '}
                          record
                          {requirement.evidence_ids.length ===
                          1
                            ? ''
                            : 's'}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ROLE DESCRIPTION */}

          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">
                  Role overview
                </p>

                <h2>
                  About this opportunity
                </h2>
              </div>
            </div>

            <p className="job-full-description">
              {job.description}
            </p>
          </section>
        </section>

        {/* RIGHT COLUMN */}

        <aside className="job-intelligence-sidebar">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">
                  Skill gaps
                </p>

                <h2>
                  Areas to strengthen
                </h2>
              </div>

              <CircleAlert size={20} />
            </div>

            {skill_gaps.length > 0 ? (
              <div className="skill-gap-list">
                {skill_gaps.map((gap) => (
                  <div
                    key={`${gap.requirement}-${gap.status}`}
                    className={`skill-gap-item ${gap.status}`}
                  >
                    <div>
                      {gap.status === 'partial' ? (
                        <Sparkles size={16} />
                      ) : (
                        <XCircle size={16} />
                      )}
                    </div>

                    <div>
                      <strong>
                        {gap.requirement}
                      </strong>

                      <span>
                        {gap.status === 'partial'
                          ? 'Partial supporting evidence'
                          : 'No supporting evidence'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-intelligence-state">
                <CheckCircle2 size={20} />

                <strong>
                  No identified skill gaps
                </strong>

                <span>
                  Your current evidence covers the
                  analyzed requirements.
                </span>
              </div>
            )}
          </section>

          {/* SCORE BREAKDOWN */}

          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">
                  Fit analysis
                </p>

                <h2>
                  Score breakdown
                </h2>
              </div>
            </div>

            <div className="score-breakdown-list">
              <div>
                <span>
                  Matched requirement weight
                </span>

                <strong>
                  {fit.matched_weight}
                </strong>
              </div>

              <div>
                <span>
                  Total requirement weight
                </span>

                <strong>
                  {fit.total_weight}
                </strong>
              </div>

              <div>
                <span>
                  Direct matches
                </span>

                <strong>
                  {fit.matched_requirements}
                </strong>
              </div>

              <div>
                <span>
                  Partial matches
                </span>

                <strong>
                  {fit.partial_requirements?.length || 0}
                </strong>
              </div>

              <div>
                <span>
                  Missing requirements
                </span>

                <strong>
                  {fit.missing_requirements?.length || 0}
                </strong>
              </div>
            </div>
          </section>

          {/* APPLICATION CTA */}

          <section className="application-cta panel">
            <div className="cta-icon">
              <Sparkles size={19} />
            </div>

            <p className="eyebrow">
              Next step
            </p>

            <h2>
              Prepare your application
            </h2>

            <p>
              Use your verified candidate evidence to
              generate a tailored application package.
            </p>

            <Link
              to={`/jobs/${jobId}/application`}
              className="primary-button fit-button"
            >
              <Sparkles size={16} />
              Prepare application
            </Link>
          </section>
        </aside>
      </div>
    </div>
  )
}

export default JobDetails
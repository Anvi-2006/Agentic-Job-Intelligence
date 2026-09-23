import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  LoaderCircle,
  MapPin,
  Sparkles,
  XCircle,
} from 'lucide-react'

import { getJob, getJobFit } from '../services/api'

function JobDetails() {
  const { jobId } = useParams()

  const [job, setJob] = useState(null)
  const [fit, setFit] = useState(null)

  const [loadingJob, setLoadingJob] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)

  const [jobError, setJobError] = useState('')
  const [fitError, setFitError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadJob() {
      try {
        setLoadingJob(true)
        setJobError('')

        const data = await getJob(jobId)

        if (!cancelled) {
          setJob(data)
        }
      } catch (err) {
        if (!cancelled) {
          setJobError(
            err.response?.data?.detail ||
              'Unable to load this job.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoadingJob(false)
        }
      }
    }

    loadJob()

    return () => {
      cancelled = true
    }
  }, [jobId])

  async function handleAnalyzeFit() {
    try {
      setAnalyzing(true)
      setFitError('')

      const data = await getJobFit(jobId)
      setFit(data)
    } catch (err) {
      setFitError(
        err.response?.data?.detail ||
          'Unable to analyze your fit for this role.',
      )
    } finally {
      setAnalyzing(false)
    }
  }

  if (loadingJob) {
    return (
      <div className="state-card">
        <LoaderCircle className="loading-spinner" size={24} />
        <h3>Loading job details</h3>
        <p>Getting the opportunity from your job workspace.</p>
      </div>
    )
  }

  if (jobError || !job) {
    return (
      <div className="state-card error-state">
        <div className="state-icon">
          <AlertCircle size={22} />
        </div>

        <h3>We couldn't load this job</h3>
        <p>{jobError || 'This opportunity could not be found.'}</p>

        <Link to="/jobs" className="secondary-button">
          <ArrowLeft size={15} />
          Back to jobs
        </Link>
      </div>
    )
  }

  return (
    <div className="job-details-page">
      <Link to="/jobs" className="back-link">
        <ArrowLeft size={16} />
        Back to jobs
      </Link>

      <section className="job-details-header">
        <div className="company-logo large">
          {job.company?.charAt(0)?.toUpperCase() || 'J'}
        </div>

        <div className="job-details-heading">
          <p className="eyebrow">Job opportunity</p>

          <h1>{job.title}</h1>

          <div className="job-details-company">
            <strong>{job.company}</strong>

            <span>
              <MapPin size={15} />
              {job.location || 'Location not specified'}
            </span>
          </div>
        </div>

        {job.source && (
          <span className="job-source detail-source">
            {job.source}
          </span>
        )}
      </section>

      <div className="job-details-layout">
        <section className="job-description-panel panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Role overview</p>
              <h2>About this opportunity</h2>
            </div>
          </div>

          <p className="job-full-description">
            {job.description}
          </p>

          {job.job_url && (
            <a
              href={job.job_url}
              target="_blank"
              rel="noreferrer"
              className="secondary-button external-job-link"
            >
              Open original listing
            </a>
          )}
        </section>

        <aside className="fit-panel panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Candidate fit</p>
              <h2>How well do you match?</h2>
            </div>

            <Sparkles size={20} />
          </div>

          {!fit && !analyzing && (
            <>
              <p className="fit-intro">
                Compare this role with your current skills and
                candidate evidence.
              </p>

              <button
                type="button"
                className="primary-button fit-button"
                onClick={handleAnalyzeFit}
              >
                <Sparkles size={16} />
                Analyze my fit
              </button>
            </>
          )}

          {analyzing && (
            <div className="fit-loading">
              <LoaderCircle
                className="loading-spinner"
                size={24}
              />

              <strong>Analyzing your fit</strong>

              <span>
                Comparing your profile with the role requirements.
              </span>
            </div>
          )}

          {fitError && !analyzing && (
            <div className="fit-error">
              <AlertCircle size={18} />
              <span>{fitError}</span>
            </div>
          )}

          {fit && (
            <div className="fit-results">
              <div className="fit-score">
                <div>
                  <span className="fit-score-label">
                    Fit score
                  </span>

                  <strong>{Math.round(fit.score)}%</strong>
                </div>

                <span className="fit-match-count">
                  {fit.matched_requirements} /{' '}
                  {fit.total_requirements} matched
                </span>
              </div>

              <div className="fit-section">
                <h3>
                  <CheckCircle2 size={17} />
                  Matched requirements
                </h3>

                {fit.matches?.filter(
                    (match) => match.match_status === 'matched',
                    ).length > 0 ? (
                    <div className="requirement-list">
                        {fit.matches
                        .filter((match) => match.match_status === 'matched')
                        .map((match, index) => (
                            <div
                            key={`${match.requirement}-${index}`}
                            className="requirement-item matched"
                            >
                            <CheckCircle2 size={16} />
                            <span>{match.requirement}</span>
                            </div>
                        ))}
                    </div>
                    ) : (
                    <p className="muted-text">
                        No direct matches found.
                    </p>
                    )}
              </div>

              {fit.partial_requirements?.length > 0 && (
                <div className="fit-section">
                  <h3>
                    <Sparkles size={17} />
                    Partial matches
                  </h3>

                  <div className="requirement-list">
                    {fit.partial_requirements.map(
                      (requirement) => (
                        <div
                          key={requirement}
                          className="requirement-item partial"
                        >
                          <Sparkles size={16} />
                          <span>{requirement}</span>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}

              {fit.missing_requirements?.length > 0 && (
                <div className="fit-section">
                  <h3>
                    <XCircle size={17} />
                    Needs attention
                  </h3>

                  <div className="requirement-list">
                    {fit.missing_requirements.map(
                      (requirement) => (
                        <div
                          key={requirement}
                          className="requirement-item missing"
                        >
                          <XCircle size={16} />
                          <span>{requirement}</span>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}

            <Link
                to={`/jobs/${jobId}/application`}
                className="primary-button fit-button"
            >
                <Sparkles size={16} />
                Prepare application
            </Link>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}

export default JobDetails
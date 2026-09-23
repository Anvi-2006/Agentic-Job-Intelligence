import { ArrowUpRight, Building2, MapPin } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function JobCard({ job }) {
  const navigate = useNavigate()

  function handleViewJob() {
    navigate(`/jobs/${job.id}`)
  }

  const score = job.fit_score
  const recommendation = job.recommendation?.replace('_', ' ')

  return (
    <article className="job-card">
      <div className="job-card-main">
        <div className="company-logo">
          {job.company?.charAt(0)?.toUpperCase() || 'J'}
        </div>

        <div className="job-card-content">
          <div className="job-card-heading">
            <div>
              <h3>{job.title}</h3>

              <div className="job-company">
                <Building2 size={14} />
                {job.company}
              </div>
            </div>

            <span className="job-source">
              {job.source || 'Job source'}
            </span>
          </div>

          <div className="job-meta">
            <span>
              <MapPin size={14} />
              {job.location || 'Location not specified'}
            </span>
          </div>

          <p className="job-description">
            {job.description
              ? `${job.description.slice(0, 180)}${
                  job.description.length > 180 ? '...' : ''
                }`
              : 'No description available.'}
          </p>

          {score !== undefined && (
            <div className="job-intelligence">
              <div className="fit-score">
                <strong>{Math.round(score)}%</strong>
                <span>fit</span>
              </div>

              <span className="recommendation">
                {recommendation}
              </span>

              <span className="requirements-summary">
                {job.matched_requirements} direct
              </span>

              <span className="requirements-summary">
                {job.partial_requirements?.length || 0} partial
              </span>

              <span className="requirements-summary">
                {job.missing_requirements?.length || 0} missing
              </span>
            </div>
          )}

          {job.recommendation_reason && (
            <p className="recommendation-reason">
              {job.recommendation_reason}
            </p>
          )}

          {job.verification_status && (
            <div className="job-verification">
              <span className="verification-status">
                {job.verification_status === 'VERIFIED_SOURCE'
                  ? '✓ Verified source'
                  : job.verification_status === 'OFFICIAL_SOURCE'
                    ? '✓ Official source'
                    : job.verification_status === 'LINK_REACHABLE'
                      ? '✓ Link reachable'
                      : '⚠ Unverified'}
              </span>

              <span className="verification-confidence">
                {Math.round(job.verification_confidence)}% confidence
              </span>
            </div>
          )}

          {(job.missing_requirements?.length > 0 ||
            job.partial_requirements?.length > 0) && (
            <div className="requirement-gaps">
              {job.partial_requirements?.map((item) => (
                <span key={`partial-${item}`} className="partial-tag">
                  Partial: {item}
                </span>
              ))}

              {job.missing_requirements?.map((item) => (
                <span key={`missing-${item}`} className="missing-tag">
                  Missing: {item}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="job-card-footer">
        <button
          type="button"
          className="secondary-button"
          onClick={handleViewJob}
        >
          View job
          <ArrowUpRight size={15} />
        </button>
      </div>
    </article>
  )
}

export default JobCard
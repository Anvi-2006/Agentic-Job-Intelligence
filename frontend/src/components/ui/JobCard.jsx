import {
  ArrowUpRight,
  Building2,
  ExternalLink,
  MapPin,
  ShieldCheck,
  ShieldAlert,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function JobCard({ job }) {
  const navigate = useNavigate()

  function handleViewJob() {
    navigate(`/jobs/${job.id}`)
  }

  const verificationStatus = job.verification_status

  const isVerified =
    verificationStatus === 'VERIFIED_SOURCE' ||
    verificationStatus === 'OFFICIAL_SOURCE' ||
    verificationStatus === 'LINK_REACHABLE'

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

          {verificationStatus && (
            <div className="job-verification">
              <span
                className={`verification-status ${
                  isVerified ? 'verified' : 'unverified'
                }`}
              >
                {isVerified ? (
                  <>
                    <ShieldCheck size={14} />
                    {verificationStatus === 'OFFICIAL_SOURCE'
                      ? 'Official source'
                      : verificationStatus === 'VERIFIED_SOURCE'
                        ? 'Verified source'
                        : 'Link reachable'}
                  </>
                ) : (
                  <>
                    <ShieldAlert size={14} />
                    Unverified source
                  </>
                )}
              </span>

              <span className="verification-confidence">
                {Math.round(
                  (job.verification_confidence || 0) * 100,
                )}
                % confidence
              </span>
            </div>
          )}

          {job.verification_reason && (
            <p className="verification-reason">
              {job.verification_reason}
            </p>
          )}
        </div>
      </div>

      <div className="job-card-footer">
        <button
          type="button"
          className="secondary-button"
          onClick={handleViewJob}
        >
          View intelligence
          <ArrowUpRight size={15} />
        </button>

        {job.job_url && (
          <a
            className="job-external-link"
            href={job.job_url}
            target="_blank"
            rel="noreferrer"
          >
            <ExternalLink size={14} />
            Source
          </a>
        )}
      </div>
    </article>
  )
}

export default JobCard
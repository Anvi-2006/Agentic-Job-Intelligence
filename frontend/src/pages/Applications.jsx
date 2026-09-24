import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertCircle,
  ArrowUpRight,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  FileText,
  LoaderCircle,
  Play,
  XCircle,
} from 'lucide-react'

import { getApplications } from '../services/api'

const STATUS_LABELS = {
  pending_review: 'Pending review',
  edit_required: 'Edits required',
  approved: 'Approved',
  rejected: 'Rejected',
}

function formatDate(value) {
  if (!value) {
    return '—'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return '—'
  }

  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

function getStatusIcon(status) {
  if (status === 'approved') {
    return <CheckCircle2 size={15} />
  }

  if (status === 'rejected') {
    return <XCircle size={15} />
  }

  if (status === 'edit_required') {
    return <FileText size={15} />
  }

  return <Clock3 size={15} />
}

function getStatusClass(status) {
  return `application-status status-${status}`
}

function Applications() {
  const [applications, setApplications] = useState([])
  const [totalApplications, setTotalApplications] = useState(0)
  const [activeFilter, setActiveFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadApplications() {
      try {
        setLoading(true)
        setError('')

        const data = await getApplications()

        setApplications(data.applications || [])
        setTotalApplications(data.total_applications || 0)
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            'Unable to load your applications.',
        )
      } finally {
        setLoading(false)
      }
    }

    loadApplications()
  }, [])

  const filteredApplications = useMemo(() => {
    if (activeFilter === 'all') {
      return applications
    }

    return applications.filter(
      (application) => application.status === activeFilter,
    )
  }, [applications, activeFilter])

  const statusCounts = useMemo(() => {
    return {
      all: applications.length,
      pending_review: applications.filter(
        (item) => item.status === 'pending_review',
      ).length,
      edit_required: applications.filter(
        (item) => item.status === 'edit_required',
      ).length,
      approved: applications.filter(
        (item) => item.status === 'approved',
      ).length,
      rejected: applications.filter(
        (item) => item.status === 'rejected',
      ).length,
    }
  }, [applications])

  if (loading) {
    return (
      <div className="state-card">
        <LoaderCircle className="loading-spinner" size={24} />
        <h3>Loading applications</h3>
        <p>Fetching your application activity.</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="state-card error-state">
        <div className="state-icon">
          <AlertCircle size={22} />
        </div>

        <h3>Applications unavailable</h3>
        <p>{error}</p>

        <button
          type="button"
          className="primary-button"
          onClick={() => window.location.reload()}
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="applications-page">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Application tracker</p>
          <h1>Your applications</h1>
          <p>
            Keep track of every opportunity you've prepared,
            reviewed, and approved.
          </p>
        </div>

        <Link to="/jobs" className="primary-button">
          <BriefcaseBusiness size={17} />
          Discover jobs
        </Link>
      </section>

      <section className="application-summary">
        <div className="application-summary-card">
          <span className="summary-label">Total applications</span>
          <strong>{totalApplications}</strong>
        </div>

        <div className="application-summary-card">
          <span className="summary-label">Pending review</span>
          <strong>{statusCounts.pending_review}</strong>
        </div>

        <div className="application-summary-card">
          <span className="summary-label">Approved</span>
          <strong>{statusCounts.approved}</strong>
        </div>
      </section>

      <section className="applications-panel">
        <div className="applications-toolbar">
          <div>
            <h2>Application activity</h2>
            <p>
              {filteredApplications.length}{' '}
              {filteredApplications.length === 1
                ? 'application'
                : 'applications'}
            </p>
          </div>

          <div className="application-filters">
            {[
              ['all', 'All'],
              ['pending_review', 'Pending'],
              ['edit_required', 'Edits required'],
              ['approved', 'Approved'],
              ['rejected', 'Rejected'],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={
                  activeFilter === value
                    ? 'filter-button active'
                    : 'filter-button'
                }
                onClick={() => setActiveFilter(value)}
              >
                {label}
                <span>{statusCounts[value]}</span>
              </button>
            ))}
          </div>
        </div>

        {filteredApplications.length === 0 ? (
          <div className="applications-empty">
            <div className="empty-icon">
              <BriefcaseBusiness size={22} />
            </div>

            <h3>
              {applications.length === 0
                ? 'No applications yet'
                : 'No applications in this category'}
            </h3>

            <p>
              {applications.length === 0
                ? 'Find a relevant opportunity and prepare your first application package.'
                : 'Try another status filter to see more applications.'}
            </p>

            {applications.length === 0 && (
              <Link to="/jobs" className="secondary-button">
                Discover jobs
                <ArrowUpRight size={15} />
              </Link>
            )}
          </div>
        ) : (
          <div className="applications-list">
            {filteredApplications.map((application) => (
              <article
                className="application-row"
                key={application.application_id}
              >
                <div className="application-company">
                  <div className="company-mark">
                    {application.company?.charAt(0)?.toUpperCase() ||
                      'C'}
                  </div>

                  <div>
                    <h3>{application.job_title}</h3>
                    <p>
                      {application.company}
                      {application.location
                        ? ` · ${application.location}`
                        : ''}
                    </p>
                  </div>
                </div>

                <div className="application-fit">
                  <span>Fit</span>
                  <strong>
                    {Math.round(application.fit_score)}%
                  </strong>
                </div>

                <div>
                  <span className="application-column-label">
                    Recommendation
                  </span>

                  <span
                    className={
                      application.recommendation === 'APPLY'
                        ? 'recommendation apply'
                        : 'recommendation'
                    }
                  >
                    {application.recommendation}
                  </span>
                </div>

                <div>
                  <span className="application-column-label">
                    Status
                  </span>

                  <span className={getStatusClass(application.status)}>
                    {getStatusIcon(application.status)}
                    {STATUS_LABELS[application.status] ||
                      application.status}
                  </span>
                </div>

                <div className="application-date">
                  <span className="application-column-label">
                    Updated
                  </span>
                  <span>{formatDate(application.updated_at)}</span>
                </div>

                {application.status === 'approved' ? (
                  <Link
                    to={`/execution/${application.application_id}`}
                    className="application-review-link application-execution-link"
                  >
                    <Play size={15} />
                    Execute
                  </Link>
                ) : (
                  <Link
                    to={`/review/${application.application_id}`}
                    className="application-review-link"
                  >
                    Review
                    <ArrowUpRight size={15} />
                  </Link>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default Applications
import { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  ArrowUpRight,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  LoaderCircle,
  Search,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { getApplications, getJobs } from '../services/api'

function getGreeting() {
  const hour = new Date().getHours()

  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

function formatDate() {
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  }).format(new Date())
}

function getStatusLabel(status) {
  return (status || 'pending_review')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function Dashboard() {
  const [jobs, setJobs] = useState([])
  const [applications, setApplications] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true)
        setError('')

        const [jobsData, applicationsData] = await Promise.all([
          getJobs(),
          getApplications(),
        ])

        setJobs(Array.isArray(jobsData) ? jobsData : [])

        setApplications(
          Array.isArray(applicationsData)
            ? applicationsData
            : applicationsData?.applications || [],
        )
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            'Unable to load your dashboard data.',
        )
      } finally {
        setLoading(false)
      }
    }

    loadDashboard()
  }, [])

  const dashboardStats = useMemo(() => {
    const strongMatches = applications.filter(
      (application) =>
        application.recommendation === 'APPLY' ||
        application.recommendation === 'STRONG_MATCH',
    ).length

    const pendingReview = applications.filter(
      (application) => application.status === 'pending_review',
    ).length

    const inProgress = applications.filter((application) =>
      ['approved', 'edit_required'].includes(application.status),
    ).length

    return {
      relevantJobs: jobs.length,
      strongMatches,
      applications: applications.length,
      pendingReview,
      inProgress,
    }
  }, [jobs, applications])

  const recentApplications = useMemo(
    () =>
      [...applications]
        .sort(
          (a, b) =>
            new Date(b.updated_at || b.created_at || 0) -
            new Date(a.updated_at || a.created_at || 0),
        )
        .slice(0, 3),
    [applications],
  )

  return (
    <div className="dashboard">
      <section className="welcome-section">
        <div>
          <p className="eyebrow">{formatDate()}</p>

          <h1>{getGreeting()}, Anvi.</h1>

          <p className="welcome-copy">
            Here&apos;s what your job search looks like today.
          </p>
        </div>

        <Link to="/jobs" className="primary-button">
          <Search size={17} />
          Discover jobs
        </Link>
      </section>

      {error && (
        <div className="validation-warning">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="state-card">
          <LoaderCircle className="loading-spinner" size={24} />
          <h3>Loading your dashboard</h3>
          <p>Fetching your latest jobs and application activity.</p>
        </div>
      ) : (
        <>
          <section className="stats-grid">
            <article className="stat-card">
              <div className="stat-card-top">
                <div className="stat-icon">
                  <Search size={18} strokeWidth={1.8} />
                </div>

                <ArrowUpRight size={16} className="stat-arrow" />
              </div>

              <div className="stat-value">
                {dashboardStats.relevantJobs}
              </div>

              <div className="stat-label">Relevant jobs</div>

              <div className="stat-change">
                Available in your job feed
              </div>
            </article>

            <article className="stat-card">
              <div className="stat-card-top">
                <div className="stat-icon">
                  <CheckCircle2 size={18} strokeWidth={1.8} />
                </div>

                <ArrowUpRight size={16} className="stat-arrow" />
              </div>

              <div className="stat-value">
                {dashboardStats.strongMatches}
              </div>

              <div className="stat-label">Strong matches</div>

              <div className="stat-change">
                Based on your current applications
              </div>
            </article>

            <article className="stat-card">
              <div className="stat-card-top">
                <div className="stat-icon">
                  <BriefcaseBusiness
                    size={18}
                    strokeWidth={1.8}
                  />
                </div>

                <ArrowUpRight size={16} className="stat-arrow" />
              </div>

              <div className="stat-value">
                {dashboardStats.applications}
              </div>

              <div className="stat-label">Applications</div>

              <div className="stat-change">
                {dashboardStats.pendingReview} awaiting review
              </div>
            </article>

            <article className="stat-card">
              <div className="stat-card-top">
                <div className="stat-icon">
                  <Clock3 size={18} strokeWidth={1.8} />
                </div>

                <ArrowUpRight size={16} className="stat-arrow" />
              </div>

              <div className="stat-value">
                {dashboardStats.inProgress}
              </div>

              <div className="stat-label">In progress</div>

              <div className="stat-change">
                Approved or awaiting edits
              </div>
            </article>
          </section>

          <section className="dashboard-grid">
            <article className="panel panel-large">
              <div className="panel-header">
                <div>
                  <p className="panel-kicker">
                    Recommended for you
                  </p>

                  <h2>Jobs worth your attention</h2>
                </div>

                <Link to="/jobs" className="text-button">
                  View all
                  <ArrowUpRight size={15} />
                </Link>
              </div>

              {jobs.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">
                    <Search size={22} />
                  </div>

                  <h3>No jobs discovered yet</h3>

                  <p>
                    Start job discovery to find opportunities that
                    match your skills and preferences.
                  </p>

                  <Link to="/jobs" className="secondary-button">
                    Start discovery
                  </Link>
                </div>
              ) : (
                <div className="dashboard-job-list">
                  {jobs.slice(0, 3).map((job) => (
                    <Link
                      to={`/jobs/${job.id}`}
                      className="dashboard-job"
                      key={job.id}
                    >
                      <div>
                        <strong>{job.title}</strong>

                        <span>
                          {job.company}
                          {job.location
                            ? ` · ${job.location}`
                            : ''}
                        </span>
                      </div>

                      <ArrowUpRight size={17} />
                    </Link>
                  ))}
                </div>
              )}
            </article>

            <article className="panel">
              <div className="panel-header">
                <div>
                  <p className="panel-kicker">
                    Application pipeline
                  </p>

                  <h2>Recent activity</h2>
                </div>
              </div>

              {recentApplications.length === 0 ? (
                <div className="empty-state compact">
                  <div className="empty-icon">
                    <BriefcaseBusiness size={20} />
                  </div>

                  <h3>No applications yet</h3>

                  <p>
                    Review a matched job and prepare your first
                    application package.
                  </p>

                  <Link
                    to="/jobs"
                    className="secondary-button"
                  >
                    Explore jobs
                  </Link>
                </div>
              ) : (
                <div className="activity-list">
                  {recentApplications.map((application) => (
                    <Link
                      to={`/review/${application.application_id}`}
                      className="activity-item"
                      key={application.application_id}
                    >
                      <div
                        className={`activity-status ${
                          application.status === 'approved'
                            ? 'ready'
                            : application.status ===
                                'rejected'
                              ? 'match'
                              : 'review'
                        }`}
                      />

                      <div>
                        <strong>
                          {getStatusLabel(application.status)}
                        </strong>

                        <span>
                          {application.job_title ||
                            'Application'}{' '}
                          ·{' '}
                          {application.company || 'Company'}
                        </span>
                      </div>

                      <ArrowUpRight size={15} />
                    </Link>
                  ))}
                </div>
              )}
            </article>
          </section>
        </>
      )}
    </div>
  )
}

export default Dashboard
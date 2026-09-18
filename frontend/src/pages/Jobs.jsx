import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  AlertCircle,
  BriefcaseBusiness,
  LoaderCircle,
  Search,
} from 'lucide-react'


import { searchJobs } from '../services/api'
import JobCard from '../components/ui/JobCard'

function Jobs() {
  const [jobs, setJobs] = useState([])
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState(
    searchParams.get('query') || '',
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadJobs() {
      try {
        setLoading(true)
        setError('')
        console.log('SEARCH QUERY:', query)

        setLoading(true)

        console.log('CALLING searchJobs')
        const data = query.trim()
          ? await searchJobs(query)
          : []
        console.log('SEARCH RESULT:', data)

        if (!cancelled) setJobs(data)
      } catch (err) {
        if (!cancelled) {
          setError(
            err.response?.data?.detail ||
              'Unable to search jobs. Please try again.',
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadJobs()

    return () => {
      cancelled = true
    }
  }, [query])

  async function handleSearch(event) {
    event.preventDefault()

    const value = query.trim()
    if (!value) return

    try {
      setLoading(true)
      setError('')
      setJobs(await searchJobs(value))
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Unable to search jobs. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="jobs-page">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Job discovery</p>
          <h1>Find roles that fit you.</h1>
          <p>
            ApplyIQ compares opportunities with your skills, experience, and
            career goals.
          </p>
        </div>

        <div className="jobs-count">
          <BriefcaseBusiness size={17} />
          {jobs.length} opportunities
        </div>
      </section>

      <form className="job-search-bar" onSubmit={handleSearch}>
        <Search size={18} />
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by role, company, or skill..."
          aria-label="Search jobs"
        />
      </form>

      {loading && (
        <div className="state-card">
          <LoaderCircle className="loading-spinner" size={24} />
          <h3>Finding opportunities</h3>
          <p>Loading jobs from your intelligence workspace.</p>
        </div>
      )}

      {!loading && error && (
        <div className="state-card error-state">
          <div className="state-icon">
            <AlertCircle size={22} />
          </div>
          <h3>We couldn't load your jobs</h3>
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && jobs.length === 0 && (
        <div className="state-card">
          <div className="state-icon">
            <Search size={22} />
          </div>
          <h3>No jobs found</h3>
          <p>
            Try a different role, company, location, or skill.
          </p>
        </div>
      )}

      {!loading && !error && jobs.length > 0 && (
        <section className="jobs-list">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </section>
      )}
    </div>
  )
}

export default Jobs
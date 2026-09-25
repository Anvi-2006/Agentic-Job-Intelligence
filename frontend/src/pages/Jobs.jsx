import { useSearchParams } from 'react-router-dom'
import {
  AlertCircle,
  BriefcaseBusiness,
  LoaderCircle,
  Search,
} from 'lucide-react'
import { useState } from 'react'

import { searchJobs } from '../services/api'
import JobCard from '../components/ui/JobCard'

function Jobs() {
  const [searchParams] = useSearchParams()

  const initialQuery = searchParams.get('query') || ''

  const [query, setQuery] = useState(initialQuery)
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function runSearch(searchValue) {
    const value = searchValue.trim()

    if (!value) {
      setJobs([])
      setError('')
      return
    }

    try {
      setLoading(true)
      setError('')

      const results = await searchJobs(value)

      setJobs(results)
    } catch (err) {
      console.error('Job search failed:', err)

      setError(
        err.response?.data?.detail ||
          err.message ||
          'Unable to search jobs. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  function handleSearch(event) {
    event.preventDefault()
    runSearch(query)
  }

  return (
    <div className="jobs-page">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Job discovery</p>

          <h1>Find roles that fit you.</h1>

          <p>
            ApplyIQ compares opportunities with your skills, experience,
            and career goals.
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

        <button
          type="submit"
          className="primary-button"
          disabled={loading || !query.trim()}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {loading && (
        <div className="state-card">
          <LoaderCircle className="loading-spinner" size={24} />

          <h3>Finding opportunities</h3>

          <p>
            ApplyIQ is searching connected job sources and preparing
            opportunities.
          </p>
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

          <h3>Search for your next opportunity</h3>

          <p>
            Search by role, company, technology, or another skill.
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
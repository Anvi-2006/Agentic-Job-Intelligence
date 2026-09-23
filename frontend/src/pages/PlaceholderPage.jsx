import { ArrowLeft } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

function PlaceholderPage() {
  const location = useLocation()

  const pageName = location.pathname
    .replace('/', '')
    .replaceAll('-', ' ')

  return (
    <div className="state-card">
      <h3>{pageName || 'Page'} is coming next</h3>

      <p>
        This section is part of the ApplyIQ workflow and will be connected to
        the backend in the next implementation stages.
      </p>

      <Link to="/dashboard" className="secondary-button">
        <ArrowLeft size={15} />
        Back to overview
      </Link>
    </div>
  )
}

export default PlaceholderPage
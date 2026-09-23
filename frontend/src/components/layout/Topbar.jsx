import { useState } from 'react'
import { Bell, Search } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function Topbar() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  function handleSearch(event) {
    event.preventDefault()

    const value = query.trim()

    if (!value) return

    navigate(`/jobs?query=${encodeURIComponent(value)}`)
  }

  return (
    <header className="topbar">
      <form className="topbar-search" onSubmit={handleSearch}>
        <Search size={18} strokeWidth={1.8} />

        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search jobs, companies, applications..."
          aria-label="Search"
        />

        <span className="search-shortcut">⌘ K</span>
      </form>

      <div className="topbar-actions">
        <button
          type="button"
          className="icon-button"
          aria-label="Notifications"
        >
          <Bell size={19} strokeWidth={1.8} />
          <span className="notification-dot" />
        </button>

        <div className="topbar-avatar">A</div>
      </div>
    </header>
  )
}

export default Topbar
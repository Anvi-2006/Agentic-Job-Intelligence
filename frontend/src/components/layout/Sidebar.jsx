import {
  BriefcaseBusiness,
  ClipboardCheck,
  FileText,
  LayoutDashboard,
  Search,
  Settings,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

const navigation = [
  {
    label: 'Overview',
    icon: LayoutDashboard,
    path: '/dashboard',
  },
  {
    label: 'Discover Jobs',
    icon: Search,
    path: '/jobs',
  },
  {
    label: 'Applications',
    icon: FileText,
    path: '/applications',
  },
  {
    label: 'Application Review',
    icon: ClipboardCheck,
    path: '/applications',
  },
  {
    label: 'Career Profile',
    icon: BriefcaseBusiness,
    path: '/profile',
  },
]

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">A</div>

        <div>
          <div className="brand-name">ApplyIQ</div>
          <div className="brand-subtitle">Job Intelligence</div>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        <div className="nav-section-label">Workspace</div>

        {navigation.map(({ label, icon: Icon, path }) => (
          <NavLink
            key={label}
            to={path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
          >
            <Icon size={18} strokeWidth={1.8} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <button type="button" className="nav-item">
          <Settings size={18} strokeWidth={1.8} />
          <span>Settings</span>
        </button>

        <div className="sidebar-profile">
          <div className="avatar">A</div>

          <div className="profile-info">
            <strong>Anvi</strong>
            <span>Candidate</span>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
import { Navigate, Route, Routes } from 'react-router-dom'

import AppShell from './components/layout/AppShell'
import Dashboard from './pages/Dashboard'
import Jobs from './pages/Jobs'
import PlaceholderPage from './pages/PlaceholderPage'
import JobDetails from './pages/JobDetails'
import ApplicationPackage from './pages/ApplicationPackage'
import ApplicationReview from './pages/ApplicationReview'
import Applications from './pages/Applications'
import ApplicationExecution from './pages/ApplicationExecution'

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/jobs/:jobId" element={<JobDetails />} />
        <Route path="/applications" element={<Applications />} />
        <Route
          path="/review/:applicationId"
          element={<ApplicationReview />}
        />
        <Route
          path="/execution/:applicationId"
          element={<ApplicationExecution />}
        />
        <Route path="/profile" element={<PlaceholderPage />} />
        <Route path="/settings" element={<PlaceholderPage />} />
        <Route
          path="/jobs/:jobId/application"
          element={<ApplicationPackage />}
        />
      </Route>
    </Routes>
  )
}

export default App
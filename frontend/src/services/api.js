import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
})

const CANDIDATE_ID = '332b3f24-eefc-4d05-99d5-56798d24a50c'

export async function getJobs() {
  const response = await api.get('/api/jobs')
  return response.data
}

export async function getJob(jobId) {
  const response = await api.get(`/api/jobs/${jobId}`)
  return response.data
}

export async function getJobFit(jobId) {
  const response = await api.get(
    `/api/job-fit/${CANDIDATE_ID}/${jobId}`,
  )
  return response.data
}
export async function generateApplicationPackage(jobId) {
  const response = await api.post(
    `/api/application-package/${CANDIDATE_ID}/${jobId}/generate`,
  )
  return response.data
}

export async function getApplicationPackage(jobId) {
  const response = await api.get(
    `/api/application-package/${CANDIDATE_ID}/${jobId}`,
  )
  return response.data
}

export async function reviewApplication(
  candidateId,
  jobId,
  decision,
  reviewerNote = '',
) {
  const response = await api.post(
    `/api/applications/${candidateId}/${jobId}/review`,
    {
      decision,
      reviewer_note: reviewerNote || null,
    },
  )

  return response.data
}

export async function getApplicationReview(applicationId) {
  const response = await api.get(
    `/api/applications/review/${applicationId}`,
  )
  return response.data
}

export async function getApplications() {
  const response = await api.get(
    `/api/applications/${CANDIDATE_ID}`,
  )

  return response.data
}

export async function searchJobs(query) {
  const response = await api.post('/api/jobs/search', {
    candidate_id: CANDIDATE_ID,
    query,
  })

  return response.data.jobs.map((job) => ({
    ...job,
    id: job.job_id,
  }))
}

export default api
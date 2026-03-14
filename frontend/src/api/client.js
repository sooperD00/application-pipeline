/**
 * api/client.js — fetch wrappers for all existing backend routes.
 *
 * Sprint 7 scaffolding. Thin functions, no abstraction astronautics.
 * The Vite dev proxy handles /api → localhost:8000, so no CORS issues.
 *
 * Convention:
 *   - All functions return parsed JSON (or a Response for SSE streams).
 *   - Errors throw with the status code and detail from FastAPI's error body.
 *   - No auth headers yet — the backend stub grabs the first User row.
 */

const BASE = ''  // empty = same origin, proxy handles it in dev

// ── Helpers ──────────────────────────────────────────────────────────────────

class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `API error ${status}`)
    this.status = status
    this.detail = detail
  }
}

async function request(path, options = {}) {
  const url = `${BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    let detail
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      detail = res.statusText
    }
    throw new ApiError(res.status, detail)
  }
  // 204 No Content (e.g. DELETE) — nothing to parse
  if (res.status === 204) return null
  return res.json()
}

function get(path) {
  return request(path)
}

function post(path, body) {
  return request(path, { method: 'POST', body: JSON.stringify(body) })
}

function patch(path, body) {
  return request(path, { method: 'PATCH', body: JSON.stringify(body) })
}

function del(path) {
  return request(path, { method: 'DELETE' })
}

// ── Sessions ─────────────────────────────────────────────────────────────────

/** GET /api/sessions — list all sessions for current user */
export function listSessions() {
  return get('/api/sessions')
}

/** POST /api/sessions — create session with metadata */
export function createSession({ board, filters, search_term }) {
  return post('/api/sessions', { board, filters, search_term })
}

/** GET /api/sessions/{id} — full session state with all JDs */
export function getSession(sessionId) {
  return get(`/api/sessions/${sessionId}`)
}

/** POST /api/sessions/{id}/jds — add a JD (auto-cleans on ingest) */
export function addJD(sessionId, { raw_text, company = '', role = '', compensation, employee_count, link }) {
  return post(`/api/sessions/${sessionId}/jds`, {
    raw_text, company, role, compensation, employee_count, link,
  })
}

/**
 * POST /api/sessions/{id}/analyze — kick off batch analysis.
 *
 * Returns a raw Response (SSE stream). The caller consumes it with
 * the useSSE hook (Sprint 10).
 *
 * This is the only client function that calls fetch() directly and returns
 * the raw Response — the analyze endpoint streams results via SSE, not a
 * single JSON blob. The caller reads that stream incrementally.
 *
 * Note: the endpoint takes no body. It fetches all of the user's resumes
 * internally (up to 3). The Sprint 7 scaffold had a phantom resume_id
 * param here — removed in Sprint 10 (first sprint where this is called
 * from UI). See remaining-sprints.md deferred section for the Phase 1+
 * resume selection feature that will re-add it with real plumbing.
 *
 * Usage:
 *   const res = await analyzeSession(id)
 *   // pass res to useSSE.consume()
 */
export async function analyzeSession(sessionId) {
  const url = `${BASE}/api/sessions/${sessionId}/analyze`
  const res = await fetch(url, {
    method: 'POST',
  })
  if (!res.ok) {
    let detail
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      detail = res.statusText
    }
    throw new ApiError(res.status, detail)
  }
  return res  // raw Response — caller reads the SSE stream
}

/** GET /api/sessions/{id}/tailoring-jobs — batch status dashboard */
export function listSessionTailoringJobs(sessionId) {
  return get(`/api/sessions/${sessionId}/tailoring-jobs`)
}

/**
 * POST /api/sessions/{id}/batch-tailor — Apply All (up to 4 parallel).
 *
 * No body — the backend fetches all user resumes internally.
 * Sprint 11: removed phantom resume_id param (same fix as analyzeSession
 * in Sprint 10). See remaining-sprints.md deferred section for Phase 1+
 * resume selection that will re-add it with real plumbing.
 */
export function batchTailor(sessionId, { force = false } = {}) {
  const qs = force ? '?force=true' : ''
  return request(`/api/sessions/${sessionId}/batch-tailor${qs}`, { method: 'POST' })
}

// ── JDs ──────────────────────────────────────────────────────────────────────

/** GET /api/jds/{id} — single JD with all relations */
export function getJD(jdId) {
  return get(`/api/jds/${jdId}`)
}

/** PATCH /api/jds/{id} — update status, app_questions, etc. 
 *  
 * Note: updateJD takes fields without destructuring — intentionally 
 * loose so you can pass any subset of fields to patch.
*/
export function updateJD(jdId, fields) {
  return patch(`/api/jds/${jdId}`, fields)
}

/** GET /api/jds/{id}/tailoring — per-JD tailoring history */
export function listJDTailoringJobs(jdId) {
  return get(`/api/jds/${jdId}/tailoring`)
}

/**
 * POST /api/jds/{id}/tailoring — kick off single tailoring job.
 *
 * No body — the backend fetches all user resumes internally.
 * Sprint 11: removed phantom resume_id param (same fix pattern as
 * analyzeSession in Sprint 10 and batchTailor above).
 */
export function createTailoringJob(jdId) {
  return request(`/api/jds/${jdId}/tailoring`, { method: 'POST' })
}

/** GET /api/jds/{id}/tailoring/{jobId} — tailoring status + outputs */
export function getTailoringJob(jdId, jobId) {
  return get(`/api/jds/${jdId}/tailoring/${jobId}`)
}

/**
 * GET /api/jds/{id}/tailoring/{jobId}/docx — download generated resume docx.
 *
 * Returns a Blob. Caller can create an object URL for download.
 *
 * Usage:
 *   const blob = await downloadTailoringDocx(jdId, jobId)
 *   const url = URL.createObjectURL(blob)
 *   window.open(url)  // browser opens/downloads the file
 */
export async function downloadTailoringDocx(jdId, jobId) {
  const url = `${BASE}/api/jds/${jdId}/tailoring/${jobId}/docx`
  const res = await fetch(url)
  if (!res.ok) {
    throw new ApiError(res.status, res.statusText)
  }
  return res.blob()
}

/**
 * GET /api/jds/{id}/tailoring/{jobId}/package — download zip bundle (ADR-014).
 *
 * Returns a Blob. Same download pattern as downloadTailoringDocx.
 */
export async function downloadTailoringPackage(jdId, jobId) {
  const url = `${BASE}/api/jds/${jdId}/tailoring/${jobId}/package`
  const res = await fetch(url)
  if (!res.ok) {
    throw new ApiError(res.status, res.statusText)
  }
  return res.blob()
}

// ── Resumes ──────────────────────────────────────────────────────────────────

/** GET /api/resumes — list user's resumes */
export function listResumes() {
  return get('/api/resumes')
}

/** POST /api/resumes — create resume (label + pasted text) */
export function createResume({ label, content }) {
  return post('/api/resumes', { label, content })
}

/** PATCH /api/resumes/{id} — edit label or content */
export function updateResume(resumeId, fields) {
  return patch(`/api/resumes/${resumeId}`, fields)
}

/** DELETE /api/resumes/{id} */
export function deleteResume(resumeId) {
  return del(`/api/resumes/${resumeId}`)
}

// ── Health ────────────────────────────────────────────────────────────────────

/** GET /health — backend liveness check */
export function healthCheck() {
  return get('/health')
}

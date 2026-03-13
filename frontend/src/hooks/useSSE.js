/**
 * useSSE — consume a Server-Sent Events stream from a raw fetch Response.
 *
 * Why not native EventSource? The analyze endpoint is POST, and EventSource
 * only supports GET. So we read the ReadableStream ourselves with a
 * TextDecoder and buffer-split on \n\n (the SSE message delimiter).
 *
 * All state mutation lives in the caller's callbacks — this hook is pure
 * parsing machinery. Returns { consume, abort }.
 *
 * The backend's SSE format (from analysis.py _sse helper):
 *   event: <event_name>\n
 *   data: <json_payload>\n
 *   \n
 *
 * Events: batch_start, jd_result, batch_complete, analysis_complete, error
 * 
 * Buffer Strategy: network chunks are not mapped to "message boundaries" (*their* 
 * chunks are not *your* chunks); use the classic `split('\n\n')` / `pop()` pattern:
 * split on the delimiter, process everything except the last element (because the 
 * last element might be a fragment or empty string). Same as file read. 
 * 
 * Ownership of state: this hook deliberately owns zero state (no useState here).
 * 
 * Lifecycle / cleanup: abort and abortedRef pattern for when a user navigates away 
 * or cancels mid-stream.
 */

import { useRef, useCallback } from 'react'

export default function useSSE() {
  const readerRef = useRef(null)
  const abortedRef = useRef(false)

  const abort = useCallback(() => {
    abortedRef.current = true
    if (readerRef.current) {
      readerRef.current.cancel().catch(() => {})
      readerRef.current = null
    }
  }, [])

  /**
   * Start consuming an SSE stream from a raw Response.
   *
   * Resolves when the stream ends (done=true) or is aborted.
   * The caller awaits this — all progress arrives via callbacks.
   *
   * @param {Response} response — raw fetch Response with body stream
   * @param {Object} callbacks — keyed by event name:
   *   { batch_start, jd_result, batch_complete, analysis_complete, error }
   *   Each receives the parsed JSON data payload.
   */
  const consume = useCallback(async (response, callbacks) => {
    abortedRef.current = false
    const reader = response.body.getReader()
    readerRef.current = reader
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done || abortedRef.current) break

        buffer += decoder.decode(value, { stream: true })

        // SSE messages are separated by double newlines.
        // Split and keep the last element — it's either empty (message was
        // complete) or a partial chunk still accumulating.
        const messages = buffer.split('\n\n')
        buffer = messages.pop()

        for (const message of messages) {
          if (!message.trim()) continue

          const parsed = parseSSEMessage(message)
          if (!parsed) continue

          // Dispatch: callback keys match event names directly.
          // New backend event? Just pass a new callback. Zero dispatch code.
          callbacks[parsed.event]?.(parsed.data)
        }
      }
      // Flush any remaining buffered message after stream closes.
      // The backend always terminates with \n\n, but a dropped connection
      // might not — parse whatever's left.
      if (buffer.trim()) {
        const parsed = parseSSEMessage(buffer)
        if (parsed) callbacks[parsed.event]?.(parsed.data)
      }
    } catch (err) {
      // Stream read error (network drop, etc.) — surface it as an SSE error
      if (!abortedRef.current) {
        callbacks.error?.({ message: err.message, recoverable: true })
      }
    } finally {
      readerRef.current = null
    }
  }, [])

  return { consume, abort }
}


/**
 * Parse a single SSE message block into { event, data }.
 *
 * Input format (one message, no trailing double-newline):
 *   event: batch_start
 *   data: {"batch": 1, "jd_numbers": [1,2,3,4,5]}
 *
 * Returns null if the message is malformed or data isn't valid JSON.
 */
export function parseSSEMessage(message) {
  let event = null
  let dataStr = ''

  for (const line of message.split('\n')) {
    if (line.startsWith('event:')) {
      event = line.slice('event:'.length).trim()
    } else if (line.startsWith('data:')) {
      // SSE spec allows multi-line data (concatenated), though our backend
      // sends single-line JSON. Handle it anyway for correctness.
      dataStr += line.slice('data:'.length).trim()
    }
  }

  if (!event || !dataStr) return null

  try {
    return { event, data: JSON.parse(dataStr) }
  } catch {
    return null
  }
}

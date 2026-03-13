import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import useSSE, { parseSSEMessage } from '../hooks/useSSE'

// ── parseSSEMessage unit tests ──────────────────────────────────────────────
// The parser is exported separately so we can test it without a full stream.

describe('parseSSEMessage', () => {
  it('parses a well-formed SSE message', () => {
    const msg = 'event: jd_result\ndata: {"jd_id":"abc","number":1,"status":"apply"}'
    const result = parseSSEMessage(msg)
    expect(result).toEqual({
      event: 'jd_result',
      data: { jd_id: 'abc', number: 1, status: 'apply' },
    })
  })

  it('returns null when event line is missing', () => {
    expect(parseSSEMessage('data: {"foo":"bar"}')).toBeNull()
  })

  it('returns null when data line is missing', () => {
    expect(parseSSEMessage('event: test')).toBeNull()
  })

  it('returns null when data is not valid JSON', () => {
    expect(parseSSEMessage('event: test\ndata: not-json')).toBeNull()
  })

  it('handles extra whitespace around event name', () => {
    const msg = 'event:   batch_start  \ndata: {"batch":1}'
    const result = parseSSEMessage(msg)
    expect(result.event).toBe('batch_start')
  })
})


// ── useSSE.consume integration tests ────────────────────────────────────────
// These test the full flow: fake ReadableStream → buffer → parse → callbacks.
//
// Callback keys match backend event names directly (batch_start, jd_result,
// etc.) — useSSE dispatches via callbacks[event]?.(data).

/**
 * Create a fake Response whose .body is a ReadableStream that emits the
 * given string(s) as encoded chunks. Single string = one chunk; array =
 * one chunk per element (tests chunked delivery).
 */
function makeFakeResponse(chunks) {
  if (typeof chunks === 'string') chunks = [chunks]
  let index = 0
  const stream = new ReadableStream({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(new TextEncoder().encode(chunks[index]))
        index++
      } else {
        controller.close()
      }
    },
  })
  return { body: stream }
}

describe('useSSE — consume', () => {
  it('dispatches all callbacks for a full analysis stream', async () => {
    const callbacks = {
      batch_start: vi.fn(),
      jd_result: vi.fn(),
      batch_complete: vi.fn(),
      analysis_complete: vi.fn(),
      error: vi.fn(),
    }

    // Simulate a 2-JD, single-batch analysis
    const sseText = [
      'event: batch_start',
      'data: {"batch":1,"jd_numbers":[1,2]}',
      '',
      'event: jd_result',
      'data: {"jd_id":"aaa","number":1,"status":"apply","analysis":"good fit","requirements_met":[],"exclude_company":false}',
      '',
      'event: jd_result',
      'data: {"jd_id":"bbb","number":2,"status":"no","analysis":"bad fit","requirements_met":[],"exclude_company":false}',
      '',
      'event: batch_complete',
      'data: {"batch":1,"meta_analysis":"One strong match out of two."}',
      '',
      'event: analysis_complete',
      'data: {"session_id":"sess-1","summary":{"apply":1,"maybe":0,"no":1}}',
      '',
    ].join('\n')

    const { result } = renderHook(() => useSSE())

    await act(async () => {
      await result.current.consume(makeFakeResponse(sseText), callbacks)
    })

    expect(callbacks.batch_start).toHaveBeenCalledOnce()
    expect(callbacks.batch_start).toHaveBeenCalledWith({
      batch: 1,
      jd_numbers: [1, 2],
    })

    expect(callbacks.jd_result).toHaveBeenCalledTimes(2)
    expect(callbacks.jd_result.mock.calls[0][0]).toMatchObject({
      jd_id: 'aaa',
      number: 1,
      status: 'apply',
    })
    expect(callbacks.jd_result.mock.calls[1][0]).toMatchObject({
      jd_id: 'bbb',
      number: 2,
      status: 'no',
    })

    expect(callbacks.batch_complete).toHaveBeenCalledOnce()
    expect(callbacks.batch_complete).toHaveBeenCalledWith({
      batch: 1,
      meta_analysis: 'One strong match out of two.',
    })

    expect(callbacks.analysis_complete).toHaveBeenCalledOnce()
    expect(callbacks.analysis_complete.mock.calls[0][0].summary).toEqual({
      apply: 1,
      maybe: 0,
      no: 1,
    })

    expect(callbacks.error).not.toHaveBeenCalled()
  })

  it('handles chunked delivery — message split across network chunks', async () => {
    const callbacks = {
      batch_start: vi.fn(),
      analysis_complete: vi.fn(),
    }

    // Split a batch_start message right in the middle of the JSON
    const chunk1 = 'event: batch_start\ndata: {"batch":1,"jd_nu'
    const chunk2 = 'mbers":[1]}\n\nevent: analysis_complete\ndata: {"session_id":"s","summary":{"apply":1,"maybe":0,"no":0}}\n\n'

    const { result } = renderHook(() => useSSE())

    await act(async () => {
      await result.current.consume(makeFakeResponse([chunk1, chunk2]), callbacks)
    })

    // The buffering logic should reassemble the split message
    expect(callbacks.batch_start).toHaveBeenCalledWith({
      batch: 1,
      jd_numbers: [1],
    })
    expect(callbacks.analysis_complete).toHaveBeenCalledOnce()
  })

  it('dispatches error callback for SSE error events', async () => {
    const callbacks = { error: vi.fn() }

    const sseText = 'event: error\ndata: {"batch":1,"message":"Claude API error after retry: timeout","recoverable":true}\n\n'

    const { result } = renderHook(() => useSSE())

    await act(async () => {
      await result.current.consume(makeFakeResponse(sseText), callbacks)
    })

    expect(callbacks.error).toHaveBeenCalledWith({
      batch: 1,
      message: 'Claude API error after retry: timeout',
      recoverable: true,
    })
  })

  it('ignores unknown event types gracefully', async () => {
    const callbacks = {
      batch_start: vi.fn(),
      jd_result: vi.fn(),
    }

    const sseText = [
      'event: some_future_event',
      'data: {"foo":"bar"}',
      '',
      'event: jd_result',
      'data: {"jd_id":"x","number":1,"status":"maybe"}',
      '',
    ].join('\n')

    const { result } = renderHook(() => useSSE())

    await act(async () => {
      await result.current.consume(makeFakeResponse(sseText), callbacks)
    })

    // Unknown event silently skipped, known event still fires
    expect(callbacks.batch_start).not.toHaveBeenCalled()
    expect(callbacks.jd_result).toHaveBeenCalledOnce()
  })
})

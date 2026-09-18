// Pure overview-view helpers ported 1:1 from the legacy view
// (src/agentos/gateway/static/js/views/overview.js) and the shared UI helpers
// it consumes (static/js/components.js relTime / sessionStatus*). Each function
// carries the legacy line range it mirrors so the parity matrix stays auditable.
// RPC calls, event subscriptions, and rendering live in OverviewPage.tsx; this
// module owns the pure derivations (label mapping, formatting, session sort).

// Registers this view's copy; it ships in this chunk, not the entry bundle.
import '@/i18n/en/overview'
import { t } from '@/i18n'

/** A recent session row as returned by sessions.list (all fields optional). */
export interface OverviewSession {
  key?: string
  status?: string
  model?: string
  message_count?: number
  messageCount?: number
  updated_at?: string | number
  updatedAt?: string | number
  [key: string]: unknown
}

/** overview.js:352-365 — readiness status -> human label. Known tokens map
 *  directly; anything else is Title-cased by splitting _/- separators. Empty /
 *  nullish falls back to "Unknown". */
export function readinessStatusLabel(status?: string | null): string {
  const labels: Record<string, string> = {
    ready: t('overview.readyReady'),
    degraded: t('overview.readyDegraded'),
    action_required: t('overview.readyActionRequired'),
    unavailable: t('overview.readyUnavailable'),
    unknown: t('overview.readyUnknown'),
  }
  const key = String(status || 'unknown').toLowerCase()
  if (labels[key]) return labels[key]
  return key.replace(/[_-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/** overview.js:234-242 — uptime_ms -> "Hh Mm Ss"; null/undefined -> "—". */
export function formatUptime(ms?: number | null): string {
  if (ms == null) return t('common.dash')
  const s = Math.floor(ms / 1000)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return t('overview.uptime', { hours: h, minutes: m, seconds: s % 60 })
}

// components.js:249-269 — session status -> dot color variant / tooltip label.
const SESSION_STATUS_DOT: Record<string, string> = {
  running: 'ok',
  done: 'off',
  failed: 'err',
  killed: 'off',
  timeout: 'warn',
}

/** components.js:272-275 — dot color variant ("ok"/"warn"/"err"/"off"). */
export function sessionStatusClass(status?: string | null): string {
  const k = String(status || '').toLowerCase()
  return SESSION_STATUS_DOT[k] || 'off'
}

/** components.js:284-287 — tooltip label; raw string else "Unknown" when empty. */
export function sessionStatusLabel(status?: string | null): string {
  const labels: Record<string, string> = {
    running: t('overview.sessionRunning'),
    done: t('overview.sessionDone'),
    failed: t('overview.sessionFailed'),
    killed: t('overview.sessionKilled'),
    timeout: t('overview.sessionTimeout'),
  }
  const k = String(status || '').toLowerCase()
  return labels[k] || (status ? String(status) : t('overview.sessionUnknown'))
}

/** components.js:228-241 — relative time. Numeric input is treated as an epoch
 *  (seconds when < 1e10, else millis); strings parse as ISO. Invalid -> "—". */
export function relTime(isoOrTs: string | number): string {
  const numeric =
    typeof isoOrTs === 'number'
      ? isoOrTs
      : typeof isoOrTs === 'string' && isoOrTs.trim() !== ''
        ? Number(isoOrTs)
        : NaN
  const d = Number.isFinite(numeric)
    ? new Date(Math.abs(numeric) < 10_000_000_000 ? numeric * 1000 : numeric)
    : new Date(isoOrTs)
  if (Number.isNaN(d.getTime())) return t('common.dash')
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 60) return t('overview.relJustNow')
  if (diff < 3600) return t('overview.relMinutes', { count: Math.floor(diff / 60) })
  if (diff < 86_400) return t('overview.relHours', { count: Math.floor(diff / 3600) })
  return t('overview.relDays', { count: Math.floor(diff / 86_400) })
}

/** overview.js:320-326 — JSON-stringify a payload, truncating at 80 chars with
 *  an ellipsis; fall back to String() when serialization throws. */
export function formatEventPayload(payload: unknown): string {
  let payloadStr = ''
  try {
    payloadStr = JSON.stringify(payload)
    if (payloadStr.length > 80) payloadStr = payloadStr.slice(0, 80) + '…'
  } catch {
    payloadStr = String(payload)
  }
  return payloadStr
}

/** overview.js:318-319 — a Date -> "HH:MM:SS" (local time). */
export function formatEventTs(now: Date): string {
  return now.toTimeString().slice(0, 8)
}

/** Coerce updated_at / updatedAt to a millisecond timestamp, or 0 when absent/invalid. */
function sessionUpdatedAtMs(s: OverviewSession): number {
  const val = s.updated_at ?? s.updatedAt
  if (val == null || val === '') return 0
  if (typeof val === 'number') {
    if (!Number.isFinite(val)) return 0
    return Math.abs(val) < 10_000_000_000 ? val * 1000 : val
  }
  if (typeof val === 'string') {
    const trimmed = val.trim()
    if (!trimmed) return 0
    const n = Number(trimmed)
    if (Number.isFinite(n)) {
      return Math.abs(n) < 10_000_000_000 ? n * 1000 : n
    }
    const d = new Date(trimmed).getTime()
    return Number.isNaN(d) ? 0 : d
  }
  return 0
}

/** overview.js:274-281 — sort sessions by updated_at / updatedAt descending
 *  (missing -> epoch 0) and slice to the first 6. Never mutates the input. */
export function sortRecentSessions(sessions: OverviewSession[]): OverviewSession[] {
  return sessions
    .slice()
    .sort((a, b) => {
      const ta = sessionUpdatedAtMs(a)
      const tb = sessionUpdatedAtMs(b)
      return tb - ta
    })
    .slice(0, 6)
}

/** overview.js:263 — localized token count; null/undefined -> "—". */
export function formatTokens(total?: number | null): string {
  return total != null ? total.toLocaleString() : t('common.dash')
}

/** overview.js:266-268 — total cost as "$X.XXXX"; null/undefined -> "—". */
export function formatCost(usd?: number | null): string {
  return usd != null ? '$' + Number(usd).toFixed(4) : t('common.dash')
}

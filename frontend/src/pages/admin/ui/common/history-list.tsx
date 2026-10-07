import type { AuditEntry } from '../../api/types'
import { formatStamp } from '../../lib/format'
import { AUDIT_ACTION_LABELS, AUDIT_ENTITY_LABELS } from '../../lib/labels'

function show(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (Array.isArray(value)) return value.length ? value.map(show).join(', ') : '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

/** Field changes stored as {field: [old, new]}. */
function changes(entry: AuditEntry) {
  return Object.entries(entry.changes).map(([field, pair]) => {
    const [before, after] = Array.isArray(pair) && pair.length === 2 ? pair : [undefined, pair]
    return { field, before: show(before), after: show(after) }
  })
}

const LONG = 140

function clip(text: string) {
  return text.length > LONG ? `${text.slice(0, LONG)}…` : text
}

export function HistoryList({
  entries,
  withEntity,
}: {
  entries: AuditEntry[]
  withEntity?: boolean
}) {
  if (!entries.length) return <p className="admin-hint">Изменений пока не было.</p>
  return (
    <ol className="history">
      {entries.map((entry) => (
        <li key={entry.id} className="history__item">
          <p className="history__head">
            <span>{formatStamp(entry.createdAt)}</span>
            <span>{entry.actorEmail ?? 'система'}</span>
            <strong>{AUDIT_ACTION_LABELS[entry.action] ?? entry.action}</strong>
            {withEntity && (
              <span>
                {AUDIT_ENTITY_LABELS[entry.entity] ?? entry.entity} · {entry.entityId}
              </span>
            )}
          </p>
          {changes(entry).length > 0 && (
            <ul className="history__changes">
              {changes(entry).map((change) => (
                <li key={change.field}>
                  <code>{change.field}</code>: {clip(change.before)} → {clip(change.after)}
                </li>
              ))}
            </ul>
          )}
          {entry.reason && <p className="history__reason">Причина: {entry.reason}</p>}
        </li>
      ))}
    </ol>
  )
}

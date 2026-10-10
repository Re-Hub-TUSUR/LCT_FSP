import type { CandidateContactsDto } from '../api/candidate-api'

/** Opened contacts on one line: the email, then the phone and Telegram the candidate left. */
export function contactsLine(contacts: CandidateContactsDto): string {
  const telegram = contacts.telegram?.replace(/^@+/, '')
  return [contacts.email, contacts.phone, telegram ? `@${telegram}` : null]
    .filter(Boolean)
    .join(' · ')
}

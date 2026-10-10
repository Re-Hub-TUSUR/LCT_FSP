import { consentDocument } from '../config/consent'
import { privacyDocument } from '../config/privacy'
import { termsDocument } from '../config/terms'
import { LegalPage } from './legal-page'

export function PrivacyPage() {
  return <LegalPage document={privacyDocument} downloadHref="/legal/kadry-privacy-policy.docx" />
}

export function TermsPage() {
  return <LegalPage document={termsDocument} downloadHref="/legal/kadry-user-agreement.docx" />
}

export function ConsentPage() {
  return <LegalPage document={consentDocument} downloadHref="/legal/kadry-consent.docx" />
}

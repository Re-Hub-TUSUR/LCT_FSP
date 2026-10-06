import type { CandidateDto } from '../api/candidate-api'
import './candidate-resumes.css'

/** Priority resume first. Hidden when the person has only one profile. */
export function CandidateResumes({ candidate }: { candidate: CandidateDto }) {
  const resumes = candidate.resumes ?? []
  if (resumes.length < 2) return null
  return (
    <ul className="candidate-resumes" aria-label="Резюме">
      {resumes.map((resume) => (
        <li key={resume.id}>
          <span
            className={
              resume.isPrimary
                ? 'candidate-resumes__mark'
                : 'candidate-resumes__mark candidate-resumes__mark--muted'
            }
          >
            {resume.isPrimary ? 'Приоритетное' : 'Второстепенное'}
          </span>
          {resume.headline ?? resume.specialization}
        </li>
      ))}
    </ul>
  )
}

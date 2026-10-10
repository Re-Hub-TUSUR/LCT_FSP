import { useEffect, useState } from 'react'
import { ROUTES } from '@/shared/config'
import { Button, ButtonLink, Modal } from '@/shared/ui'

const KEY = 'kadry:resume-next-step'

/**
 * The first save takes the candidate from the form to the profile, and the page mounts anew
 * (the cabinet opens around it), so the form leaves a note for the profile page to find.
 */
export function rememberFirstResume() {
  try {
    sessionStorage.setItem(KEY, '1')
  } catch {
    // Private mode: the window is skipped, the test is still one click away in the menu.
  }
}

function firstResumeJustSaved(): boolean {
  try {
    return sessionStorage.getItem(KEY) === '1'
  } catch {
    return false
  }
}

/** Right after the first resume: the next step is the test, said in a window, not a line. */
export function ResumeNextStep() {
  const [open, setOpen] = useState(firstResumeJustSaved)

  useEffect(() => {
    try {
      sessionStorage.removeItem(KEY)
    } catch {
      // Nothing was stored.
    }
  }, [])

  if (!open) return null
  return (
    <Modal title="Резюме сохранено" onClose={() => setOpen(false)}>
      <p className="resume-next__text">
        Оно приоритетное: вакансии подбираются по нему в первую очередь.
      </p>
      <p className="resume-next__text">
        Следующий шаг — тест. Он подтверждает грейд, и после него работодатели находят вас в банке
        кандидатов.
      </p>
      <div className="resume-start__actions">
        <ButtonLink to={ROUTES.testing}>Пройти тест</ButtonLink>
        <Button type="button" variant="ghost" size="inline" onClick={() => setOpen(false)}>
          Позже
        </Button>
      </div>
    </Modal>
  )
}

import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { ROUTES } from '@/shared/config'
import { Button, ButtonLink, Modal } from '@/shared/ui'

const KEY = 'kadry:resume-next-step'

type Note = 'saved' | 'link-fsp'

/**
 * The first save takes the candidate from the form to the profile, and the page mounts anew
 * (the cabinet opens around it), so the form leaves a note for the profile page to find.
 * `linkFsp`: the candidate asked for the FSP results and has no FSP ID linked yet.
 */
export function rememberFirstResume(linkFsp = false) {
  try {
    sessionStorage.setItem(KEY, linkFsp ? 'link-fsp' : 'saved')
  } catch {
    // Private mode: the window is skipped, the test is still one click away in the menu.
  }
}

function firstResumeNote(): Note | null {
  try {
    const note = sessionStorage.getItem(KEY)
    return note === 'saved' || note === 'link-fsp' ? note : null
  } catch {
    return null
  }
}

/** Right after the first resume: the next step is the test, said in a window, not a line. */
export function ResumeNextStep() {
  const [note, setNote] = useState(firstResumeNote)

  useEffect(() => {
    // «Сохранить» is at the bottom of the form: the profile that replaces it starts from the top.
    if (firstResumeNote()) window.scrollTo({ top: 0 })
    try {
      sessionStorage.removeItem(KEY)
    } catch {
      // Nothing was stored.
    }
  }, [])

  if (!note) return null
  const close = () => setNote(null)
  return (
    <Modal title="Резюме сохранено" onClose={close}>
      <p className="resume-next__text">
        Оно приоритетное: вакансии подбираются по нему в первую очередь.
      </p>
      <p className="resume-next__text">
        Следующий шаг — тест. Он подтверждает грейд, и после него работодатели находят вас в банке
        кандидатов.
      </p>
      {note === 'link-fsp' && (
        <p className="resume-next__text">
          Чтобы результаты пришли из реестра ФСП,{' '}
          <Link to={ROUTES.profileSettings}>привяжите ФСП ID в настройках</Link>.
        </p>
      )}
      <div className="resume-start__actions">
        <ButtonLink to={ROUTES.testing}>Пройти тест</ButtonLink>
        <Button type="button" variant="ghost" size="inline" onClick={close}>
          Позже
        </Button>
      </div>
    </Modal>
  )
}

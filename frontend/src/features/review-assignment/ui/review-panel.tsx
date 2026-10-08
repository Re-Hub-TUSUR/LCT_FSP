import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { TASK_KIND_LABELS, assignmentApi, assignmentKeys } from '@/entities/assessment'
import type { AssignmentDetailDto, ReviewGrade, ReviewTaskDto } from '@/entities/assessment'
import { getErrorMessage } from '@/shared/api'
import { Button, TextArea, TextField } from '@/shared/ui'
import './review-panel.css'

type Draft = { percent: string; comment: string }

const percentOf = (points: number | null) =>
  points === null ? '' : String(Math.round(points * 100))

/** The candidate's answer next to what was expected; every kind shows it its own way. */
function Answer({ task }: { task: ReviewTaskDto }) {
  if (!task.answered) return <p className="review__empty">Кандидат не ответил</p>
  switch (task.kind) {
    case 'quiz':
      return (
        <ul className="review__options">
          {task.review.options.map((option, index) => {
            const chosen = task.review.selected.includes(index)
            const correct = task.review.correct.includes(index)
            return (
              // Options are a fixed list of the task.
              // oxlint-disable-next-line react/no-array-index-key
              <li key={index} className={correct ? 'is-correct' : chosen ? 'is-wrong' : undefined}>
                {option}
                {chosen && <span> · выбрал кандидат</span>}
                {correct && <span> · верный</span>}
              </li>
            )
          })}
        </ul>
      )
    case 'code':
      return (
        <>
          <p className="review__label">Решение · {task.review.language}</p>
          <pre className="review__code">{task.review.code}</pre>
        </>
      )
    case 'open':
      return (
        <>
          <p className="review__text">{task.review.text}</p>
          {task.review.guidance && (
            <p className="review__guidance">На что смотреть: {task.review.guidance}</p>
          )}
        </>
      )
  }
}

/** A finished test of one candidate: answers, points and grading of the hand-checked ones. */
export function ReviewPanel({ detail }: { detail: AssignmentDetailDto }) {
  const queryClient = useQueryClient()
  const gradable = detail.tasks.filter((task) => task.manual && task.answered)
  const [drafts, setDrafts] = useState<Record<string, Draft>>(() =>
    Object.fromEntries(
      gradable.map((task) => [
        task.id,
        { percent: percentOf(task.points), comment: task.comment ?? '' },
      ]),
    ),
  )
  const [problem, setProblem] = useState('')

  const save = useMutation({
    mutationFn: (grades: ReviewGrade[]) => assignmentApi.review(detail.id, grades),
    onSuccess: (next) => {
      queryClient.setQueryData(assignmentKeys.detail(detail.id), next)
      void queryClient.invalidateQueries({ queryKey: assignmentKeys.outgoing() })
    },
  })

  const setDraft = (taskId: string, patch: Partial<Draft>) => {
    setDrafts((prev) => ({
      ...prev,
      [taskId]: { percent: '', comment: '', ...prev[taskId], ...patch },
    }))
    setProblem('')
  }

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const grades: ReviewGrade[] = []
    for (const task of gradable) {
      const draft = drafts[task.id]
      const percent = Number(draft?.percent)
      if (!draft || draft.percent.trim() === '' || !(percent >= 0 && percent <= 100)) {
        return setProblem('Оцените каждый открытый ответ: от 0 до 100')
      }
      grades.push({ taskId: task.id, points: percent / 100, comment: draft.comment.trim() || null })
    }
    save.mutate(grades)
  }

  return (
    <form className="review" noValidate onSubmit={onSubmit}>
      <div className="review__tiles">
        <div className="review__tile">
          <p className="review__tile-label">Итог</p>
          <p className="review__summary">
            {detail.score === null
              ? 'Итог появится, когда будут оценены все открытые ответы'
              : `Итог: ${Math.round(detail.score)} из 100 · проходной балл ${detail.passScore}`}
          </p>
        </div>
        <div className="review__tile">
          <p className="review__tile-label">Наблюдения</p>
          <p className="review__signals">
            Вставок из буфера: {detail.pasteCount} · уходов с вкладки: {detail.blurCount}. Это
            наблюдения, а не оценка: на балл они не влияют.
          </p>
        </div>
      </div>

      <ol className="review__tasks">
        {detail.tasks.map((task, index) => {
          const draft = drafts[task.id]
          return (
            <li
              key={task.id}
              className={task.points === null ? 'review__task is-waiting' : 'review__task'}
            >
              <header className="review__head">
                <p className="review__label">
                  <span className="review__num" aria-hidden="true">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  {TASK_KIND_LABELS[task.kind]}
                </p>
                <p className="review__points">
                  {task.points === null ? 'Ждёт оценки' : `${Math.round(task.points * 100)}%`}
                </p>
              </header>
              <h4 className="review__title">{task.title}</h4>
              {task.statement !== task.title && (
                <p className="review__statement">{task.statement}</p>
              )}
              <Answer task={task} />
              {draft && (
                <div className="review__grade">
                  <TextField
                    id={`grade-${task.id}`}
                    label="Оценка, % от задания"
                    inputMode="numeric"
                    value={draft.percent}
                    onChange={(e) => setDraft(task.id, { percent: e.target.value })}
                  />
                  <TextArea
                    id={`comment-${task.id}`}
                    label="Комментарий"
                    maxLength={2000}
                    value={draft.comment}
                    onChange={(e) => setDraft(task.id, { comment: e.target.value })}
                  />
                </div>
              )}
            </li>
          )
        })}
      </ol>

      {gradable.length > 0 && (
        <footer className="review__foot">
          {problem || save.isError ? (
            <p className="review__error" role="alert">
              {problem || getErrorMessage(save.error)}
            </p>
          ) : (
            <p className="review__hint">Оценка каждого открытого ответа — от 0 до 100</p>
          )}
          <Button type="submit" size="inline" disabled={save.isPending}>
            {save.isPending ? 'Сохраняем…' : 'Сохранить оценки'}
          </Button>
        </footer>
      )}
    </form>
  )
}

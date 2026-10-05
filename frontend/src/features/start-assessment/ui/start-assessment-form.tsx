import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { assessmentApi, assessmentKeys } from '@/entities/assessment'
import type { AttemptDetailDto } from '@/entities/assessment'
import { categoryQueries } from '@/entities/category'
import { getErrorMessage } from '@/shared/api'
import { Button, QueryState, SelectField } from '@/shared/ui'
import './start-assessment-form.css'

type Props = {
  /** Pre-selects what the candidate has already confirmed or tried. */
  defaultSpecialization?: string | null
  defaultGrade?: string | null
  onStarted?: (attempt: AttemptDetailDto) => void
}

/** Specialization and declared grade: the test confirms exactly this pair. */
export function StartAssessmentForm({ defaultSpecialization, defaultGrade, onStarted }: Props) {
  const queryClient = useQueryClient()
  const dictionary = useQuery(categoryQueries.dictionary())
  const [specialization, setSpecialization] = useState(defaultSpecialization ?? '')
  const [grade, setGrade] = useState(defaultGrade ?? '')
  const [touched, setTouched] = useState(false)

  const start = useMutation({
    mutationFn: assessmentApi.start,
    onSuccess: (attempt) => {
      queryClient.setQueryData(assessmentKeys.attempt(attempt.id), attempt)
      void queryClient.invalidateQueries({ queryKey: assessmentKeys.status() })
      onStarted?.(attempt)
    },
  })

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setTouched(true)
    if (specialization && grade) start.mutate({ specialization, grade })
  }

  return (
    <QueryState query={dictionary}>
      {(data) => (
        <form className="start-test" noValidate onSubmit={onSubmit}>
          <div className="start-test__fields">
            <SelectField
              id="test-specialization"
              label="Специализация"
              value={specialization}
              error={touched && !specialization ? 'Выберите специализацию' : undefined}
              onChange={(e) => setSpecialization(e.target.value)}
            >
              <option value="">Не выбрана</option>
              {data.specializations.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.label}
                </option>
              ))}
            </SelectField>
            <SelectField
              id="test-grade"
              label="Грейд, на который претендуете"
              value={grade}
              error={touched && !grade ? 'Выберите грейд' : undefined}
              onChange={(e) => setGrade(e.target.value)}
            >
              <option value="">Не выбран</option>
              {data.grades.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.label}
                </option>
              ))}
            </SelectField>
          </div>

          <ul className="start-test__rules">
            <li>Тест идёт 25–35 минут: вопросы с выбором ответа и одна задача на код.</li>
            <li>Таймер запускается сразу и не ставится на паузу.</li>
            <li>Код можно запускать на открытых тестах; итог считается по закрытым.</li>
            <li>Проходной балл — 60 из 100. Если не набрать, категория не присваивается.</li>
          </ul>

          {start.isError && (
            <p className="start-test__error" role="alert">
              {getErrorMessage(start.error)}
            </p>
          )}

          <Button type="submit" size="inline" disabled={start.isPending}>
            {start.isPending ? 'Готовим вариант…' : 'Начать тест'}
          </Button>
        </form>
      )}
    </QueryState>
  )
}

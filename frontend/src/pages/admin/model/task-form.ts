import type {
  AdminTaskDetail,
  AdminTaskWrite,
  CodeGroup,
  CodePayload,
  QuizPayload,
  TaskKind,
} from '../api/types'

export type VariableDraft = { name: string; min: string; max: string; step: string }
export type OptionDraft = { text: string; correct: boolean }

export type TaskForm = {
  kind: TaskKind
  title: string
  statement: string
  specializations: string[]
  grade: string
  skill: string
  difficulty: 'easy' | 'medium' | 'hard'
  timeLimitMinutes: string
  variables: VariableDraft[]
  status: 'draft' | 'active'
  options: OptionDraft[]
  multiple: boolean
  languages: string
  runLimitSeconds: string
  groups: CodeGroup[]
  referenceLanguage: string
  referenceCode: string
  /** The one starter the form edits; starters of other languages are kept as they are. */
  starterLanguage: string
  starterCode: string
  starterOther: Record<string, string>
}

const VARIABLE_NAME = /^[A-Za-z_][A-Za-z0-9_]{0,31}$/
const PLACEHOLDER = /\{([A-Za-z_][A-Za-z0-9_]*)\}/g

export function emptyForm(kind: TaskKind = 'quiz'): TaskForm {
  return {
    kind,
    title: '',
    statement: '',
    specializations: [],
    grade: '',
    skill: '',
    difficulty: 'medium',
    timeLimitMinutes: '',
    variables: [],
    status: 'draft',
    options: [
      { text: '', correct: true },
      { text: '', correct: false },
    ],
    multiple: false,
    languages: '',
    runLimitSeconds: '5',
    groups: [
      { input: '', expected: '', hidden: false },
      { input: '', expected: '', hidden: true },
    ],
    referenceLanguage: '',
    referenceCode: '',
    starterLanguage: '',
    starterCode: '',
    starterOther: {},
  }
}

export function toForm(task: AdminTaskDetail): TaskForm {
  const form = emptyForm(task.kind)
  const base = {
    ...form,
    title: task.title,
    statement: task.statement,
    specializations: task.specializations,
    grade: task.grade ?? '',
    skill: task.skill,
    difficulty: task.difficulty,
    timeLimitMinutes: task.timeLimitMinutes ? String(task.timeLimitMinutes) : '',
    variables: task.variables.map((variable) => ({
      name: variable.name,
      min: String(variable.min),
      max: String(variable.max),
      step: String(variable.step),
    })),
  }
  if (task.kind === 'quiz') {
    const payload = task.payload as QuizPayload
    return {
      ...base,
      options: payload.options.map((text, index) => ({
        text,
        correct: payload.correct.includes(index),
      })),
      multiple: payload.multiple,
    }
  }
  const payload = task.payload as CodePayload
  const [[starterLanguage, starterCode] = ['', ''], ...otherStarters] = Object.entries(
    payload.starter ?? {},
  )
  return {
    ...base,
    starterLanguage,
    starterCode,
    starterOther: Object.fromEntries(otherStarters),
    languages: payload.languages.join(', '),
    runLimitSeconds: String(payload.timeLimit),
    groups: payload.groups,
    referenceLanguage: payload.reference?.language ?? '',
    referenceCode: payload.reference?.code ?? '',
  }
}

/** Placeholders `{name}` of the statement and the quiz options without a declared variable. */
export function undeclared(form: TaskForm): string[] {
  const declared = new Set(form.variables.map((variable) => variable.name))
  const texts = [form.statement, ...(form.kind === 'quiz' ? form.options.map((o) => o.text) : [])]
  const used = texts.flatMap((text) => [...text.matchAll(PLACEHOLDER)].map((match) => match[1]!))
  return [...new Set(used.filter((name) => !declared.has(name)))]
}

/** The first problem a person can fix in the form, or null. The server re-checks everything. */
export function validate(form: TaskForm): string | null {
  if (!form.title.trim()) return 'Укажите название'
  if (!form.statement.trim()) return 'Укажите условие'
  if (!form.skill.trim()) return 'Укажите навык'
  const minutes = form.timeLimitMinutes.trim()
  if (
    minutes &&
    !(Number.isInteger(Number(minutes)) && Number(minutes) >= 1 && Number(minutes) <= 240)
  ) {
    return 'Лимит времени — целое число минут от 1 до 240'
  }
  const names = new Set<string>()
  for (const variable of form.variables) {
    if (!VARIABLE_NAME.test(variable.name)) {
      return `Имя переменной «${variable.name}»: латиница, цифры и _, не с цифры`
    }
    if (names.has(variable.name)) return `Переменная «${variable.name}» объявлена дважды`
    names.add(variable.name)
    const [min, max, step] = [Number(variable.min), Number(variable.max), Number(variable.step)]
    if (
      [min, max, step].some((value) => Number.isNaN(value)) ||
      variable.min === '' ||
      variable.max === ''
    ) {
      return `Диапазон переменной «${variable.name}»: числа от и до`
    }
    if (min > max) return `Переменная «${variable.name}»: «от» больше «до»`
    if (step <= 0) return `Переменная «${variable.name}»: шаг должен быть больше нуля`
  }
  const missing = undeclared(form)
  if (missing.length) return `В тексте есть необъявленные переменные: ${missing.join(', ')}`
  if (form.kind === 'quiz') {
    const filled = form.options.filter((option) => option.text.trim())
    if (filled.length < 2) return 'Нужно минимум два варианта ответа'
    const correct = filled.filter((option) => option.correct).length
    if (correct === 0) return 'Отметьте правильный вариант'
    if (!form.multiple && correct > 1) return 'В вопросе с одним ответом правильный вариант один'
  } else {
    const groups = form.groups.filter((group) => group.expected.trim())
    if (groups.length < 2) return 'Нужно минимум два тест-кейса с ожидаемым выводом'
    if (!groups.some((group) => group.hidden) || groups.every((group) => group.hidden)) {
      return 'Нужен хотя бы один открытый и один скрытый тест-кейс'
    }
    const seconds = Number(form.runLimitSeconds)
    if (!(seconds > 0 && seconds <= 20)) return 'Лимит запуска — от 0 до 20 секунд'
    if (Boolean(form.referenceCode.trim()) !== Boolean(form.referenceLanguage.trim())) {
      return 'Эталонное решение: укажите и язык, и код'
    }
    if (Boolean(form.starterCode.trim()) !== Boolean(form.starterLanguage.trim())) {
      return 'Стартовый код: укажите и язык, и код'
    }
    const weights = groups.filter((group) => group.hidden).map((group) => group.weight ?? 1)
    if (weights.some((weight) => !(Number.isInteger(weight) && weight >= 1 && weight <= 10))) {
      return 'Вес скрытого тест-кейса — целое число от 1 до 10'
    }
  }
  return null
}

export function toPayload(form: TaskForm): AdminTaskWrite {
  const common = {
    kind: form.kind,
    title: form.title.trim(),
    statement: form.statement.trim(),
    specializations: form.specializations,
    grade: form.grade || null,
    skill: form.skill.trim(),
    difficulty: form.difficulty,
    timeLimitMinutes: form.timeLimitMinutes.trim() ? Number(form.timeLimitMinutes) : null,
    variables: form.variables.map((variable) => ({
      name: variable.name,
      min: Number(variable.min),
      max: Number(variable.max),
      step: Number(variable.step) || 1,
    })),
  }
  if (form.kind === 'quiz') {
    const options = form.options.filter((option) => option.text.trim())
    return {
      ...common,
      payload: {
        options: options.map((option) => option.text.trim()),
        correct: options.flatMap((option, index) => (option.correct ? [index] : [])),
        multiple: form.multiple,
      },
    }
  }
  return {
    ...common,
    payload: {
      languages: form.languages
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
      timeLimit: Number(form.runLimitSeconds),
      groups: form.groups.filter((group) => group.expected.trim()),
      reference: form.referenceCode.trim()
        ? { language: form.referenceLanguage.trim(), code: form.referenceCode }
        : null,
      starter: {
        ...form.starterOther,
        ...(form.starterCode.trim() ? { [form.starterLanguage.trim()]: form.starterCode } : {}),
      },
    },
  }
}

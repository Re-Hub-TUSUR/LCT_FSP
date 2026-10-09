import type {
  CodePayloadDto,
  OpenPayloadDto,
  QuizPayloadDto,
  TaskKind,
  TestGroupDto,
} from '@/entities/assessment'

/**
 * Registry of task kinds for the editor: what a new task of the kind starts with, how its form
 * state maps to the stored content and what makes it invalid. The fields themselves live in
 * `ui/kind-fields`. A new kind adds an entry here and a fields component there.
 */

/** The code runner cuts stdout at 999 characters, so a longer expected output can never match. */
export const MAX_EXPECTED_OUTPUT = 900

export type QuizDraft = QuizPayloadDto

export type CodeDraft = {
  languages: string[]
  timeLimit: string
  groups: TestGroupDto[]
  referenceLanguage: string
  referenceCode: string
  /** Compiler id → the program the candidate has to fix; empty code = no starter. */
  starter: Record<string, string>
}

export type OpenDraft = {
  maxLength: string
  guidance: string
}

export type KindDrafts = { quiz: QuizDraft; code: CodeDraft; open: OpenDraft }
type KindPayloads = { quiz: QuizPayloadDto; code: CodePayloadDto; open: OpenPayloadDto }

type KindEditor<K extends TaskKind> = {
  /** «Новая запись: …» */
  label: string
  statementLabel: string
  /** False: the statement is the title (a question is its own name). */
  titled: boolean
  empty: () => KindDrafts[K]
  fromPayload: (payload: KindPayloads[K]) => KindDrafts[K]
  /** First problem that would make the server reject the content, or null. */
  validate: (draft: KindDrafts[K]) => string | null
  toPayload: (draft: KindDrafts[K]) => KindPayloads[K]
}

const filledStarter = (starter: Record<string, string>) =>
  Object.fromEntries(Object.entries(starter).filter(([, code]) => code.trim()))

export const KIND_EDITORS: { [K in TaskKind]: KindEditor<K> } = {
  quiz: {
    label: 'вопрос',
    statementLabel: 'Вопрос',
    titled: false,
    empty: () => ({ options: ['', '', '', ''], correct: [0], multiple: false }),
    fromPayload: (payload) => payload,
    validate: (draft) => {
      if (draft.options.some((option) => !option.trim())) return 'Заполните все варианты ответа'
      if (draft.options.length < 2) return 'Нужно хотя бы два варианта'
      if (draft.correct.length === 0) return 'Отметьте верный вариант'
      if (!draft.multiple && draft.correct.length > 1)
        return 'Несколько верных вариантов возможны только при множественном выборе'
      return null
    },
    toPayload: (draft) => ({ ...draft, options: draft.options.map((option) => option.trim()) }),
  },
  code: {
    label: 'задача на код',
    statementLabel: 'Условие: формат ввода и вывода',
    titled: true,
    empty: () => ({
      languages: [],
      timeLimit: '5',
      groups: [
        { input: '', expected: '', hidden: false },
        { input: '', expected: '', hidden: true },
      ],
      referenceLanguage: 'python-3.14',
      referenceCode: '',
      starter: {},
    }),
    fromPayload: (payload) => ({
      languages: payload.languages,
      timeLimit: String(payload.timeLimit),
      groups: payload.groups,
      referenceLanguage: payload.reference?.language ?? 'python-3.14',
      referenceCode: payload.reference?.code ?? '',
      starter: payload.starter ?? {},
    }),
    validate: (draft) => {
      const limit = Number(draft.timeLimit)
      if (!(limit > 0 && limit <= 20)) return 'Ограничение времени — от 0 до 20 секунд'
      if (draft.groups.some((group) => !group.expected.trim()))
        return 'У каждой группы тестов должен быть ожидаемый вывод'
      if (draft.groups.some((group) => group.expected.length > MAX_EXPECTED_OUTPUT))
        return `Ожидаемый вывод группы — не длиннее ${MAX_EXPECTED_OUTPUT} символов`
      const hidden = draft.groups.filter((group) => group.hidden).length
      if (hidden === 0 || hidden === draft.groups.length)
        return 'Нужна хотя бы одна открытая и одна закрытая группа тестов'
      const weights = draft.groups.filter((group) => group.hidden).map((group) => group.weight ?? 1)
      if (weights.some((weight) => !(Number.isInteger(weight) && weight >= 1 && weight <= 10)))
        return 'Вес закрытой группы — целое число от 1 до 10'
      const started = Object.keys(filledStarter(draft.starter))
      if (draft.languages.length > 0 && started.some((id) => !draft.languages.includes(id)))
        return 'Стартовый код написан на языке, который не разрешён в задаче'
      return null
    },
    toPayload: (draft) => ({
      languages: draft.languages,
      timeLimit: Number(draft.timeLimit),
      groups: draft.groups,
      reference: draft.referenceCode.trim()
        ? { language: draft.referenceLanguage, code: draft.referenceCode }
        : null,
      starter: filledStarter(draft.starter),
    }),
  },
  open: {
    label: 'открытый вопрос',
    statementLabel: 'Вопрос или задание',
    titled: true,
    empty: () => ({ maxLength: '4000', guidance: '' }),
    fromPayload: (payload) => ({
      maxLength: String(payload.maxLength),
      guidance: payload.guidance ?? '',
    }),
    validate: (draft) => {
      const length = Number(draft.maxLength)
      if (!(Number.isInteger(length) && length >= 100 && length <= 20_000))
        return 'Длина ответа — от 100 до 20 000 символов'
      return null
    },
    toPayload: (draft) => ({
      maxLength: Number(draft.maxLength),
      guidance: draft.guidance.trim() || null,
    }),
  },
}

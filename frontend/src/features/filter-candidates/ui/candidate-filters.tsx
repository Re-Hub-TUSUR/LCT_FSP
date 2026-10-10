import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useState } from 'react'
import { candidateApi, candidateKeys, candidateQueries } from '@/entities/candidate'
import type {
  CandidateFiltersDto,
  SavedCandidateSearchDto,
  VacancyPresetDto,
} from '@/entities/candidate'
import { categoryQueries, GRADE_LABELS, GRADES } from '@/entities/category'
import {
  EMPLOYMENT_LABELS,
  EMPLOYMENT_TYPES,
  WORK_FORMAT_LABELS,
  WORK_FORMATS,
} from '@/entities/vacancy'
import { getErrorMessage } from '@/shared/api'
import type { OptionCountDto } from '@/shared/api'
import { formatNumber, plural, resolveTerm, squashTerm, termOptions, toggled } from '@/shared/lib'
import {
  CheckRow,
  CountChip,
  FILTER_TERMS_MAX,
  FilterDeadEnd,
  FilterGroup,
  FilterHead,
  FilterSubLabel,
  ModeSelect,
  MoneyField,
  SaveSearchButton,
  savedCountNote,
  SourceMark,
  TagCombobox,
  UndoToast,
} from '@/shared/ui'
import type { ModeOption, Relaxation, ToastState } from '@/shared/ui'
import {
  ACTIVE_DAYS,
  EMPTY_FILTERS,
  EXPERIENCE_STEPS,
  FSP_DISCIPLINE_SHORT,
  FSP_DISCIPLINES,
  FSP_RESULT_STEPS,
  LOOKING,
  markOf,
  onlyRemote,
  relaxation,
  reverted,
  sameFilters,
} from '../model/filters'
import type { MarkGroup } from '../model/filters'
import { useCandidateFilters } from '../model/use-candidate-filters'

const CANDIDATES = ['кандидат', 'кандидата', 'кандидатов'] as const
const FREE = 'free'
// Mode ids of saved searches: `saved:<id>`.
const SAVED = 'saved:'
const SUGGESTIONS = 5
// Required skills leaving this few candidates deserve a hint to move some to «nice to have».
const FEW = 5

const countIn = (options: OptionCountDto[] | undefined, value: string) =>
  options?.find((option) => option.value === value)?.count

function presetSubtitle(preset: VacancyPresetDto): string {
  const place =
    preset.workFormat === 'remote'
      ? WORK_FORMAT_LABELS.remote
      : `${preset.city ? `${preset.city} · ` : ''}${WORK_FORMAT_LABELS[preset.workFormat].toLowerCase()}`
  return `${place} · до ${formatNumber(preset.salaryTo)} ₽`
}

/**
 * The recruiter's filters (the «Фильтры рекрутерам» mockup): every option shows how many
 * candidates it leaves, a vacancy fills the filters in from its requirements, an empty list
 * suggests what to loosen. The state lives in the URL.
 */
export function CandidateFilters() {
  const {
    filters,
    vacancyId,
    savedId,
    text,
    view,
    snapshot,
    active,
    query,
    setFilters,
    setSaved,
    restore,
  } = useCandidateFilters()
  const [toast, setToast] = useState<ToastState>(null)
  const closeToast = useCallback(() => setToast(null), [])

  const dictionary = useQuery(categoryQueries.dictionary())
  const presets = useQuery(candidateQueries.presets(view))
  const facets = useQuery({
    ...candidateQueries.facets({ ...query, q: text || undefined, view }),
    placeholderData: keepPreviousData,
  })
  const counts = facets.data
  const savedSearches = useQuery(candidateQueries.savedSearches())
  const preset = presets.data?.vacancies.find((item) => item.vacancyId === vacancyId) ?? null
  const savedSearch = savedSearches.data?.find((item) => item.id === savedId) ?? null
  // What the filters were filled in from: an opened saved search, otherwise the vacancy.
  const origin = savedSearch
    ? { filters: savedSearch.filters, source: 'из поиска', count: savedSearch.count }
    : preset
      ? { filters: preset.filters, source: 'из вакансии', count: preset.count }
      : null
  const presetFilters = origin?.filters ?? null

  const queryClient = useQueryClient()
  const refreshSaved = () =>
    queryClient.invalidateQueries({ queryKey: candidateKeys.savedSearches() })
  const save = useMutation({ mutationFn: candidateApi.saveSearch })
  // Opened: the list and its counts show the new candidates, the search marks them seen.
  const open = useMutation({
    mutationFn: candidateApi.openSearch,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: candidateKeys.all }),
  })
  const remove = useMutation({ mutationFn: candidateApi.deleteSearch, onSuccess: refreshSaved })
  const synonyms = dictionary.data?.synonyms ?? []
  const technologies = counts?.stack ?? []
  const specializationLabels = new Map(
    (dictionary.data?.specializations ?? []).map((item) => [item.code, item.label]),
  )

  const change = (patch: Partial<CandidateFiltersDto>) => setFilters({ ...filters, ...patch })

  /** A technology lives in one list only: adding it to one takes it out of the other. */
  const addTechnologies = (list: 'stack' | 'nice', values: string[]) => {
    const other = list === 'stack' ? 'nice' : 'stack'
    const fresh = values.filter((value) => !filters[list].includes(value))
    change({
      // The API takes at most FILTER_TERMS_MAX technologies a list; more would be a 422.
      [list]: [...filters[list], ...fresh].slice(0, FILTER_TERMS_MAX),
      [other]: filters[other].filter((value) => !values.includes(value)),
    })
  }

  const undoable = (message: string, apply: () => void, worthUndo = true) => {
    const before = snapshot
    apply()
    setToast({ message, undo: worthUndo ? () => restore(before) : undefined })
  }

  const pickMode = (id: string) => {
    const hadSomething = active > 0 || vacancyId !== null || savedId !== null
    if (id.startsWith(SAVED)) {
      const search = savedSearches.data?.find((item) => `${SAVED}${item.id}` === id)
      if (!search) return
      undoable(
        'Фильтры из сохранённого поиска',
        () =>
          setFilters(search.filters, {
            vacancyId: search.vacancyId,
            text: search.text,
            saved: search.id,
          }),
        hadSomething,
      )
      // Opened: its new candidates are seen now.
      open.mutate(search.id)
      return
    }
    if (id === FREE) {
      undoable(
        'Вакансия снята, фильтры очищены',
        () => setFilters(EMPTY_FILTERS, { vacancyId: null, saved: null }),
        hadSomething,
      )
      return
    }
    const chosen = presets.data?.vacancies.find((item) => item.vacancyId === id)
    if (chosen) {
      undoable(
        'Фильтры заполнены из вакансии',
        () => setFilters(chosen.filters, { vacancyId: id, saved: null }),
        hadSomething,
      )
    }
  }

  const reset = () =>
    presetFilters
      ? undoable(
          savedSearch
            ? 'Фильтры возвращены к сохранённому поиску'
            : 'Фильтры возвращены к вакансии',
          () => setFilters(presetFilters),
        )
      : undoable('Фильтры сброшены', () => setFilters(EMPTY_FILTERS))

  const sameSearch = (search: SavedCandidateSearchDto) =>
    sameFilters(search.filters, filters) &&
    (search.text ?? '') === text &&
    (search.vacancyId ?? null) === vacancyId
  const alreadySaved = (savedSearches.data ?? []).some(sameSearch)

  const saveCurrent = () =>
    save.mutate(
      { filters, text: text || null, vacancyId },
      {
        onSuccess: (created) => {
          void refreshSaved()
          setSaved(created.id)
          setToast({ message: 'Поиск сохранён' })
        },
      },
    )

  const deleteCurrent = (search: SavedCandidateSearchDto) =>
    remove.mutate(search.id, {
      onSuccess: () => {
        setSaved(null)
        setToast({ message: `Поиск «${search.title}» удалён` })
      },
    })

  const mark = (group: MarkGroup) => (
    <SourceMark
      state={markOf(group, filters, presetFilters)}
      source={origin?.source ?? 'из вакансии'}
      onRevert={() => presetFilters && setFilters(reverted(group, filters, presetFilters))}
    />
  )

  const vacancies = presets.data?.vacancies ?? []
  const modes: ModeOption[] = [
    {
      id: FREE,
      title: 'Свободный поиск',
      subtitle: 'Без вакансии · по силе профиля',
      note: presets.data ? `${presets.data.total} всего` : undefined,
    },
    ...vacancies.map((item) => ({
      id: item.vacancyId,
      title: item.published ? item.title : `${item.title} (черновик)`,
      subtitle: presetSubtitle(item),
      note: `${item.count} ${plural(item.count, ['подходит', 'подходят', 'подходят'])}`,
      section: 'Мои вакансии',
    })),
  ]
  modes.push(
    ...(savedSearches.data ?? []).map((item) => ({
      id: `${SAVED}${item.id}`,
      title: item.title,
      subtitle: item.summary,
      note:
        item.newCount > 0
          ? `+${item.newCount} новых`
          : savedCountNote(item.id === savedId, item.count, counts?.count, view, CANDIDATES),
      fresh: item.newCount > 0,
      section: 'Сохранённые поиски',
    })),
  )
  // A mode opened by a link before its data loaded is still the current one.
  const mode = savedId ? `${SAVED}${savedId}` : (vacancyId ?? FREE)
  if (!modes.some((item) => item.id === mode)) {
    modes.push(
      savedId
        ? { id: mode, title: 'Сохранённый поиск', subtitle: 'Загружаем…' }
        : { id: mode, title: 'Подбор под вакансию', subtitle: 'По совпадению' },
    )
  }

  const dirty = presetFilters ? !sameFilters(filters, presetFilters) : active > 0
  const chosenTechnologies = new Set([...filters.stack, ...filters.nice].map(squashTerm))
  const suggestions =
    counts && counts.count > 0
      ? technologies
          .filter((item) => item.count > 0 && !chosenTechnologies.has(squashTerm(item.value)))
          .slice(0, SUGGESTIONS)
      : []
  const fewLeft =
    counts !== undefined && filters.stack.length >= 2 && counts.count > 0 && counts.count <= FEW

  const relaxations: Relaxation[] = (counts?.relaxations ?? []).flatMap((item) => {
    const loosened = relaxation(item, filters)
    if (!loosened) return []
    return [
      {
        key: `${item.kind}:${item.value ?? ''}`,
        label: loosened.label,
        gain: item.count,
        apply: () => setFilters(loosened.next),
      },
    ]
  })

  return (
    <>
      <FilterHead
        active={active}
        resetLabel={
          dirty
            ? savedSearch
              ? 'Вернуть из поиска'
              : presetFilters
                ? 'Вернуть из вакансии'
                : 'Сбросить'
            : null
        }
        onReset={reset}
        count={
          counts && (
            <>
              {counts.count}{' '}
              <small>
                {plural(counts.count, CANDIDATES)} из {counts.total}
              </small>
            </>
          )
        }
      />

      <div className="filters-group">
        <ModeSelect
          label="Подбор под вакансию"
          options={modes}
          value={mode}
          onChange={pickMode}
          searchPlaceholder="Найти вакансию или поиск"
          emptyText="Ничего не найдено"
          accented={mode !== FREE}
        />
        {savedSearch ? (
          <p className="filters-saved-note">
            О новых подходящих кандидатах придёт уведомление.
            <button
              type="button"
              className="filters-link"
              disabled={remove.isPending}
              onClick={() => deleteCurrent(savedSearch)}
            >
              Удалить поиск
            </button>
          </p>
        ) : (
          vacancies.length > 0 && (
            <p className="filters-hint">
              {vacancyId
                ? 'Фильтры заполнены из вакансии, кандидаты отсортированы по совпадению.'
                : 'Выберите вакансию — фильтры заполнятся из её требований.'}
            </p>
          )
        )}
      </div>

      {counts?.count === 0 && (
        <FilterDeadEnd
          title="Никто не подходит"
          relaxations={relaxations}
          fallback={
            origin
              ? {
                  key: 'preset',
                  label: savedSearch ? 'Вернуть фильтры из поиска' : 'Вернуть фильтры из вакансии',
                  gain: origin.count,
                  apply: () => setFilters(origin.filters),
                }
              : {
                  key: 'reset',
                  label: 'Сбросить все фильтры',
                  gain: counts.total,
                  apply: () => setFilters(EMPTY_FILTERS),
                }
          }
        />
      )}

      <FilterGroup label="Специализация" aside={mark('specializations')}>
        <TagCombobox
          label="Специализация"
          placeholder="Все специализации"
          values={filters.specializations}
          tagLabel={(code) => specializationLabels.get(code) ?? code}
          options={(typed) =>
            (dictionary.data?.specializations ?? [])
              .filter(
                (item) =>
                  !filters.specializations.includes(item.code) &&
                  item.label.toLowerCase().includes(typed.toLowerCase()),
              )
              .map((item) => ({
                value: item.code,
                label: item.label,
                count: countIn(counts?.specializations, item.code),
              }))
              // oxlint-disable-next-line unicorn/no-array-sort -- a fresh array; toSorted() needs ES2023
              .sort((a, b) => (b.count ?? 0) - (a.count ?? 0))
          }
          onAdd={(values) =>
            change({ specializations: [...new Set([...filters.specializations, ...values])] })
          }
          onRemove={(value) =>
            change({ specializations: filters.specializations.filter((item) => item !== value) })
          }
          emptyText="Ничего не найдено"
        />
      </FilterGroup>

      <FilterGroup label="Грейд" aside={mark('grades')}>
        <div className="feed__chips">
          {GRADES.map((grade) => {
            const count = countIn(counts?.grades, grade)
            return (
              <CountChip
                key={grade}
                active={filters.grades.includes(grade)}
                count={count}
                empty={count === 0}
                onClick={() => change({ grades: toggled(filters.grades, grade) })}
              >
                {GRADE_LABELS[grade]}
              </CountChip>
            )
          })}
        </div>
        <CheckRow
          checked={filters.verifiedOnly}
          count={filters.verifiedOnly ? null : counts?.verified}
          onChange={(checked) => change({ verifiedOnly: checked })}
        >
          Грейд подтверждён тестом
        </CheckRow>
        <CheckRow
          checked={filters.hasFsp === true}
          count={filters.hasFsp === true ? null : counts?.fsp}
          onChange={(checked) =>
            change(
              checked ? { hasFsp: true } : { hasFsp: null, fspResult: null, fspDiscipline: null },
            )
          }
        >
          Есть результаты ФСП
        </CheckRow>
        {filters.hasFsp === true && (
          <div className="filters-nested">
            <FilterSubLabel>Лучший результат</FilterSubLabel>
            <div className="feed__chips">
              {FSP_RESULT_STEPS.map((step) => {
                const count = step.value ? countIn(counts?.fspResults, step.value) : undefined
                return (
                  <CountChip
                    key={step.label}
                    active={filters.fspResult === step.value}
                    count={count}
                    empty={count === 0}
                    onClick={() => change({ fspResult: step.value })}
                  >
                    {step.label}
                  </CountChip>
                )
              })}
            </div>
            <FilterSubLabel>Дисциплина</FilterSubLabel>
            <div className="feed__chips">
              <CountChip
                active={filters.fspDiscipline === null}
                onClick={() => change({ fspDiscipline: null })}
              >
                Любая
              </CountChip>
              {FSP_DISCIPLINES.map((discipline) => {
                const count = countIn(counts?.fspDisciplines, discipline)
                return (
                  <CountChip
                    key={discipline}
                    active={filters.fspDiscipline === discipline}
                    count={count}
                    empty={count === 0}
                    onClick={() => change({ fspDiscipline: discipline })}
                  >
                    {FSP_DISCIPLINE_SHORT[discipline]}
                  </CountChip>
                )
              })}
            </div>
          </div>
        )}
      </FilterGroup>

      <FilterGroup label="Коммерческий стаж" aside={mark('experience')}>
        <div className="feed__chips">
          {EXPERIENCE_STEPS.map((step) => {
            const count = step.value ? countIn(counts?.experience, String(step.value)) : undefined
            return (
              <CountChip
                key={step.label}
                active={filters.experienceMin === step.value}
                count={count}
                empty={count === 0}
                onClick={() => change({ experienceMin: step.value })}
              >
                {step.label}
              </CountChip>
            )
          })}
        </div>
      </FilterGroup>

      <FilterGroup label="Стек" aside={mark('stack')}>
        <FilterSubLabel hint="отсекает остальных">Обязательно</FilterSubLabel>
        <TagCombobox
          label="Обязательный стек"
          placeholder="Например, Python"
          values={filters.stack}
          options={(typed) =>
            termOptions(technologies, typed, [...filters.stack, ...filters.nice], synonyms)
          }
          resolve={(typed) => resolveTerm(technologies, typed, synonyms)}
          onAdd={(values) => addTechnologies('stack', values)}
          onRemove={(value) => change({ stack: filters.stack.filter((item) => item !== value) })}
          move={{
            symbol: '↓',
            title: 'Перенести в «Будет плюсом»',
            onMove: (value) => addTechnologies('nice', [value]),
          }}
          emptyText="Нет в словаре технологий"
        />
        <FilterSubLabel hint="поднимает выше в выдаче">Будет плюсом</FilterSubLabel>
        <TagCombobox
          label="Желательный стек"
          placeholder="Например, Docker"
          values={filters.nice}
          options={(typed) =>
            termOptions(technologies, typed, [...filters.stack, ...filters.nice], synonyms)
          }
          resolve={(typed) => resolveTerm(technologies, typed, synonyms)}
          onAdd={(values) => addTechnologies('nice', values)}
          onRemove={(value) => change({ nice: filters.nice.filter((item) => item !== value) })}
          move={{
            symbol: '↑',
            title: 'Сделать обязательным',
            onMove: (value) => addTechnologies('stack', [value]),
          }}
          soft
          emptyText="Нет в словаре технологий"
        />
        {suggestions.length > 0 && (
          <div className="filters-suggest">
            <p>Часто встречается у подходящих кандидатов:</p>
            {suggestions.map((item) => (
              <button
                key={item.value}
                type="button"
                title="Добавить в «Будет плюсом»"
                onClick={() => addTechnologies('nice', [item.value])}
              >
                + {item.value}
                <span>{item.count}</span>
              </button>
            ))}
          </div>
        )}
        {fewLeft && (
          <p className="filters-warn">
            Обязательные навыки оставили {counts.count} {plural(counts.count, CANDIDATES)}. Часть
            можно перенести в «Будет плюсом» кнопкой ↓ на навыке.
          </p>
        )}
      </FilterGroup>

      <FilterGroup label="Зарплатные ожидания, ₽" aside={mark('salary')}>
        <div className="filters-pair">
          <MoneyField
            label="Зарплатные ожидания от"
            prefix="от"
            placeholder="0"
            value={filters.salaryMin}
            onChange={(value) => change({ salaryMin: value })}
          />
          <MoneyField
            label="Зарплатные ожидания до"
            prefix="до"
            placeholder="любые"
            value={filters.salaryMax}
            onChange={(value) => change({ salaryMax: value })}
          />
        </div>
        <p className="filters-hint">В месяц, на руки</p>
        {filters.salaryMin !== null &&
          filters.salaryMax !== null &&
          filters.salaryMin > filters.salaryMax && (
            <p className="filters-error">«От» больше, чем «до» — никто не попадёт в диапазон</p>
          )}
      </FilterGroup>

      <FilterGroup label="Формат" aside={mark('formats')}>
        <div className="feed__chips">
          {WORK_FORMATS.map((format) => {
            const count = countIn(counts?.workFormats, format)
            return (
              <CountChip
                key={format}
                active={filters.workFormats.includes(format)}
                count={count}
                empty={count === 0}
                onClick={() => change({ workFormats: toggled(filters.workFormats, format) })}
              >
                {WORK_FORMAT_LABELS[format]}
              </CountChip>
            )
          })}
        </div>
      </FilterGroup>

      {!onlyRemote(filters) && (
        <FilterGroup
          label="Город"
          aside={
            <>
              {filters.workFormats.includes('remote') && <span>для офиса и гибрида</span>}
              {mark('location')}
            </>
          }
        >
          <TagCombobox
            label="Город"
            placeholder="Любой город"
            values={filters.cities}
            options={(typed) => termOptions(counts?.cities ?? [], typed, filters.cities)}
            resolve={(typed) => resolveTerm(counts?.cities ?? [], typed)}
            onAdd={(values) => change({ cities: [...new Set([...filters.cities, ...values])] })}
            onRemove={(value) =>
              change({ cities: filters.cities.filter((item) => item !== value) })
            }
            emptyText="Ничего не найдено"
          />
          <CheckRow
            checked={filters.relocation}
            count={filters.relocation ? null : counts?.relocation}
            onChange={(checked) => change({ relocation: checked })}
          >
            + готовые к переезду
          </CheckRow>
        </FilterGroup>
      )}

      <FilterGroup label="Занятость" aside={mark('employment')}>
        <div className="feed__chips">
          {EMPLOYMENT_TYPES.map((kind) => {
            const count = countIn(counts?.employmentTypes, kind)
            return (
              <CountChip
                key={kind}
                active={filters.employmentTypes.includes(kind)}
                count={count}
                empty={count === 0}
                onClick={() => change({ employmentTypes: toggled(filters.employmentTypes, kind) })}
              >
                {EMPLOYMENT_LABELS[kind]}
              </CountChip>
            )
          })}
        </div>
      </FilterGroup>

      <FilterGroup label="Готовность к работе">
        <div className="feed__chips">
          {LOOKING.map((status) => {
            const count = countIn(counts?.jobStatuses, status.value)
            return (
              <CountChip
                key={status.value}
                active={filters.jobStatuses.includes(status.value)}
                count={count}
                empty={count === 0}
                onClick={() => change({ jobStatuses: toggled(filters.jobStatuses, status.value) })}
              >
                {status.label}
              </CountChip>
            )
          })}
        </div>
        <CheckRow
          checked={filters.activeDays !== null}
          count={filters.activeDays !== null ? null : counts?.active}
          onChange={(checked) => change({ activeDays: checked ? ACTIVE_DAYS : null })}
        >
          Активность за последние {ACTIVE_DAYS} дней
        </CheckRow>
      </FilterGroup>

      <SaveSearchButton
        saved={alreadySaved}
        pending={save.isPending}
        onSave={saveCurrent}
        hint="Пришлём уведомление, когда появятся новые подходящие кандидаты"
        error={save.isError ? getErrorMessage(save.error) : null}
      />

      <UndoToast toast={toast} onClose={closeToast} />
    </>
  )
}

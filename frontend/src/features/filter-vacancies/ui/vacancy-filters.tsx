import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { categoryQueries } from '@/entities/category'
import {
  BENEFIT_LABELS,
  BENEFITS,
  EMPLOYMENT_LABELS,
  EMPLOYMENT_TYPES,
  vacancyQueries,
  WORK_FORMAT_LABELS,
  WORK_FORMATS,
} from '@/entities/vacancy'
import type { FeedMode, VacancyFiltersDto } from '@/entities/vacancy'
import type { OptionCountDto } from '@/shared/api'
import { plural, resolveTerm, termOptions, toggled } from '@/shared/lib'
import {
  CheckRow,
  CountChip,
  FilterDeadEnd,
  FilterDisclosure,
  FilterGroup,
  FilterHead,
  FilterSubLabel,
  ModeSelect,
  MoneyField,
  SourceMark,
  TagCombobox,
} from '@/shared/ui'
import type { ModeOption, Relaxation } from '@/shared/ui'
import {
  EMPTY_FILTERS,
  markOf,
  onlyRemote,
  relaxation,
  reverted,
  sameFilters,
} from '../model/filters'
import type { MarkGroup } from '../model/filters'
import { useVacancyFilters } from '../model/use-vacancy-filters'

const VACANCIES = ['вакансия', 'вакансии', 'вакансий'] as const

const countIn = (options: OptionCountDto[] | undefined, value: string) =>
  options?.find((option) => option.value === value)?.count

/**
 * The candidate's filters (the «Фильтры кандидатам» mockup): the feed starts from the profile or
 * from every vacancy, options show how many vacancies they add, an empty feed suggests what to
 * loosen. The state lives in the URL.
 */
export function VacancyFilters() {
  const { filters, mode, view, active, query, setFilters } = useVacancyFilters()
  const presets = useQuery(vacancyQueries.feedPresets(view))
  const facets = useQuery({
    ...vacancyQueries.feedFacets({ ...query, view }),
    placeholderData: keepPreviousData,
  })
  const dictionary = useQuery(categoryQueries.dictionary())
  const counts = facets.data
  const synonyms = dictionary.data?.synonyms ?? []
  const technologies = counts?.stack ?? []

  // Unknown yet: the backend matches the profile by default.
  const personalized = presets.data?.personalized !== false
  const current: FeedMode = personalized ? mode : 'free'
  const profile = presets.data?.profile ?? null
  const preset = current === 'profile' ? profile : null

  const change = (patch: Partial<VacancyFiltersDto>) => setFilters({ ...filters, ...patch })

  const addTechnologies = (list: 'stack' | 'nice', values: string[]) => {
    const other = list === 'stack' ? 'nice' : 'stack'
    const fresh = values.filter((value) => !filters[list].includes(value))
    change({
      [list]: [...filters[list], ...fresh],
      [other]: filters[other].filter((value) => !values.includes(value)),
    })
  }

  const pickMode = (id: string) =>
    id === 'profile'
      ? setFilters(profile ?? EMPTY_FILTERS, 'profile')
      : setFilters(EMPTY_FILTERS, 'free')

  const mark = (group: MarkGroup) => (
    <SourceMark
      state={markOf(group, filters, preset)}
      source="из профиля"
      onRevert={() => preset && setFilters(reverted(group, filters, preset))}
    />
  )

  /** «+3» next to an option: how many vacancies adding it brings, once the group narrows. */
  const gain = (
    options: OptionCountDto[] | undefined,
    value: string,
    chosen: readonly string[],
  ) => {
    if (!counts || chosen.length === 0 || chosen.includes(value)) return undefined
    const added = (countIn(options, value) ?? counts.count) - counts.count
    return added > 0 ? `+${added}` : undefined
  }

  const modes: ModeOption[] = [
    ...(personalized
      ? [
          {
            id: 'profile',
            title: 'Подбор по профилю',
            subtitle: `${presets.data?.category?.label ?? 'Ваш профиль'} · по совпадению`,
            note: presets.data
              ? `${presets.data.profileCount} ${plural(presets.data.profileCount, ['подходит', 'подходят', 'подходят'])}`
              : undefined,
          },
        ]
      : []),
    {
      id: 'free',
      title: 'Свободный поиск',
      subtitle: 'Все вакансии · по дате',
      note: presets.data ? `${presets.data.freeCount} всего` : undefined,
    },
  ]

  const dirty = preset ? !sameFilters(filters, preset) : active > 0
  const relaxations: Relaxation[] = (counts?.relaxations ?? []).flatMap((item) => {
    const loosened = relaxation(item, filters)
    if (!loosened) return []
    return [
      {
        key: `${item.kind}:${item.value ?? ''}`,
        label: loosened.label,
        gain: item.count,
        apply: () => setFilters(loosened.next, loosened.mode),
      },
    ]
  })
  const conditions = filters.benefits.length + (filters.accredited ? 1 : 0)

  return (
    <>
      <FilterHead
        active={active}
        resetLabel={dirty ? (preset ? 'Вернуть из профиля' : 'Сбросить') : null}
        onReset={() => setFilters(preset ?? EMPTY_FILTERS)}
        count={
          counts && (
            <>
              {counts.count} <small>{plural(counts.count, VACANCIES)}</small>
            </>
          )
        }
      />

      <ModeSelect
        label="Основа ленты"
        options={modes}
        value={current}
        onChange={pickMode}
        searchPlaceholder="Найти поиск"
        emptyText="Ничего не найдено"
        accented={current === 'profile'}
      />

      {counts?.count === 0 && (
        <FilterDeadEnd
          title="Нет вакансий по этим фильтрам"
          relaxations={relaxations}
          fallback={
            preset
              ? {
                  key: 'profile',
                  label: 'Вернуть фильтры из профиля',
                  gain: presets.data?.profileCount ?? 0,
                  apply: () => setFilters(preset),
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

      <FilterGroup label="Зарплата от, ₽" aside={mark('salary')}>
        <MoneyField
          label="Зарплата от"
          placeholder="Например, 60 000"
          value={filters.salaryMin}
          onChange={(value) => change({ salaryMin: value })}
        />
        <p className="filters-hint">В месяц, на руки</p>
      </FilterGroup>

      <FilterGroup label="Формат" aside={mark('formats')}>
        <div className="feed__chips">
          {WORK_FORMATS.map((format) => (
            <CountChip
              key={format}
              active={filters.workFormats.includes(format)}
              count={gain(counts?.workFormats, format, filters.workFormats)}
              onClick={() => change({ workFormats: toggled(filters.workFormats, format) })}
            >
              {WORK_FORMAT_LABELS[format]}
            </CountChip>
          ))}
        </div>
      </FilterGroup>

      {!onlyRemote(filters) && (
        <FilterGroup
          label="Город"
          aside={
            <>
              <span>для офиса и гибрида</span>
              {mark('location')}
            </>
          }
        >
          <TagCombobox
            label="Город"
            placeholder="Например, Москва"
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
            onChange={(checked) => change({ relocation: checked })}
          >
            + вакансии с помощью при переезде
          </CheckRow>
        </FilterGroup>
      )}

      <FilterGroup label="Занятость" aside={mark('employment')}>
        <div className="feed__chips">
          {EMPLOYMENT_TYPES.map((kind) => (
            <CountChip
              key={kind}
              active={filters.employmentTypes.includes(kind)}
              count={gain(counts?.employmentTypes, kind, filters.employmentTypes)}
              onClick={() => change({ employmentTypes: toggled(filters.employmentTypes, kind) })}
            >
              {EMPLOYMENT_LABELS[kind]}
            </CountChip>
          ))}
        </div>
      </FilterGroup>

      <FilterGroup label="Стек" aside={mark('stack')}>
        <FilterSubLabel hint="отсекает остальные">Обязательно</FilterSubLabel>
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
          emptyText="Ничего не найдено"
        />
        <FilterSubLabel hint="поднимает выше в ленте">Будет плюсом</FilterSubLabel>
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
          emptyText="Ничего не найдено"
        />
      </FilterGroup>

      <FilterDisclosure title="Условия" chosen={conditions}>
        {BENEFITS.map((benefit) => (
          <CheckRow
            key={benefit}
            checked={filters.benefits.includes(benefit)}
            count={countIn(counts?.benefits, benefit)}
            onChange={() => change({ benefits: toggled(filters.benefits, benefit) })}
          >
            {BENEFIT_LABELS[benefit]}
          </CheckRow>
        ))}
        <CheckRow
          checked={filters.accredited}
          count={counts?.accredited}
          onChange={(checked) => change({ accredited: checked })}
        >
          Аккредитованная IT-компания
        </CheckRow>
      </FilterDisclosure>
    </>
  )
}

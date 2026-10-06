import { useId, useState } from 'react'
import { suggestSkills } from '../model/skills'

type Props = {
  id: string
  label: string
  catalog: readonly string[]
  value: string[]
  error?: string
  onChange: (next: string[]) => void
}

export function SkillField({ id, label, catalog, value, error, onChange }: Props) {
  const listId = useId()
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const matches = suggestSkills(catalog, query, value)

  const add = (skill: string) => {
    const next = skill.trim().replace(/\s+/g, ' ')
    if (!next || next.length > 40) return
    if (value.some((item) => item.toLocaleLowerCase('ru') === next.toLocaleLowerCase('ru'))) return
    onChange([...value, next])
    setQuery('')
  }

  return (
    <div className="skills">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      {value.length > 0 && (
        <ul className="skills__chosen" aria-label={`Выбранные: ${label}`}>
          {value.map((skill) => (
            <li key={skill}>
              <button
                type="button"
                className="skills__chip"
                onClick={() => onChange(value.filter((item) => item !== skill))}
              >
                {skill}
                <span className="skills__remove" aria-hidden="true">
                  ×
                </span>
                <span className="skills__sr">Убрать {skill}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <input
        id={id}
        className="field__input"
        autoComplete="off"
        value={query}
        placeholder="Начните вводить, например pyth"
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onChange={(event) => {
          setQuery(event.target.value)
          setOpen(true)
        }}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault()
            const typed = query.trim()
            const exact = matches.find(
              (item) => item.toLocaleLowerCase('ru') === typed.toLocaleLowerCase('ru'),
            )
            if (exact) add(exact)
            else if (matches[0] && typed) add(matches[0])
            else if (typed) add(typed)
          }
        }}
      />
      {!query.trim() && matches.length > 0 && (
        <ul className="skills__popular" aria-label="Готовые навыки">
          {matches.map((skill) => (
            <li key={skill}>
              <button type="button" className="skills__suggest" onClick={() => add(skill)}>
                {skill}
              </button>
            </li>
          ))}
        </ul>
      )}
      {query.trim() && open && matches.length > 0 && (
        <ul id={listId} className="skills__list">
          {matches.map((skill) => (
            <li key={skill}>
              <button
                type="button"
                className="skills__option"
                onMouseDown={(event) => {
                  event.preventDefault()
                  add(skill)
                }}
              >
                {skill}
              </button>
            </li>
          ))}
        </ul>
      )}
      {error && (
        <p className="field__error" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

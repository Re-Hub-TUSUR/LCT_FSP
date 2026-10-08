import { Link } from 'react-router'
import type { TodoItem } from '../../lib/todos'

export type { TodoItem }

/** Open items first; finished ones stay visible so the list explains the progress. */
export function TodoList({ items }: { items: TodoItem[] }) {
  const ordered = [...items.filter((item) => !item.done), ...items.filter((item) => item.done)]
  return (
    <ul className="todo-list">
      {ordered.map((item, index) => (
        <li key={item.id}>
          <Link to={item.to} className={item.done ? 'is-done' : undefined}>
            <span className="todo-list__num" aria-hidden="true">
              {String(index + 1).padStart(2, '0')}
            </span>
            <span className="todo-list__label">{item.label}</span>
            <span className="todo-list__box" aria-hidden="true">
              {item.done ? '✓' : ''}
            </span>
            <span className="visually-hidden">{item.done ? 'Готово' : 'Сделать'}</span>
          </Link>
        </li>
      ))}
    </ul>
  )
}

import { Link } from 'react-router'

export type TodoItem = { id: string; label: string; done: boolean; to: string }

/** Open items first; finished ones stay visible so the list explains the progress. */
export function TodoList({ items }: { items: TodoItem[] }) {
  const ordered = [...items.filter((item) => !item.done), ...items.filter((item) => item.done)]
  return (
    <ul className="todo-list">
      {ordered.map((item) => (
        <li key={item.id}>
          <Link to={item.to} className={item.done ? 'is-done' : undefined}>
            <span>{item.label}</span>
            <span className="cabinet-time">{item.done ? 'Готово' : 'Сделать'}</span>
          </Link>
        </li>
      ))}
    </ul>
  )
}

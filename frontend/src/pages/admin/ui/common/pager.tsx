type Props = {
  page: number
  pages: number
  total: number
  onPage: (page: number) => void
}

/** Server-side pages of 50 rows: 1 … 4 5 6 … 12. */
export function Pager({ page, pages, total, onPage }: Props) {
  const shown = Array.from({ length: pages }, (_, i) => i + 1).filter(
    (n) => n === 1 || n === pages || Math.abs(n - page) <= 1,
  )
  const items: (number | 'gap')[] = []
  shown.forEach((n, i) => {
    if (i > 0 && n - shown[i - 1]! > 1) items.push('gap')
    items.push(n)
  })

  return (
    <nav className="pager" aria-label="Страницы">
      <p className="pager__total">Всего: {total}</p>
      {pages > 1 && (
        <div className="pager__pages">
          <button type="button" disabled={page <= 1} onClick={() => onPage(page - 1)}>
            ←<span className="visually-hidden">Предыдущая</span>
          </button>
          {items.map((item, i) =>
            item === 'gap' ? (
              <span key={`gap-${i}`} className="pager__gap">
                …
              </span>
            ) : (
              <button
                key={item}
                type="button"
                aria-current={item === page ? 'page' : undefined}
                className={item === page ? 'is-current' : undefined}
                onClick={() => onPage(item)}
              >
                {item}
              </button>
            ),
          )}
          <button type="button" disabled={page >= pages} onClick={() => onPage(page + 1)}>
            →<span className="visually-hidden">Следующая</span>
          </button>
        </div>
      )}
    </nav>
  )
}

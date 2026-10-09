import type { LegalBlock, LegalCell } from '../model/types'
import { InlineText } from './inline-text'

const LETTERS = 'абвгдежзиклмнопрстуфхцчшщэюя'

export const sectionId = (index: number) => `section-${index + 1}`

function Cell({ content }: { content: LegalCell }) {
  const lines = Array.isArray(content) ? content : [content]
  return (
    <>
      {lines.map((line, index) =>
        line.startsWith('- ') ? (
          <p key={index} className="legal-doc__cell-item">
            <InlineText text={line.slice(2)} />
          </p>
        ) : (
          <p key={index}>
            <InlineText text={line} />
          </p>
        ),
      )}
    </>
  )
}

function Lines({ lines }: { lines: string[] }) {
  return (
    <>
      {lines.map((line, index) =>
        line.startsWith('- ') ? (
          <p key={index} className="legal-doc__item">
            <InlineText text={line.slice(2)} />
          </p>
        ) : (
          <p key={index}>
            <InlineText text={line} />
          </p>
        ),
      )}
    </>
  )
}

/** Position of every top-level heading among the headings, -1 for any other block. */
function sectionIndexes(blocks: LegalBlock[]): number[] {
  let count = 0
  return blocks.map((block) => (block.t === 'h1' ? count++ : -1))
}

/** Every top-level heading gets the anchor (`sectionId`) the contents list points to. */
export function LegalBlocks({ blocks }: { blocks: LegalBlock[] }) {
  const sections = sectionIndexes(blocks)
  return (
    <>
      {blocks.map((block, index) => {
        switch (block.t) {
          case 'h1':
            return (
              <h2 key={index} id={sectionId(sections[index] ?? 0)} className="legal-doc__h1">
                {block.text}
              </h2>
            )
          case 'h2':
            return (
              <h3 key={index} className="legal-doc__h2">
                {block.text}
              </h3>
            )
          case 'p':
            return (
              <p key={index} className="legal-doc__p">
                <InlineText text={block.text} />
              </p>
            )
          case 'c':
            return (
              <p key={index} className="legal-doc__clause">
                <span className="legal-doc__num">{block.num}</span>
                <span>
                  <InlineText text={block.text} />
                </span>
              </p>
            )
          case 'subs':
            return (
              <ol key={index} className="legal-doc__list">
                {block.items.map((item, at) => (
                  <li key={at} data-label={`${LETTERS[at] ?? ''})`}>
                    <InlineText text={item} />
                  </li>
                ))}
              </ol>
            )
          case 'bullets':
            return (
              <ul key={index} className="legal-doc__list legal-doc__list--dash">
                {block.items.map((item, at) => (
                  <li key={at}>
                    <InlineText text={item} />
                  </li>
                ))}
              </ul>
            )
          case 'table':
            return (
              <div key={index} className="legal-doc__table-wrap">
                <table className="legal-doc__table">
                  <colgroup>
                    {block.widths.map((width, at) => (
                      <col key={at} style={{ width: `${width}%` }} />
                    ))}
                  </colgroup>
                  {block.header && (
                    <thead>
                      <tr>
                        {(block.rows[0] ?? []).map((cell, at) => (
                          <th key={at} scope="col">
                            <Cell content={cell} />
                          </th>
                        ))}
                      </tr>
                    </thead>
                  )}
                  <tbody>
                    {block.rows.slice(block.header ? 1 : 0).map((row, at) => (
                      <tr key={at}>
                        {row.map((cell, cellAt) => (
                          <td key={cellAt}>
                            <Cell content={cell} />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          case 'card':
            return (
              <div key={index} className="legal-doc__card">
                <h3 className="legal-doc__h2">{block.title}</h3>
                <div className="legal-doc__table-wrap">
                  <table className="legal-doc__table legal-doc__table--card">
                    <tbody>
                      {block.rows.map(([label, value], at) => (
                        <tr key={at}>
                          <th scope="row">{label}</th>
                          <td>
                            <Cell content={value} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )
          case 'callout':
            return (
              <aside key={index} className="legal-doc__callout">
                <strong className="legal-doc__callout-title">{block.title}</strong>
                <Lines lines={block.lines} />
              </aside>
            )
          case 'break':
            return null
        }
      })}
    </>
  )
}

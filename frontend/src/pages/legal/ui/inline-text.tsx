const TOKEN = /(\*\*[^*]+\*\*|~~[^~]+~~)/g

/** Renders the `**bold**` and `~~italic~~` markup of a legal text. */
export function InlineText({ text }: { text: string }) {
  const parts = text.split(TOKEN).filter(Boolean)
  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>
        if (part.startsWith('~~')) return <em key={index}>{part.slice(2, -2)}</em>
        return part
      })}
    </>
  )
}

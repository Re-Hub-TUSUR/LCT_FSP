import type { ButtonHTMLAttributes, Ref } from 'react'
import { Link } from 'react-router'
import type { LinkProps } from 'react-router'
import './button.css'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'solid' | 'ghost'
  /** `block` stretches to the container width (landing forms), `inline` fits the content. */
  size?: 'block' | 'inline'
  ref?: Ref<HTMLButtonElement>
}

export function Button({
  variant = 'solid',
  size = 'block',
  type = 'button',
  className,
  ref,
  ...rest
}: Props) {
  const classes = ['btn', `btn--${variant}`, size === 'inline' && 'btn--inline', className]
    .filter(Boolean)
    .join(' ')

  return <button ref={ref} type={type} className={classes} {...rest} />
}

type ButtonLinkProps = LinkProps & {
  variant?: 'solid' | 'ghost'
  size?: 'block' | 'inline'
}

/** Same look as `Button`, but a real link: it can be opened, copied and focused. */
export function ButtonLink({
  variant = 'solid',
  size = 'inline',
  className,
  ...rest
}: ButtonLinkProps) {
  const classes = ['btn', `btn--${variant}`, size === 'inline' && 'btn--inline', className]
    .filter(Boolean)
    .join(' ')

  return <Link className={classes} {...rest} />
}

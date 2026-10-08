import type { ButtonHTMLAttributes, Ref } from 'react'
import { Link } from 'react-router'
import type { LinkProps } from 'react-router'
import './button.css'

type Variant = 'solid' | 'ghost' | 'danger'
type Size = 'block' | 'inline' | 'small'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
  /** `block` stretches to the container width (forms), `inline` and `small` fit the content. */
  size?: Size
  ref?: Ref<HTMLButtonElement>
}

const classesOf = (variant: Variant, size: Size, className?: string) =>
  ['btn', `btn--${variant}`, size !== 'block' && `btn--${size}`, className]
    .filter(Boolean)
    .join(' ')

export function Button({
  variant = 'solid',
  size = 'block',
  type = 'button',
  className,
  ref,
  ...rest
}: Props) {
  return <button ref={ref} type={type} className={classesOf(variant, size, className)} {...rest} />
}

type ButtonLinkProps = LinkProps & {
  variant?: Variant
  size?: Size
}

/** Same look as `Button`, but a real link: it can be opened, copied and focused. */
export function ButtonLink({
  variant = 'solid',
  size = 'inline',
  className,
  ...rest
}: ButtonLinkProps) {
  return <Link className={classesOf(variant, size, className)} {...rest} />
}

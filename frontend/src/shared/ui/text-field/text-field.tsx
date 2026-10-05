import type { InputHTMLAttributes, ReactNode, Ref, TextareaHTMLAttributes } from 'react'
import './text-field.css'

type FieldProps = {
  id: string
  label: string
  /** Keeps the label for screen readers only (e.g. a single-field landing form). */
  hideLabel?: boolean
  error?: string
}

function FieldShell({
  id,
  label,
  hideLabel,
  error,
  children,
}: FieldProps & { children: ReactNode }) {
  return (
    <div className="field">
      <label className={hideLabel ? 'visually-hidden' : 'field__label'} htmlFor={id}>
        {label}
      </label>
      {children}
      <p id={`${id}-error`} className="field__error" role="alert">
        {error}
      </p>
    </div>
  )
}

const a11y = (id: string, error?: string) => ({
  'aria-invalid': error ? true : undefined,
  'aria-describedby': error ? `${id}-error` : undefined,
})

type TextFieldProps = FieldProps &
  Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> & { ref?: Ref<HTMLInputElement> }

export function TextField({
  id,
  label,
  hideLabel,
  error,
  className,
  ref,
  ...rest
}: TextFieldProps) {
  return (
    <FieldShell id={id} label={label} hideLabel={hideLabel} error={error}>
      <input
        ref={ref}
        id={id}
        className={['field__input', className].filter(Boolean).join(' ')}
        {...a11y(id, error)}
        {...rest}
      />
    </FieldShell>
  )
}

type TextAreaProps = FieldProps &
  Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'id'> & { ref?: Ref<HTMLTextAreaElement> }

export function TextArea({ id, label, hideLabel, error, className, ref, ...rest }: TextAreaProps) {
  return (
    <FieldShell id={id} label={label} hideLabel={hideLabel} error={error}>
      <textarea
        ref={ref}
        id={id}
        className={['field__input', 'field__input--multiline', className].filter(Boolean).join(' ')}
        {...a11y(id, error)}
        {...rest}
      />
    </FieldShell>
  )
}

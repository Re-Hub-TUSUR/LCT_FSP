import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { companyApi, companyKeys, companyLogoUrl } from '@/entities/company'
import type { CompanyDto } from '@/entities/company'
import { getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui'

const MAX_SIZE = 2 * 1024 * 1024

/** Company logo: JPEG, PNG or WebP up to 2 MB, shown to candidates on the company page. */
export function LogoField({ company }: { company: CompanyDto }) {
  const queryClient = useQueryClient()
  const input = useRef<HTMLInputElement>(null)
  const [version, setVersion] = useState(0)
  const [tooBig, setTooBig] = useState(false)
  const done = (next: CompanyDto) => {
    queryClient.setQueryData(companyKeys.mine(), next)
    setVersion((value) => value + 1)
  }
  const upload = useMutation({ mutationFn: companyApi.uploadLogo, onSuccess: done })
  const remove = useMutation({ mutationFn: companyApi.removeLogo, onSuccess: done })

  const pick = (files: FileList | null) => {
    const file = files?.[0]
    if (input.current) input.current.value = ''
    if (!file) return
    upload.reset()
    setTooBig(file.size > MAX_SIZE)
    if (file.size <= MAX_SIZE) upload.mutate(file)
  }

  return (
    <div className="logo-field">
      <div className="logo-field__preview" aria-hidden={!company.hasLogo}>
        {company.hasLogo ? (
          <img src={companyLogoUrl(company.id, version)} alt={`Логотип ${company.name}`} />
        ) : (
          <span>{company.name.slice(0, 1).toUpperCase()}</span>
        )}
      </div>
      <div className="logo-field__body">
        <p className="logo-field__title">Логотип</p>
        <p className="form-hint">JPEG, PNG или WebP, до 2 МБ. Квадратный смотрится лучше.</p>
        <input
          ref={input}
          className="visually-hidden"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          aria-label="Логотип компании"
          onChange={(event) => pick(event.target.files)}
        />
        <div className="form-actions">
          <Button
            type="button"
            variant="ghost"
            size="inline"
            disabled={upload.isPending}
            onClick={() => input.current?.click()}
          >
            {upload.isPending ? 'Загружаем…' : company.hasLogo ? 'Заменить' : 'Загрузить'}
          </Button>
          {company.hasLogo && (
            <Button
              type="button"
              variant="ghost"
              size="inline"
              disabled={remove.isPending}
              onClick={() => remove.mutate()}
            >
              Удалить
            </Button>
          )}
        </div>
        {tooBig && (
          <p className="form-banner" role="alert">
            Файл больше 2 МБ
          </p>
        )}
        {(upload.isError || remove.isError) && (
          <p className="form-banner" role="alert">
            {getErrorMessage(upload.error ?? remove.error)}
          </p>
        )}
      </div>
    </div>
  )
}

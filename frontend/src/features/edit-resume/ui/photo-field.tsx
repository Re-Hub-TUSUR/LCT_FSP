import { useCandidatePhoto } from '@/entities/candidate'

type Props = {
  candidateId: string | null
  hasPhoto: boolean
  previewUrl: string | null
  error: string
  busy: boolean
  onPick: (file: File) => void
}

export function PhotoField({ candidateId, hasPhoto, previewUrl, error, busy, onPick }: Props) {
  const remote = useCandidatePhoto(candidateId, hasPhoto && !previewUrl)
  const src = previewUrl ?? remote.data ?? null

  return (
    <div className="photo">
      <p className="field__label" id="resume-photo-label">
        Фото
      </p>
      <div className="photo__row">
        {src ? (
          <img className="photo__preview" src={src} alt="Ваше фото" />
        ) : (
          <span className="photo__preview photo__preview--empty" aria-hidden="true" />
        )}
        <div className="photo__copy">
          <label className="btn btn--ghost btn--inline file-btn">
            {busy ? 'Загружаем…' : src ? 'Заменить фото' : 'Добавить фото'}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
              aria-labelledby="resume-photo-label"
              disabled={busy}
              onChange={(event) => {
                const file = event.target.files?.[0]
                event.target.value = ''
                if (file) onPick(file)
              }}
            />
          </label>
          <p className="form-hint">JPEG, PNG или WebP, до 2 МБ.</p>
          {error && (
            <p className="form-banner" role="alert">
              {error}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

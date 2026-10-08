import { useMutation } from '@tanstack/react-query'
import { candidateApi } from '@/entities/candidate'
import { getErrorMessage } from '@/shared/api'
import { downloadBlob } from '@/shared/lib'
import { Button } from '@/shared/ui'
import './download-resume-button.css'

type Props = {
  candidateId: string
  /** For the file name: «Резюме — Марина Крылова.pdf». */
  name: string
}

/** The resume as a PDF file, laid out by the backend in the site's fonts. */
export function DownloadResumeButton({ candidateId, name }: Props) {
  const download = useMutation({
    mutationFn: () => candidateApi.resumePdf(candidateId),
    onSuccess: (blob) => downloadBlob(`Резюме — ${name}.pdf`, blob),
  })

  return (
    <span className="download-resume">
      <Button
        variant="ghost"
        size="small"
        disabled={download.isPending}
        onClick={() => download.mutate()}
      >
        {download.isPending ? 'Готовим PDF…' : 'Скачать резюме PDF'}
      </Button>
      {download.isError && (
        <span className="download-resume__error" role="alert">
          {getErrorMessage(download.error)}
        </span>
      )}
    </span>
  )
}

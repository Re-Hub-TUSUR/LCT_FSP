import { queryOptions } from '@tanstack/react-query'
import { companyKeys } from '@/entities/company'
import { http } from '@/shared/api'

export type VerificationStatus = 'pending' | 'approved' | 'rejected'

export type CompanyVerificationDto = {
  /** Null until the first document is uploaded. */
  status: VerificationStatus | null
  submittedAt: string | null
  decidedAt: string | null
  /** The admin's reason, shown after a rejection. */
  reason: string | null
  documents: {
    id: string
    filename: string
    sizeBytes: number
    uploadedAt: string
    kind: 'pdf' | 'docx'
  }[]
}

export const verificationKeys = { mine: companyKeys.verification() }

export const verificationQueries = {
  mine: () =>
    queryOptions({
      queryKey: verificationKeys.mine,
      queryFn: ({ signal }) =>
        http.get<CompanyVerificationDto>('/companies/me/verification', { signal }),
    }),
}

export const verificationApi = {
  upload: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return http.post<CompanyVerificationDto>('/companies/me/verification/documents', body)
  },
  remove: (documentId: string) =>
    http.delete<CompanyVerificationDto>(`/companies/me/verification/documents/${documentId}`),
}

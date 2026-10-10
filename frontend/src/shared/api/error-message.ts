import { ApiError } from './http'

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'email_not_verified' || error.code === 'too_many_requests') {
      return error.message
    }
    if (error.status === 501) return 'Раздел ещё в разработке.'
    if (error.status === 403) return 'Недостаточно прав для просмотра.'
    if (error.status === 404) return 'Ничего не найдено.'
    // The proxy answers 413 itself, in English, before the API sees the file.
    if (error.status === 413) return 'Файл слишком большой.'
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Что-то пошло не так.'
}

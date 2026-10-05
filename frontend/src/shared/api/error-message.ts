import { ApiError } from './http'

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 501) return 'Раздел ещё в разработке.'
    if (error.status === 403) return 'Недостаточно прав для просмотра.'
    if (error.status === 404) return 'Ничего не найдено.'
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Что-то пошло не так.'
}

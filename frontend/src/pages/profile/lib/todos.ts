import type { OwnCandidateDto } from '@/entities/candidate'
import type { CompanyDto } from '@/entities/company'
import { ROUTES } from '@/shared/config'

export type TodoItem = { id: string; label: string; done: boolean; to: string }

/** What makes a specialist's profile complete: the checklist and the progress bar read it. */
export function candidateTodos(profile: OwnCandidateDto): TodoItem[] {
  return [
    {
      id: 'test',
      label: 'Подтвердить грейд тестом',
      done: profile.assessmentStatus === 'passed',
      to: ROUTES.testing,
    },
    {
      id: 'fsp',
      label: 'Связать профиль с ФСП',
      done: profile.fspLinked,
      to: ROUTES.profileSettings,
    },
    {
      id: 'photo',
      label: 'Добавить фото',
      done: Boolean(profile.hasPhoto),
      to: ROUTES.profileResume,
    },
    {
      id: 'about',
      label: 'Рассказать о себе',
      done: Boolean(profile.about),
      to: ROUTES.profileResume,
    },
    {
      id: 'education',
      label: 'Указать образование',
      done: profile.education.length > 0,
      to: ROUTES.profileResume,
    },
    {
      id: 'github',
      label: 'Добавить ссылку на GitHub',
      done: Boolean(profile.githubUrl),
      to: ROUTES.profileResume,
    },
  ]
}

export function employerTodos(company: CompanyDto, invited: boolean): TodoItem[] {
  return [
    {
      id: 'legal',
      label: 'Заполнить реквизиты',
      done: Boolean(company.inn && company.ogrn && company.legalAddress),
      to: ROUTES.profileCompany,
    },
    {
      id: 'profile',
      label: 'Описать компанию для кандидатов',
      done: Boolean(company.description && company.website),
      to: ROUTES.profileCompany,
    },
    { id: 'logo', label: 'Загрузить логотип', done: company.hasLogo, to: ROUTES.profileCompany },
    {
      id: 'accreditation',
      label: 'Подтвердить IT-аккредитацию',
      done: company.itAccredited,
      to: ROUTES.profileCompany,
    },
    { id: 'invite', label: 'Пригласить первого кандидата', done: invited, to: ROUTES.feed },
  ]
}

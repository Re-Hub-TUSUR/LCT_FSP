/** Grade ladder used for categorisation. Order matters: index = seniority. */
export const GRADES = ['intern', 'junior', 'middle', 'senior', 'lead'] as const

export type Grade = (typeof GRADES)[number]

export const GRADE_LABELS: Record<Grade, string> = {
  intern: 'Стажёр',
  junior: 'Junior',
  middle: 'Middle',
  senior: 'Senior',
  lead: 'Lead',
}

/** Specialization codes come from the backend dictionary; the frontend treats them as opaque. */
export type SpecializationCode = string

/** A category is the pair "specialization + grade", e.g. "backend · middle". */
export type CategoryDto = {
  code: string
  label: string
  specialization: SpecializationCode
  grade: Grade
}

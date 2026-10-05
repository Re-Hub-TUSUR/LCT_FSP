import type { CandidateDto, CandidateMatchDto, CandidateSearchDto } from '../api/candidate-api'

/** Sample cards shown while the search API answers 501 (backend in progress). */
const base: Omit<CandidateDto, 'id' | 'displayName' | 'headline' | 'category' | 'stack'> = {
  about: null,
  gradeVerified: true,
  assessmentScore: 82,
  assessmentStatus: 'passed',
  softSkills: ['Работа в команде', 'Ответственность'],
  experienceYears: 4,
  englishLevel: 'B2',
  city: 'Москва',
  relocationReady: false,
  workFormats: ['remote', 'hybrid'],
  salaryExpectation: 260_000,
  fspAchievements: [],
  fspLinked: false,
  contacts: null,
}

const category = (
  specialization: string,
  label: string,
  grade: 'middle' | 'senior' | 'junior',
) => ({
  code: `${specialization}:${grade}`,
  label,
  specialization,
  grade,
})

export const DEMO_CANDIDATES: CandidateMatchDto[] = [
  {
    candidate: {
      ...base,
      id: 'demo-p1',
      displayName: 'Марина Крылова',
      headline: 'Middle Backend-разработчик (Python)',
      about:
        '5 лет в IT, из них 4 — в агротехе. В фокусе: асинхронные REST API на FastAPI, тесты и CI.',
      category: category('backend', 'Backend-разработка · Middle', 'middle'),
      assessmentScore: 91.4,
      assessmentStatus: 'passed',
      stack: ['Python', 'PostgreSQL', 'FastAPI', 'asyncio', 'gRPC', 'Kafka'],
      fspLinked: true,
      fspAchievements: [
        {
          eventName: 'Чемпионат Москвы по спортивному программированию',
          year: 2025,
          place: 1,
          discipline: 'algorithmic',
          level: 'regional',
        },
      ],
    },
    matchScore: 0.94,
    profileStrength: 0.85,
    reasons: [
      'Грейд подтверждён тестом: 91 из 100',
      'ФСП: 1-е место — Чемпионат Москвы (2025)',
      'Стек вакансии: Python, PostgreSQL, FastAPI (3 из 4)',
      'Ожидания 260 000 ₽ — в пределах вилки',
    ],
    reaction: null,
  },
  {
    candidate: {
      ...base,
      id: 'demo-p2',
      displayName: 'Тимур Кудрявцев',
      headline: 'Senior Go-разработчик',
      category: category('backend', 'Backend-разработка · Senior', 'senior'),
      assessmentScore: 88.1,
      assessmentStatus: 'passed',
      experienceYears: 7,
      salaryExpectation: 390_000,
      city: 'Казань',
      relocationReady: true,
      stack: ['Go', 'PostgreSQL', 'Kafka', 'gRPC', 'ClickHouse', 'Kubernetes'],
      fspLinked: true,
      fspAchievements: [
        {
          eventName: 'Кубок России по спортивному программированию',
          year: 2024,
          place: 2,
          discipline: 'product',
          level: 'national',
        },
      ],
    },
    matchScore: 0.81,
    profileStrength: 0.88,
    reasons: [
      'Грейд подтверждён тестом: 88 из 100',
      'ФСП: 2-е место — Кубок России (2024)',
      'Грейд на ступень выше вакансии',
      'Рассматривает переезд',
    ],
    reaction: 'like',
  },
  {
    candidate: {
      ...base,
      id: 'demo-p3',
      displayName: 'Алина Сафина',
      headline: 'Middle Python-разработчик',
      category: category('backend', 'Backend-разработка · Middle', 'middle'),
      assessmentScore: 76.5,
      assessmentStatus: 'passed',
      experienceYears: 3,
      salaryExpectation: 230_000,
      city: 'Санкт-Петербург',
      stack: ['Python', 'Django', 'PostgreSQL', 'Celery', 'Redis'],
    },
    matchScore: 0.72,
    profileStrength: 0.46,
    reasons: [
      'Грейд подтверждён тестом: 77 из 100',
      'Стек вакансии: Python, PostgreSQL (2 из 4)',
      'Подходит формат: удалённо',
    ],
    reaction: null,
  },
  {
    candidate: {
      ...base,
      id: 'demo-p4',
      displayName: 'Егор Смирнов',
      headline: 'Junior Backend-разработчик (Python)',
      category: category('backend', 'Backend-разработка · Junior', 'junior'),
      gradeVerified: false,
      assessmentScore: null,
      assessmentStatus: 'not_taken',
      experienceYears: 1,
      salaryExpectation: 120_000,
      city: 'Томск',
      stack: ['Python', 'FastAPI', 'Docker', 'PostgreSQL'],
      fspLinked: true,
      fspAchievements: [
        {
          eventName: 'Чемпионат Томской области по спортивному программированию',
          year: 2025,
          place: null,
          discipline: 'product',
          level: 'regional',
        },
      ],
    },
    matchScore: 0.55,
    profileStrength: 0.08,
    reasons: [
      'Грейд указан без теста',
      'ФСП: участие — Чемпионат Томской области (2025)',
      'Стек вакансии: Python, FastAPI, PostgreSQL (3 из 4)',
    ],
    reaction: null,
  },
]

export function demoCandidateSearch(page: number, perPage: number): CandidateSearchDto {
  const start = (page - 1) * perPage
  return {
    items: DEMO_CANDIDATES.slice(start, start + perPage),
    total: DEMO_CANDIDATES.length,
    page,
    perPage,
    pages: Math.ceil(DEMO_CANDIDATES.length / perPage),
    engine: 'elasticsearch',
  }
}

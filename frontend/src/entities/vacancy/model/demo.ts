import type { VacancyFeedDto, VacancyMatchDto } from '../api/vacancy-api'

/**
 * Sample cards shown while the feed API answers 501 (backend in progress).
 * Same shape and wording as the backend demo dataset (backend/app/seed).
 */
const day = (n: number) => new Date(Date.now() - n * 86_400_000).toISOString()

const backend = (grade: 'junior' | 'middle' | 'senior') => ({
  code: `backend:${grade}`,
  label: `Backend-разработка · ${grade[0]!.toUpperCase()}${grade.slice(1)}`,
  specialization: 'backend',
  grade,
})

export const DEMO_VACANCIES: VacancyMatchDto[] = [
  {
    vacancy: {
      id: 'demo-v1',
      title: 'Python-разработчик (платформа инференса)',
      company: {
        id: 'demo-c1',
        name: 'МедИнтеллект',
        industry: 'Медтех: ИИ-диагностика',
        city: 'Москва',
        size: '51–200',
      },
      category: backend('middle'),
      stack: ['Python', 'PostgreSQL', 'FastAPI', 'RabbitMQ', 'Docker', 'Kafka'],
      salary: { from: 210_000, to: 290_000 },
      workFormat: 'remote',
      city: null,
      description:
        'Платформа принимает снимки из 40 клиник, ставит задачи моделям и возвращает врачам результаты за минуты.\n\nЗадачи:\n— разработка асинхронных REST API на FastAPI;\n— интеграции с внешними сервисами через очереди сообщений;\n— покрытие кода тестами на pytest и настройка CI.\n\nУсловия:\n— удалённая работа из любого города России;\n— ДМС со стоматологией после испытательного срока.',
      publishedAt: day(1),
    },
    matchScore: 0.92,
    reasons: [
      'Ваша категория: Backend-разработка · Middle',
      'Совпадает стек: Python, PostgreSQL, FastAPI, Kafka (4 из 6)',
      'Подходит формат: удалённо',
      'Зарплата до 290 000 ₽ — не ниже ваших ожиданий',
      'Опубликована вчера',
    ],
    reaction: null,
  },
  {
    vacancy: {
      id: 'demo-v2',
      title: 'Python-разработчик (RAG-платформа)',
      company: {
        id: 'demo-c2',
        name: 'Квант Аналитика',
        industry: 'Искусственный интеллект (LLM, NLP)',
        city: 'Москва',
        size: '11–50',
      },
      category: backend('middle'),
      stack: ['Python', 'PostgreSQL', 'FastAPI', 'Elasticsearch', 'Celery'],
      salary: { from: 220_000, to: 300_000 },
      workFormat: 'remote',
      city: null,
      description:
        'Платформа индексирует миллионы документов клиентов и отвечает на вопросы сотрудников.\n\nЗадачи:\n— проектирование схем данных и оптимизация запросов в PostgreSQL;\n— фоновые задачи и планировщики на Celery.',
      publishedAt: day(4),
    },
    matchScore: 0.84,
    reasons: [
      'Ваша категория: Backend-разработка · Middle',
      'Совпадает стек: Python, PostgreSQL, FastAPI (3 из 5)',
      'Подходит формат: удалённо',
      'Опубликована 4 дня назад',
    ],
    reaction: 'like',
  },
  {
    vacancy: {
      id: 'demo-v3',
      title: 'Senior Python-разработчик (поиск авиабилетов)',
      company: {
        id: 'demo-c3',
        name: 'Тревелио',
        industry: 'Travel tech',
        city: 'Санкт-Петербург',
        size: '201–500',
      },
      category: backend('senior'),
      stack: ['Python', 'PostgreSQL', 'asyncio', 'Redis', 'Kafka', 'Docker', 'gRPC'],
      salary: { from: 300_000, to: 420_000 },
      workFormat: 'hybrid',
      city: 'Санкт-Петербург',
      description:
        'Поиск авиабилетов опрашивает десятки поставщиков и возвращает выдачу за 2 секунды.\n\nТребования:\n— коммерческий опыт от 4 лет;\n— понимание асинхронности в Python (asyncio).',
      publishedAt: day(8),
    },
    matchScore: 0.71,
    reasons: [
      'Грейд Senior на ступень выше вашего: шанс вырасти',
      'Совпадает стек: Python, PostgreSQL, asyncio, Kafka (5 из 7)',
      'Подходит формат: гибрид',
      'Опубликована 8 дней назад',
    ],
    reaction: null,
  },
  {
    vacancy: {
      id: 'demo-v4',
      title: 'Go-разработчик (телематика)',
      company: {
        id: 'demo-c4',
        name: 'Поехали!',
        industry: 'Каршеринг и мобильность',
        city: 'Москва',
        size: '201–500',
      },
      category: backend('middle'),
      stack: ['Go', 'PostgreSQL', 'Kafka', 'gRPC', 'ClickHouse'],
      salary: { from: 230_000, to: 310_000 },
      workFormat: 'hybrid',
      city: 'Москва',
      description:
        'Телематика каждые 5 секунд принимает данные от 15 000 автомобилей и управляет замками и двигателями.',
      publishedAt: day(4),
    },
    matchScore: 0.63,
    reasons: [
      'Ваша категория: Backend-разработка · Middle',
      'Совпадает стек: PostgreSQL, Kafka, gRPC (3 из 5)',
      'Офис в вашем городе: Москва',
    ],
    reaction: null,
  },
  {
    vacancy: {
      id: 'demo-v5',
      title: 'Junior Python-разработчик',
      company: {
        id: 'demo-c5',
        name: 'Северный код',
        industry: 'Заказная разработка ПО',
        city: 'Санкт-Петербург',
        size: '201–500',
      },
      category: backend('junior'),
      stack: ['Python', 'PostgreSQL', 'Django', 'Celery', 'pytest'],
      salary: { from: 95_000, to: 140_000 },
      workFormat: 'hybrid',
      city: 'Санкт-Петербург',
      description:
        'Проектная команда делает сервисы для ритейла и логистики; у каждого джуниора есть ментор и индивидуальный план развития.',
      publishedAt: day(3),
    },
    matchScore: 0.52,
    reasons: [
      'Грейд Junior на ступень ниже вашего',
      'Совпадает стек: Python, PostgreSQL, Django (3 из 5)',
      'Опубликована 3 дня назад',
    ],
    reaction: null,
  },
]

export function demoVacancyFeed(page: number, perPage: number): VacancyFeedDto {
  const start = (page - 1) * perPage
  return {
    items: DEMO_VACANCIES.slice(start, start + perPage),
    total: DEMO_VACANCIES.length,
    page,
    perPage,
    pages: Math.ceil(DEMO_VACANCIES.length / perPage),
    personalized: true,
    basis: {
      category: backend('middle'),
      gradeVerified: true,
      stack: ['Python', 'PostgreSQL', 'FastAPI', 'Kafka', 'asyncio', 'gRPC'],
      workFormats: ['remote', 'hybrid'],
      city: 'Москва',
      salaryExpectation: 270_000,
    },
  }
}

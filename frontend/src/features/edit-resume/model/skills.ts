/** Curated skills. Typing filters them; a click adds the skill, so the whole list need not be typed. */

export const STACK_SKILLS = [
  'Python',
  'PostgreSQL',
  'Docker',
  'Kubernetes',
  'Go',
  'Java',
  'Kotlin',
  'C#',
  'C++',
  'TypeScript',
  'JavaScript',
  'React',
  'Vue',
  'Angular',
  'Node.js',
  'FastAPI',
  'Django',
  'Spring',
  'Redis',
  'Kafka',
  'RabbitMQ',
  'MongoDB',
  'MySQL',
  'ClickHouse',
  'Elasticsearch',
  'Git',
  'Linux',
  'Nginx',
  'Terraform',
  'Ansible',
  'AWS',
  'GCP',
  'Yandex Cloud',
  'CI/CD',
  'Grafana',
  'Prometheus',
  'SQL',
  'REST',
  'gRPC',
  'GraphQL',
  'HTML',
  'CSS',
  'Swift',
  'Kotlin Multiplatform',
  'Flutter',
  'React Native',
  'PyTorch',
  'TensorFlow',
  'Pandas',
  'Airflow',
  'Spark',
  'Hadoop',
  'Bash',
  'PowerShell',
  'Windows Server',
  'Active Directory',
  'Helm',
  'Istio',
  'OpenShift',
] as const

export const SOFT_SKILLS = [
  'Коммуникация',
  'Работа в команде',
  'Наставничество',
  'Самостоятельность',
  'Ответственность',
  'Тайм-менеджмент',
  'Критическое мышление',
  'Решение проблем',
  'Адаптивность',
  'Лидерство',
  'Эмпатия',
  'Презентации',
  'Переговоры',
  'Обучаемость',
  'Внимание к деталям',
] as const

export function suggestSkills(
  catalog: readonly string[],
  query: string,
  selected: readonly string[],
): string[] {
  const needle = query.trim().toLocaleLowerCase('ru')
  const taken = new Set(selected.map((item) => item.toLocaleLowerCase('ru')))
  const starts: string[] = []
  const contains: string[] = []
  for (const item of catalog) {
    const folded = item.toLocaleLowerCase('ru')
    if (taken.has(folded)) continue
    if (!needle) {
      starts.push(item)
      continue
    }
    if (!folded.includes(needle)) continue
    if (folded.startsWith(needle)) starts.push(item)
    else contains.push(item)
  }
  return [...starts, ...contains].slice(0, 8)
}

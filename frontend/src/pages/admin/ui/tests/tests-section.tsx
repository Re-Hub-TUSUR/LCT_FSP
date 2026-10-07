import { AssessmentBank } from '@/widgets/assessment-bank'

/** Grade test templates are still composed in the existing bank widget. */
export function TestsSection() {
  return (
    <section className="admin-section">
      <header className="admin-section__head">
        <h1 className="admin-section__title">Шаблоны тестов</h1>
      </header>
      <p className="admin-hint">
        Шаблоны грейдовых тестов: правила выборки задач, длительность, проходной балл. Статусы задач
        и история — в разделе «Банк заданий».
      </p>
      <AssessmentBank scope="admin" />
    </section>
  )
}

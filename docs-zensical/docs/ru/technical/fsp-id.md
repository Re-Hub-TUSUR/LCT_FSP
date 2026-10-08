---
icon: lucide/link
---

# FSP ID

Полный контракт — `docs/FSP_INTEGRATION.md` и `fsp-registry.openapi.yaml`. Здесь короткий контур, как он есть в коде.

Вход на платформу остаётся почтой и паролем. FSP ID не выдаёт наши токены и не создаёт аккаунт. Привязка доступна вошедшему кандидату, у которого уже есть резюме.

Организаторы не дают доступ к настоящим системам, поэтому обе работают в эмуляции при `FSP_ID_MODE=mock`: пути Keycloak, обмен authorization code и PKCE, claims ID-токена и запись реестра. Переход на настоящий Keycloak — смена конфигурации, пакет `backend/app/integrations/fsp/`.

```mermaid
sequenceDiagram
  participant C as Кандидат
  participant SPA as SPA
  participant API as API
  participant IdP as FSP ID
  C->>SPA: Связать с ФСП
  SPA->>API: /fsp-id/authorize
  C->>IdP: Вход и согласие
  SPA->>API: code и state на /profile/fsp/callback
  API->>IdP: Обмен кода
  API->>API: GET реестра и запись достижений
```

Пустой ответ реестра — обычный результат, не ошибка. Достижения влияют на силу профиля внутри категории и не задают грейд. Отвязка — `DELETE /candidates/me/fsp-link`. Повторный импорт — `POST /candidates/me/fsp-sync`.

Расписание «раз в 24 часа» из FR-К-36 в коде как фоновая задача не искалось отдельно: в маршрутах есть ручная синхронизация и импорт в момент привязки.

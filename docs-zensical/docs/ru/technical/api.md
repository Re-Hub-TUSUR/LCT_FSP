---
icon: lucide/cable
---

# API

Префикс `/api/v1`. Роутер собирается в `backend/app/api/router.py`. OpenAPI — `/api/docs`.

| Модуль | Префикс | Что делает сейчас |
|--------|---------|-------------------|
| health | `/health` | Живость и готовность |
| auth | `/auth` | Регистрация, вход, код подтверждения почты, повторная отправка, refresh, logout, вход через Яндекс ID (`/yandex`, `/yandex/start`, `/yandex/callback`), `/admin-gate` для админ-поддомена |
| users | `/users` | `/users/me` |
| categories | `/categories` | Словарь категорий |
| cities | `/cities` | Поиск по справочнику городов GeoNames (`/search?q=`) |
| candidates | `/candidates` | Поиск, своё резюме, второе резюме, фото, PDF, привязка и синхронизация ФСП |
| fsp-id | `/fsp-id` | Старт входа OIDC + PKCE |
| companies | `/companies` | Свой профиль, логотип, публичная страница, банк задач компании |
| test-assignments | `/companies/me/test-assignments` | Отправка тестового, ответы, ручная проверка |
| vacancies | `/vacancies` | Список, лента, свои, карточка, создание, правка, публикация, реакции |
| invitations | `/invitations` | Создание, список, карточка, принятие и отклонение |
| applications | `/applications` | Создание и список — `501`. Взаимный интерес идёт через `/responses` |
| matching | `/matching` | Потребность и рекомендации — `501`. Подбор — банк, фильтры и свайпы |
| responses | `/responses` | Входящие лайки и ответный лайк |
| calendar | `/calendar` | Встречи за период, создание, перенос, отмена, подтверждение |
| conversations | `/conversations` | Чаты и вложения |
| notifications | `/notifications` | Лента событий |
| assessments | `/assessments` | Категории, шаблоны, попытки, запуск кода, завершение, интервью, входящие тестовые. Анкета `/survey` — `501` |
| admin | `/admin` | Пользователи, плюс пакет `app/admin`: банк, аналитика, работодатели, банлист, настройки, верификация |
| ats | `/ats` | Подключение ATS, опрос, внешние отклики и решение. Банк кандидатов не меняет |

Эмуляция FSP ID и реестра (`/mock/...`) подключается только при `FSP_ID_MODE=mock`.

Пагинация списков — `page` и `perPage`. Роль читается из базы, не только из токена.

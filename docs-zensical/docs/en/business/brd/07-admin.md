---
icon: lucide/shield
---

# Administrator

The platform task bank, analytics, company checks, the ban list, dictionaries, parameters, and the journal. One role covers all of these screens.

## FR-А-01. Administrator role

**Priority:** MVP · К4 · **UC:** UC-А-01

The admin opens on the `admin` subdomain (documentation lives on the `docs` subdomain the same way). The browser asks for a name and a password and lets in only the people listed in nginx. After the right credentials the section «Админка» is open at once. The menu beside it has «Вакансии». The account does not ask for a second factor. The administrator does not read chats.

## FR-А-02. Task card

**Priority:** MVP · К2 · **UC:** UC-А-02

A platform task has a statement, a skill, a specialization, a difficulty, and a way to check it. A coding task stores a reference and tests. Preview fills in random values of the variables.

**UI strings:** «Добавить задание».

## FR-А-03. Task analytics

**Priority:** MVP · К2 · **UC:** UC-А-03

The administrator takes a snapshot and reads a table of tasks: how often they were solved and how they went. There is no calibration on personas and no one-prompt check.

## FR-А-04. Company card

**Priority:** extra · К6 · **UC:** UC-А-04

A company shows an activity signal: vacancies and how it reaches candidates. The decision on the documents is to confirm or to refuse. When the company deletes every extract file, the request leaves the list: there is nothing left to confirm or to refuse.

The list «Работодатели под подозрением» gains a company at once, without the button «Пересчитать». «Пересчитать» still takes the invitation snapshot. A threshold counts actions as they happen, and the company gets the status «Под подозрением». Nothing is restricted on its own: the administrator still decides. A new signal after «Подозрение снято» or «Предупреждена» sets «Под подозрением» again. The statuses «Ограничена» and «Заблокирована» do not weaken when a new signal arrives.

The signals are «Частая смена отметки одного кандидата» (5 in 10 minutes), «Частая смена реквизитов» (5 in a day), «Вакансии без слов» (2 in a day), «Частые отмены встреч» (5 in a day), «Много файлов в чате» (10 in an hour), and «Направление не из списка» (any attempt). The thresholds are changed on «Параметры». The card section «Сигналы» shows how many times a signal fired and when.

## FR-А-05. Ban list

**Priority:** MVP · К6 · **UC:** UC-А-05, UC-А-06, UC-О-10

Search by email and domain. Blocking a company, an email, or a domain needs a reason. Lifting the block needs a reason too. The record's history is kept.

A ban closes both a specialist and an employer: sign-in, a session refresh, and any request from a tab that is already open. The table column «Кого затрагивает» shows the role and the email. The company decision «Заблокировать» writes a ban-list row. Closing the card does not restore access: lifting the ban does.

A banned person sees only a window in the centre, with no header and no close button. The window is black, with a red frame and red text. X_X sits at the top, in the centre. The text is: «Вы были забанены по следующей причине: {причина}. Если вы думаете, что вас забанили по ошибке, можете попробовать написать нам на эту почту: {почта}». The address is a link. It comes from the SUPPORT_EMAIL setting, and the default is support@kadry.local.

## FR-А-06. Dictionaries

**Priority:** MVP · К5 · **UC:** UC-А-07

Specializations and skills. A new value can be added, an existing one renamed or archived. Platform grades are fixed: intern, junior, middle, senior, lead.

## FR-А-07. Parameters

**Priority:** MVP · К2 · **UC:** UC-А-08

One page lists the parameters from [chapter 09](09-parameters.md). A change needs a comment and is written to the journal: the old value and the new one. A change does not rewrite a value that an attempt already read.

## FR-А-08. Journal

**Priority:** MVP · К4 · **UC:** UC-А-09

The journal stores administrator actions: who, when, what changed. A record is not edited from the interface. Export is CSV.

---
icon: lucide/id-card
---

# Candidate profile

The resume, what an employer sees on the card, and the FSP link. Screens: П-К-01, П-К-02, П-К-13, П-К-14.

## FR-К-01. Resume form

**Priority:** MVP · К5 · **UC:** UC-К-02

**Rule.** The candidate fills in a resume: name, specialization, stack, years of experience, city, work format. The city is chosen from the list of populated places; an arbitrary name cannot be saved. Email comes from the account. The salary expectation is optional. Saving does not set a grade.

**UI strings:** «Сохранить резюме», «Выберите город из списка».

## FR-К-02. PDF recognition

**Priority:** MVP · К5 · **UC:** UC-К-01

**Rule.** The candidate attaches a PDF or DOCX. When a model key is set, the text is read and the form fields are filled. The candidate checks them before saving. Without the key, resume upload is unavailable and the form is filled by hand.

## FR-К-03. A grade written in the resume is only text

**Priority:** MVP · К2 · **UC:** UC-К-01

**Rule.** What the resume says does not become a category. Only a counted test sets the category.

## FR-К-04. A second resume

**Priority:** MVP · К2 · **UC:** UC-К-03

**Rule.** A candidate may have a second resume in another profession. It does not become the primary one by itself. The category and the cooldown are kept per specialization.

## FR-К-05. A card without contacts

**Priority:** MVP · К5 · **UC:** UC-К-04

**Rule.** Until an invitation is accepted, the employer does not see email or phone. The candidate can download their own resume.

## FR-К-06. What the bank shows

**Priority:** MVP · К5 · **UC:** UC-К-21

**Rule.** In the bank an employer sees the name, specialization, stack, city, work format, salary expectation when it is set, the test score, and FSP achievements the candidate did not hide. There are no contacts.

## FR-К-07. Pause

**Priority:** MVP · К1 · **UC:** UC-К-22

**Rule.** The status «Не ищу работу» removes the profile from the bank and the feed. Invitations and chats that are already open stay. Turning search back on shows the profile again.

**UI strings:** «Не ищу работу».

## FR-К-08. Consent at sign-up

**Priority:** MVP · К5 · **UC:** UC-О-02

**Rule.** Sign-up requires consent to process the data. Without the mark the account is not created. There is no separate consent to record the screen: the test is not recorded.

## FR-К-09. FSP link

**Priority:** MVP · К1 · **UC:** UC-К-23, UC-К-25

**Rule.** The candidate links the profile to their FSP participant ID. The registry and the sign-in are emulated inside the API for now (`FSP_ID_MODE=mock`): the page «Вход через ФСП ID» accepts a demo account's login and password. Every account uses `kadry-demo-2026`. The logins are `champion`, `cup`, `hackathon`, `empty` (an empty registry), and `offline` (the registry does not answer). A wrong password stays on the page: «Неверный логин или пароль». «Отмена» does not link the profile. Achievements are pulled when the candidate asks. Unlinking removes the imported results and titles. One FSP account is one platform account.

**UI strings:** «Привязать ФСП ID», «Войти», «Отмена», «Логин», «Пароль», «Неверный логин или пароль», «Отвязать».

## FR-К-10. FSP achievements on the card

**Priority:** MVP · К1 · **UC:** UC-К-23

**Rule.** The card shows the best line: discipline, event, place, year. The full list opens with the profile. An empty registry is not an error.

## FR-К-11. No FSP history

**Priority:** MVP · К5 · **UC:** UC-К-24

**Rule.** If there is no link or the history is empty, the card gets neither a bonus nor a penalty. The candidate sees that there is no history yet.

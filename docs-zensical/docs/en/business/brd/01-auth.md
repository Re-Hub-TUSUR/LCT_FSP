---
icon: lucide/key-round
---

# Sign-in and access

Email and password or Yandex ID, a confirmation code, one role per account. Screens: [П-О-01](../../product/pages.md) … П-О-04, П-О-08.

## FR-О-01. Sign-up by email

**Priority:** MVP · К5  
**UC:** UC-О-02, UC-О-03

**Rule.** The person sets email and password at once. The password is at least 8 characters. The account can sign in only after a 6-digit code from the email. Resending the code is limited. There is no password recovery. The session lives on a refresh token: logout revokes it, and each refresh issues a new one.

**UI strings:** «Продолжить», «Отправить письмо ещё раз».

## FR-О-02. Few steps at sign-up

**Priority:** MVP · К3  
**UC:** UC-О-01, UC-О-02

**Rule.** The role is chosen on the home page: «Я ищу работу» or «Я нанимаю». The sign-up form is email, password, and consent. The resume and the company profile are filled in after sign-in.

**UI strings:** «Я ищу работу», «Я нанимаю», «Продолжить».

## FR-О-03. Access

**Priority:** MVP · К4  
**UC:** UC-О-08

**Rule.** One account has one role: candidate, employer, or administrator. A candidate sees their resumes, invitations, tests, and chats. An employer sees their vacancies, invitations, take-homes, and the bank. Someone else's object is unavailable. An administrator does not read chats.

## FR-О-04. Ban list

**Priority:** MVP · К6  
**UC:** UC-А-05, UC-А-06

**Rule.** An administrator blocks a company, an email, or a domain and writes a reason. Unblocking needs a reason too. Who blocked and who lifted the block is kept on the record. Signing up again with a blocked email or domain does not go through.

## FR-О-12. Sign-in through Yandex ID

**Priority:** MVP · К5  
**UC:** UC-О-09

**Rule.** A specialist and an employer press «Войти через Яндекс» on the «Вход» and «Регистрация» tabs. On «Регистрация» the button waits for the consent tick. Yandex has already confirmed the email, so the code from the letter is not needed. A known Yandex ID opens the session at once. On «Вход», if the person does not exist, the answer is «Сначала зарегистрируйтесь» and no account is created. On «Регистрация» the account is created with a confirmed email: the first and last name go into the form, and the portrait goes into «Фото» when the resume is saved for the first time. An email that already belongs to the same role attaches the Yandex ID. A different role or the ban list is a refusal, and a second user is not created. An administrator is not created this way. Until the Yandex app is connected, there is no button. The admin subdomain does not show it either.

**UI strings:** «Войти через Яндекс», «Сначала зарегистрируйтесь».

---
icon: lucide/key-round
---

# Sign-in and access

Email and password, a confirmation code, one role per account. Screens: [П-О-01](../../product/pages.md) … П-О-04.

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

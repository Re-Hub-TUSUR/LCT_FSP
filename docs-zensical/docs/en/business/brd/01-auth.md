---
icon: lucide/key-round
---

# Authentication and access

Shared rules for sign-in, roles, and lockout. Screens: [П-О-01](../../product/pages.md) through П-О-06 and П-О-11.

## FR-О-01. Email registration

**Priority:** MVP · K5  
**Actors:** a new user  
**Related UC:** UC-О-02, UC-О-03, UC-О-04, UC-О-05

**Rule.** The account turns on only after the person follows the link in the email. The link is single-use and lives 24 hours. A resend is at most once per 60 seconds and at most 5 times per hour. Sign-in is impossible until the email is confirmed. Password recovery uses the same kind of link: the answer is the same whether the address exists or not. After a password change every session ends.

**UI strings:** «Продолжить», «Сохранить пароль», «Отправить письмо ещё раз», «Отправить ссылку».

## FR-О-02. Minimum registration steps

**Priority:** MVP · K3  
**Actors:** a new user  
**Related UC:** UC-О-01, UC-О-02, UC-О-03

**Rule.** The first screen is one email field and one required consent checkbox. The role comes from the home page: «Я ищу работу» or «Я нанимаю». The password is set after the email is confirmed. Everything else is collected later: resume, survey, company profile.

**UI strings:** «Я ищу работу», «Я нанимаю», «Продолжить».

## FR-О-03. External sign-in

**Priority:** extra · K6  
**Actors:** a user  
**Related UC:** UC-О-04, UC-К-41

**Rule.** Yandex ID and FSP ID are additional sign-in methods. If the email matches, the system offers to link the sign-in to the existing account instead of creating a second one. Gosuslugi, Mos.ru, and Nalog.ru are a later option and are not in the hackathon. Importing FSP results is FR-К-36 and does not replace email registration.

## FR-О-04. Two-factor authentication

**Priority:** MVP · K4  
**Actors:** employer, administrator, candidate if they choose  
**Related UC:** UC-О-06, UC-Р-01, UC-К-44, UC-А-24

**Rule.** 2FA is required for the employer and the administrator from the first sign-in. The candidate turns it on themselves. The authenticator code is 6 digits and lasts 30 seconds. Turning it on issues 10 one-time backup codes. Five wrong codes in a row lock sign-in for 15 minutes. Only an administrator can reset 2FA, and the reset is written to the audit log.

**UI strings:** «Подтвердить код», «Включить 2FA».

## FR-О-05. Access control

**Priority:** MVP · K4  
**Actors:** every role  
**Related UC:** UC-О-10, UC-А-18

**Rule.** One account has one role. A candidate sees only their resumes, invitations, applications, take-homes, and chats. An employer sees only their needs, invitations, vacancies, applications, take-homes, and tasks. Someone else's object is a 403 page and an audit entry. An administrator does not read chats except for a fragment attached to a report.

**UI strings:** «На главную», «Повторить».

## FR-О-13. Effects of a ban

**Priority:** MVP · K6  
**Actors:** a banned user, an administrator  
**Related UC:** UC-О-11, UC-А-16

**Rule.** A banned person cannot sign in and sees the reason and the term. The company's needs, vacancies, and recurring tasks are hidden. Active invitations become «Отозвано» with the reason «Компания заблокирована». The candidate disappears from shortlists and the bank. Registering again with the same email is unavailable.

**UI strings:** «Написать в поддержку», «Компания заблокирована».

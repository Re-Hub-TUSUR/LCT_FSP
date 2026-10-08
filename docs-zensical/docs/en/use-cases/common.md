---
icon: lucide/list-checks
---

# Shared scenarios

Normative text: [authentication](../business/brd/01-auth.md), [chat and statuses](../business/brd/04-invitations-chat.md).

## UC-О-01 Choose a role

**As** a user, **I want** to press «Я ищу работу» or «Я нанимаю», **so that** registration opens with that role. If I am already signed in, the system opens the role's home screen. Page П-О-01. FR-О-02.

## UC-О-02 Create an account

**As** a user, **I want** to enter an email, check consent, and press «Продолжить», **so that** a letter with a link arrives. A taken email offers sign-in or recovery. A bad format cannot be submitted. П-О-02. FR-О-01, FR-О-02.

## UC-О-03 Confirm and set a password

**As** a user, **I want** to follow the link and set a password, **so that** the account turns on and the role's onboarding opens. A link older than 24 hours offers a new letter. П-О-03. FR-О-01.

## UC-О-04 Sign in

**As** a user, **I want** to sign in with email and password, **so that** I reach the cabinet or a 2FA code. Five failures lock sign-in for 15 minutes. An unconfirmed email offers to send the letter again. П-О-04. FR-О-01, FR-О-04.

## UC-О-05 Forgotten password

**As** a user, **I want** to enter an email, **so that** I get a link if the account exists. The answer is the same for existing and missing addresses. After the change, sessions end. П-О-05. FR-О-01.

## UC-О-06 Second factor

**As** a user, **I want** to scan a code and enter 6 digits, **so that** 2FA turns on and 10 backup codes are issued. No app — sign in with a backup code, and that code is spent. П-О-06. FR-О-04.

## UC-О-07 Conversation

**As** a user, **I want** to write a message or attach a file, **so that** the other side receives it and «Прочитано» appears. A file over 10 MB or of the wrong type does not send. П-О-07. FR-О-09.

## UC-О-08 Meetings

**As** a user, **I want** to switch week and month, **so that** I see meetings with statuses and a call link in my time zone. Empty: «Встречу назначает рекрутер в чате». П-О-08. FR-О-10.

## UC-О-09 Notification

**As** a user, **I want** to open an event, **so that** I land on the right page and the notification becomes read. П-О-09. FR-О-11.

## UC-О-10 Unavailable page

**As** a user, **I want** to press «На главную» or «Повторить», **so that** I get back to work. Someone else's object is a 403 without detail. П-О-10. FR-О-05.

## UC-О-11 Ban

**As** a banned user, **I want** to see the reason, the term, and «Написать в поддержку», **so that** I understand why the cabinet is closed. П-О-11. FR-О-13.

## UC-О-12 Report

**As** a user, **I want** to pick a reason and write a comment up to 1000 characters, **so that** the report enters the queue. Without a reason the button stays inactive. П-О-12. FR-О-12.

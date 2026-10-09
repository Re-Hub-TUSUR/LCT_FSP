---
icon: lucide/messages-square
---

# Invitations, statuses, and chat

An employer asks a specific person. The candidate accepts or declines. After acceptance, contacts and the conversation open.

## FR-О-05. Invitation statuses

**Priority:** MVP · К1 · **UC:** UC-К-15, UC-Р-08

An invitation is «Отправлено», «Принято», or «Отклонено». Both sides see the same status. An invitation cannot be withdrawn, and it does not become «Истекло».

## FR-О-06. Salary band

**Priority:** MVP · К1 · **UC:** UC-Р-05, UC-К-15

An invitation and a vacancy require «от» and «до» in rubles, whole numbers, with «до» not below «от». The candidate sees the band before the chat.

## FR-О-07. Revealing contacts

**Priority:** MVP · К1 · **UC:** UC-К-15

Email and phone become visible to that company after the candidate accepts its invitation. Before that they are not on the card. Another company does not receive them.

## FR-О-08. Chat

**Priority:** MVP · К1 · **UC:** UC-О-05

A chat opens when the candidate accepts an invitation, or when interest is mutual: the company marked the person and they answered, or the other way around. A message is text. A file is up to 10 MB. There is no video call inside the product.

**UI strings:** «Отправить».

## FR-О-09. Meetings

**Priority:** extra · К1 · **UC:** UC-О-06

The employer sets a meeting: date, time, and a link to an external call. The candidate confirms or declines. The employer can move or cancel it.

**UI strings:** «Назначить встречу», «Подтвердить».

## FR-О-10. Live events

**Priority:** MVP · К3 · **UC:** UC-О-07

A like and a new message arrive in the open tab as a stream. There is no email digest for every event type.

## FR-О-11. Empty state

**Priority:** MVP · К3

An empty list says what to do next: poll the ATS, take the test, fill in the company. An error is shown as text next to the action.

## FR-К-23. Incoming invitations

**Priority:** MVP · К1 · **UC:** UC-К-14

The candidate has a list of invitations, newest first. A row shows the company, the text, the band, and the status. Without a resume the list is empty, and that is not an error.

## FR-К-24. Invitation card

**Priority:** MVP · К1 · **UC:** UC-К-15

The card shows the message, the band, the contact method, and the company. A vacancy is named when the invitation is tied to one.

## FR-К-25. Accept and decline

**Priority:** MVP · К1 · **UC:** UC-К-15, UC-К-16

«Принять» sets «Принято», opens contacts for that company, and opens the chat. «Отклонить» sets «Отклонено». While the candidate has not answered, the same company cannot send a second invitation.

**UI strings:** «Принять», «Отклонить».

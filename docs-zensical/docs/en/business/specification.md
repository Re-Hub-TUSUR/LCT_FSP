---
icon: lucide/clipboard-list
---

# Business specification

## Purpose

This document records what KADRY does now. Screen behavior is in the [BRD](brd/index.md). If the texts disagree, the BRD wins.

## Goals

| ID | Goal | How to tell it worked |
|----|------|------------------------|
| G1 | The employer finds a person | Bank or swipes → invitation with a band → «Принять» → contacts and chat |
| G2 | The category does not come from the resume | A grade choice and a test. Without a counted attempt the category is not confirmed |
| G3 | Code on the test is checked with questions | After the hidden tests pass — a written interview, if a model key is set |
| G4 | Contacts and the band are clear to both sides | The «от–до» band before the chat. Contacts only after «Принять» |
| G5 | Sign-in by email | A password at registration, a 6-digit code, a session on a refresh token. Or «Войти через Яндекс» |

## What exists

- Sign-up: email, a password of at least 8 characters, a code from the email. There is no password recovery. Or «Войти через Яндекс»: the email is already confirmed, the name is in the form, the portrait is in «Фото».
- A resume form, a second resume, PDF and DOCX parsing when a model key is set.
- A test for one of five grades, an answer draft, a code run, a score, a cooldown.
- A written interview: 2–3 questions, «Отправить ответы», a pass score of 60 out of 100.
- The bank, filters, employer swipes and candidate swipes.
- An invitation with a band, accept and decline, chat, a meeting calendar.
- Vacancies: draft, publishing, mutual interest.
- A company take-home.
- An ATS poll: Mock, the platform's filters, write-back.
- Admin: task bank, analytics, company checks, ban list, dictionaries, parameters, journal.
- An FSP link in mock mode.

## What does not exist

A survey before the test, a camera and screen sharing, a voice interview, sign-in through government services, two-factor authentication, a need and shortlist versions, an «Откликнуться» application, recurring tasks, account deletion, an in-product video call.

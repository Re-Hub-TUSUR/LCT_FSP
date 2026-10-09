---
icon: lucide/shield
---

# Administrator

The platform task bank, analytics, company checks, the ban list, dictionaries, parameters, and the journal. One role covers all of these screens.

## FR-А-01. Administrator role

**Priority:** MVP · К4 · **UC:** UC-А-01

An administrator signs in with the same email and password as the other roles. A second factor is not required. They do not read chats.

## FR-А-02. Task card

**Priority:** MVP · К2 · **UC:** UC-А-02

A platform task has a statement, a skill, a specialization, a difficulty, and a way to check it. A coding task stores a reference and tests. Preview fills in random values of the variables.

**UI strings:** «Добавить задание».

## FR-А-03. Task analytics

**Priority:** MVP · К2 · **UC:** UC-А-03

The administrator takes a snapshot and reads a table of tasks: how often they were solved and how they went. There is no calibration on personas and no one-prompt check.

## FR-А-04. Company card

**Priority:** extra · К6 · **UC:** UC-А-04

A company shows an activity signal: vacancies and how it reaches candidates. The decision on the documents is to confirm or to refuse.

## FR-А-05. Ban list

**Priority:** MVP · К6 · **UC:** UC-А-05, UC-А-06

Search by email and domain. Blocking a company, an email, or a domain needs a reason. Lifting the block needs a reason too. The record's history is kept.

## FR-А-06. Dictionaries

**Priority:** MVP · К5 · **UC:** UC-А-07

Specializations and skills. A new value can be added, an existing one renamed or archived. Platform grades are fixed: intern, junior, middle, senior, lead.

## FR-А-07. Parameters

**Priority:** MVP · К2 · **UC:** UC-А-08

One page lists the parameters from [chapter 09](09-parameters.md). A change needs a comment and is written to the journal: the old value and the new one. A change does not rewrite a value that an attempt already read.

## FR-А-08. Journal

**Priority:** MVP · К4 · **UC:** UC-А-09

The journal stores administrator actions: who, when, what changed. A record is not edited from the interface. Export is CSV.

---
icon: lucide/id-card
---

# Candidate profile

The resume, what an employer sees, consents, and FSP. Screens: П-К-02, П-К-03, П-К-21 through П-К-24.

## FR-К-01. Resume form

**Priority:** MVP · K5  
**UC:** UC-К-03

**Rule.** Required: full name, a specialization from the dictionary (at the start Backend, Frontend, Data/ML, QA), 1 to 30 skills, 0–50 years of experience, current or last job title, city, work format. Email comes from the account. Optional: phone, «О себе» up to 2000 characters, roles, soft skills, experience, education, links, expected salary from. A draft is saved every 10 seconds.

**UI strings:** «Сохранить резюме», «Заполнить вручную».

## FR-К-02. PDF recognition

**Priority:** MVP · K5  
**UC:** UC-К-02

**Rule.** A PDF up to 5 MB and 10 pages is accepted. Within 30 seconds the system fills name, contacts, stack, grade, roles, experience, and soft skills. Low-confidence fields are highlighted. Nothing is saved until the candidate confirms. A scan without a text layer shows a message and the manual form. On an empty screen: «Есть готовое резюме? Приложите его, а мы попробуем вытащить из него нужные данные!»

## FR-К-03. Resume grade is only a hint

**Priority:** MVP · K2  
**UC:** UC-К-02, UC-К-09

**Rule.** The grade taken from the resume does not affect the category, ranking, or employer filters. It is only preselected on «Выбор грейда» and shown to the employer with the caption «указано кандидатом».

## FR-К-04. Several resumes

**Priority:** MVP · K2  
**UC:** UC-К-04, UC-К-23

**Rule.** Up to N_резюме resumes. Each has its own specialization; a repeat is forbidden. Category and cooldown are tracked separately. The test runs on the first resume, then the system offers a test for the next. A refusal does not change the first category. The banner «Создайте ещё одно резюме» stays after save until the limit is reached.

## FR-К-05. Standard PDF profile

**Priority:** MVP · K5  
**UC:** UC-К-05, UC-Р-19

**Rule.** The file is rebuilt after the resume, category, or FSP results change, from one template. It contains the category, test score and date, per-skill result, stack, experience, roles, and FSP results. Two versions: a full one for the candidate, and an employer version without contacts before reveal and without fields the candidate hid.

**UI strings:** «Скачать PDF-профиль», «До раскрытия контактов», «После».

## FR-К-06. Cabinet statistics

**Priority:** extra · K3  
**UC:** UC-К-24

**Rule.** On «Приглашения», counters for 30 days: profile views, invitations received and accepted, applications by status.

## FR-К-33. Privacy

**Priority:** MVP · K5  
**UC:** UC-К-38, UC-К-05

**Rule.** Before contacts are revealed the employer always sees the category, test score and date, stack, experience, roles, and freshness. The candidate toggles visibility of the name (full, first name and the first letter of the surname, or hidden; the default is first name and the first letter), photo, current job, city, FSP results, recurring-task answers, per-skill result, and expected salary. A change reaches search within 1 minute.

## FR-К-34. Search pause

**Priority:** MVP · K1  
**UC:** UC-К-39

**Rule.** «Не ищу работу» removes the profile from shortlists, the bank, and recurring-task distribution within 1 minute. Active invitations, chats, and take-homes stay. Turning it off returns the profile to search.

## FR-К-35. Consents

**Priority:** MVP · K5  
**UC:** UC-К-10, UC-К-40

**Rule.** Required: personal-data processing at registration, profile publication (otherwise no shortlists and no bank), and proctoring recording before every grade test. Optional: FSP import and mailings. Each consent stores date, time, and text version. Withdrawing publication hides the profile within 1 minute. Withdrawing processing starts account deletion.

**UI strings:** «Отозвать».

## FR-К-36. FSP link

**Priority:** MVP · K1  
**UC:** UC-К-41, UC-К-43

**Rule.** The profile links to a participant ID by signing in with FSP ID. For the hackathon this is a demonstration registry with the same sign-in flow. Results are imported immediately and then once every 24 hours. Unlinking removes them from the profile, the PDF, and ranking within 1 minute. One FSP account links to one platform account.

**UI strings:** «Связать с ФСП», «Отвязать».

## FR-К-37. What FSP results contain

**Priority:** MVP · K1  
**UC:** UC-Р-17, UC-К-41

**Rule.** The employer sees disciplines, competitions from the last 3 years (name, level, date, place, team role), a sports rank or title, and the number of events. The card shows one line with the best result; the full list opens on click. The candidate controls visibility.

## FR-К-38. No FSP history

**Priority:** MVP · K5  
**UC:** UC-К-42

**Rule.** If there is no link or the history is empty, the candidate sees «Истории ФСП пока нет. Это не влияет на позицию в выдаче» and a link to the FSP competition calendar. The employer sees «Нет данных ФСП» without zeros or a warning colour. Ranking gives neither a bonus nor a penalty.

## FR-К-39. Account deletion

**Priority:** MVP · K5  
**UC:** UC-К-45

**Rule.** The password is required. The profile hides immediately. The account can be restored for 7 days, then data is deleted or anonymised within the NFR-03 term. Active invitations become «Истекло» with the note «Профиль удалён». Employer chats remain without the candidate's contacts.

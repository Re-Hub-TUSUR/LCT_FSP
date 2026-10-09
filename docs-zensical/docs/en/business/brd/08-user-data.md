---
icon: lucide/table
---

# What we know about a user

Where a field comes from, and whether it can be relied on. «Confirmed» means the value came from a check, not only from the resume text.

## Candidate

| Field | Source | Confirmed? |
|-------|--------|------------|
| Email | Sign-up, a code from the email | Yes |
| Name, city, format, stack, experience | Resume | No |
| Salary expectation | Resume, optional | No |
| Grade and test score | A counted attempt | Yes |
| Written-interview score | Answers after a test with working code | Yes, if an interview ran |
| FSP achievements | The registry after linking | Yes, from registry data |
| Empty FSP history | No link, or an empty registry | Yes, and it is not a penalty |
| Job-search status | The candidate | Yes, their choice |
| Consent | Sign-up | Yes |

## Employer

| Field | Source | Confirmed? |
|-------|--------|------------|
| Email | Sign-up, a code from the email | Yes |
| Name, city, description | Company profile | No, until an administrator confirms the documents |
| Vacancy and band | Vacancy form | Yes, what is published |
| Invitation | Invitation form | Yes, what was sent |
| External ATS application | Adapter poll | This is not a platform profile |

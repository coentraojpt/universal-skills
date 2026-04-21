---
usf: false
summary: Shared vocabulary — "customer" = paying entity; "user" = end-user inside a customer; "tenant" = isolated data partition.
---

# Company Glossary

Example shared vocabulary that skills can reference via `[[company-glossary]]`.

- **Customer** — a paying entity (company or individual with a billing relationship).
- **User** — an end-user who belongs to a Customer's workspace.
- **Tenant** — an isolated data partition. Usually 1:1 with Customer.
- **Workspace** — a Tenant's logical container for projects and users.
- **Project** — a top-level object inside a Workspace; scope of permissions.
- **Artifact** — any user-produced output stored in a Project.

## Naming conventions
- Database columns: `customer_id`, `user_id`, `tenant_id`, `project_id`.
- API paths: plural resource names (`/customers`, `/users`).
- Do NOT use "account" — ambiguous between Customer and User.

> Replace this file's content with your real glossary to give every skill shared memory.

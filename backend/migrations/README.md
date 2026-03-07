# Cloud SQL Migrations

Apply migrations with `psql` against your Cloud SQL Postgres instance.

Example:

```bash
psql "$DATABASE_URL" -f backend/migrations/001_init.sql
```

## 🗄 Database Migrations (Alembic)

This project uses :contentReference[oaicite:0]{index=0} for managing database schema migrations with :contentReference[oaicite:1]{index=1} models.

### Check for Pending Model Changes

Before generating a migration, you can check whether your SQLAlchemy models differ from the current database schema:

```bash
poetry run alembic check
```

If no changes exist, you will see:

```bash
No new upgrade operations detected.
```

---

### Generate a New Migration

After modifying models inside `app/models/`, generate a migration file:

```bash
poetry run alembic revision --autogenerate -m "describe your changes"
```

Example:

```bash
poetry run alembic revision --autogenerate -m "add candidate linkedin field"
```

This creates a migration file inside:

```bash
alembic/versions/
```

---

### Apply Migrations

Run all pending migrations:

```bash
poetry run alembic upgrade head
```

---

### View Current Migration Version

```bash
poetry run alembic current
```

---

### View Migration History

```bash
poetry run alembic history
```

---

### Rollback Last Migration

```bash
poetry run alembic downgrade -1
```

---

### Typical Workflow

1. Update SQLAlchemy models.
2. Check for schema differences:
   ```bash
   poetry run alembic check
   ```
3. Generate migration:
   ```bash
   poetry run alembic revision --autogenerate -m "your message"
   ```
4. Review generated migration file.
5. Apply migration:
   ```bash
   poetry run alembic upgrade head
   ```

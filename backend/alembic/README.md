# Alembic Database Migrations

This directory contains database migrations for the Shaplych Monitoring System.

## Quick Reference

### Check current migration version
```bash
alembic current
```

### List all migrations
```bash
alembic history --verbose
```

### Upgrade to latest
```bash
alembic upgrade head
```

### Downgrade one step
```bash
alembic downgrade -1
```

### Create new migration (auto-generate)
```bash
alembic revision --autogenerate -m "description_of_changes"
```

### Create new empty migration
```bash
alembic revision -m "description_of_changes"
```

## Migration History

### 257010976e6d - Add enabled field to device
- **Date:** 2025-11-27
- **Description:** Added `enabled` boolean field to `device` table for granular control over which devices are monitored
- **Changes:**
  - Added column: `device.enabled` (boolean, default=True)
  - Added index: `ix_device_enabled`

## Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations on dev database** before production
3. **Backup database** before running migrations
4. **Write reversible migrations** (downgrade should work)
5. **One logical change per migration**
6. **Descriptive migration names**

## Manual Migration Example

If you need to write a migration manually:

```python
def upgrade() -> None:
    op.add_column('device', sa.Column('new_field', sa.String(50), nullable=True))
    
def downgrade() -> None:
    op.drop_column('device', 'new_field')
```

## Troubleshooting

### Migration fails with "no such table"

Run database initialization first:
```bash
python -c "from app.core.db import create_db_and_tables; create_db_and_tables()"
```

### Alembic version table missing

Initialize Alembic:
```bash
alembic stamp head
```

### Conflict between migrations and manual schema changes

If you manually modified the database, you may need to:
1. Backup data
2. Drop tables
3. Run all migrations from scratch: `alembic upgrade head`
4. Restore data

### Reset migrations (nuclear option)

```bash
# Backup first!
cp shaplych_monitoring.db shaplych_monitoring.db.backup

# Drop alembic_version table
sqlite3 shaplych_monitoring.db "DROP TABLE IF EXISTS alembic_version;"

# Re-initialize
alembic stamp head
```

## SQLite Specifics

SQLite has limited `ALTER TABLE` support. Alembic uses batch operations for complex changes:

```python
with op.batch_alter_table('device') as batch_op:
    batch_op.add_column(sa.Column('new_field', sa.String(50)))
    batch_op.drop_column('old_field')
```

## Environment Configuration

Alembic is configured to:
- Read database path from `app.core.config.settings`
- Import all models from `app.models.*`
- Use SQLModel metadata for autogenerate

See `env.py` for details.

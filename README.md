# schemasafe

A free, offline command-line scanner that reads PostgreSQL migration `.sql` files and flags risky statements before you run them. It runs locally and sends no data anywhere.

## Usage

```
python -m schemasafe migration.sql
python -m schemasafe migrations/ other.sql --min-severity medium
python -m schemasafe migrations/ --format json
```

You can pass several files and folders. Folders are searched recursively for `*.sql` files.

Options:

- `--min-severity {low,medium,high}`: only report findings at or above this level (default `low`).
- `--format {text,json}`: output format (default `text`).

Text output is one line per finding, for example:

```
migration.sql:1 [HIGH] DROP_TABLE: Drops a table and all of its data.
```

Exit codes: `1` if anything is reported, `0` if clean, `2` on errors (no .sql files found, an unreadable or non-UTF-8 file, or bad arguments). That makes it usable in CI.

The repo also contains a `pyproject.toml` that defines a `schemasafe` command. Installing it with pip has not been tested yet.

## Rules

- High: DROP TABLE, DROP COLUMN, TRUNCATE, DELETE without WHERE, DROP SCHEMA, DROP DATABASE
- Medium: UPDATE without WHERE, SET NOT NULL, ADD COLUMN NOT NULL without DEFAULT, ALTER COLUMN TYPE, DROP CONSTRAINT, ADD FOREIGN KEY without NOT VALID, VACUUM FULL, LOCK TABLE
- Low: CREATE INDEX without CONCURRENTLY, RENAME

## How it works

The scanner blanks out comments, string literals, double-quoted identifiers and dollar-quoted blocks (keeping line numbers), splits the file into statements on semicolons, and applies one regex per rule to each statement.

## Running the tests

```
python -m pip install pytest
python -m pytest -q
```

GitHub Actions runs the tests on every push and pull request on Ubuntu, macOS and Windows with Python 3.9, 3.12 and 3.13 (see the Actions tab).

## Limitations

- It is a regex scanner, not a full SQL parser. Treat it as a quick safety net, not a guarantee.
- Code inside function bodies or DO blocks (dollar-quoted) is ignored, so risky statements there are not flagged.
- It only knows PostgreSQL-style syntax and a fixed set of rules.
- Expect some false positives and false negatives.
- Large real-world migration files have not been tested.

## License

MIT

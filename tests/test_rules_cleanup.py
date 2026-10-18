import pytest

from schemasafe.scanner import clean, scan

CASES = [
    ("DROP TABLE a;", "DROP_TABLE", True),
    ("SELECT 'a; DROP TABLE x';", "DROP_TABLE", False),
    ("SELECT E'it\\'s; DROP TABLE x';", "DROP_TABLE", False),
    ('SELECT "a;b"; DROP TABLE c;', "DROP_TABLE", True),
    ("DO $$ BEGIN DROP TABLE x; END $$;", "DROP_TABLE", False),
    ("DO $f$ BEGIN DROP TABLE x; END $f$;", "DROP_TABLE", False),
    ("SELECT $1; DROP TABLE x;", "DROP_TABLE", True),
    ("DELETE FROM t;", "DELETE_NO_WHERE", True),
    ("DELETE FROM t WHERE id = 1;", "DELETE_NO_WHERE", False),
    ("ALTER TABLE t ADD COLUMN x numeric(10,2) NOT NULL;", "ADD_NOT_NULL_NO_DEFAULT", True),
    ("ALTER TABLE t ADD COLUMN x numeric(10,2) DEFAULT 0 NOT NULL;", "ADD_NOT_NULL_NO_DEFAULT", False),
    ("ALTER TABLE t ADD COLUMN a int DEFAULT 0 NOT NULL, ADD COLUMN b int;", "ADD_NOT_NULL_NO_DEFAULT", False),
    ("ALTER TABLE t DROP COLUMN a;", "DROP_COLUMN", True),
    ("ALTER TABLE t DROP a;", "DROP_COLUMN", True),
    ("ALTER TABLE t DROP CONSTRAINT c;", "DROP_COLUMN", False),
    ("ALTER TABLE t ALTER COLUMN a DROP NOT NULL;", "DROP_COLUMN", False),
    ("ALTER TABLE t RENAME a TO b;", "RENAME", True),
    ("ALTER TABLE t RENAME TO u;", "RENAME", True),
    ("ALTER TABLE t RENAME CONSTRAINT a TO b;", "RENAME", False),
    ("ALTER INDEX i RENAME TO j;", "RENAME", False),
    ("ALTER TABLE t ALTER a SET DATA TYPE bigint;", "ALTER_TYPE", True),
    ("CREATE INDEX CONCURRENTLY i ON t (a);", "CREATE_INDEX_BLOCKING", False),
    ("VACUUM (FULL, ANALYZE) t;", "VACUUM_FULL", True),
    ("VACUUM t;", "VACUUM_FULL", False),
]


@pytest.mark.parametrize("sql,rule,expected", CASES)
def test_rule(sql, rule, expected):
    assert any(f[1] == rule for f in scan(sql)) is expected


def test_line_numbers():
    hits = [f for f in scan("SELECT 1;\n\nDROP TABLE a;") if f[1] == "DROP_TABLE"]
    assert [h[0] for h in hits] == [3]


def test_clean_preserves_length():
    sql = "SELECT 'ab\ncd';"
    assert len(clean(sql)) == len(sql)

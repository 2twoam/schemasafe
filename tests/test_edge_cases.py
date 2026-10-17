import pytest
from schemasafe.scanner import scan


def ids(sql):
    return {r[1] for r in scan(sql)}


@pytest.mark.parametrize("sql,expected", [
    ('DELETE FROM "a;b" WHERE id = 1;', set()),
    ('DROP TABLE "a;b";', {"DROP_TABLE"}),
    ('SELECT 1 AS "DROP TABLE";', set()),
    ('UPDATE "my table" SET a = 1;', {"UPDATE_NO_WHERE"}),
    ("DELETE FROM users\nWHERE id = 1;", set()),
    ("DELETE\nFROM users;", {"DELETE_NO_WHERE"}),
    ("ALTER TABLE t ADD COLUMN a int NOT NULL, DROP COLUMN b;", {"DROP_COLUMN", "ADD_NOT_NULL_NO_DEFAULT"}),
    ("ALTER TABLE t ADD COLUMN a int NOT NULL DEFAULT 0, DROP COLUMN b;", {"DROP_COLUMN"}),
    ("DELETE /* all */ FROM t;", {"DELETE_NO_WHERE"}),
    ("DELETE FROM t -- WHERE id=1\n;", {"DELETE_NO_WHERE"}),
    ("drop table x;", {"DROP_TABLE"}),
    ("DROP SCHEMA app CASCADE;", {"DROP_SCHEMA"}),
    ("DROP DATABASE app;", {"DROP_DATABASE"}),
    ("ALTER TABLE t DROP CONSTRAINT c;", {"DROP_CONSTRAINT"}),
    ("ALTER TABLE a ADD CONSTRAINT fk FOREIGN KEY (b) REFERENCES c(id);", {"ADD_FK_WITHOUT_NOT_VALID"}),
    ("ALTER TABLE a ADD FOREIGN KEY (b) REFERENCES c(id);", {"ADD_FK_WITHOUT_NOT_VALID"}),
    ("ALTER TABLE a ADD CONSTRAINT fk FOREIGN KEY (b) REFERENCES c(id) NOT VALID;", set()),
    ("ALTER TABLE a ADD FOREIGN KEY (b) REFERENCES c(id) ON DELETE CASCADE NOT VALID;", set()),
    ("VACUUM FULL users;", {"VACUUM_FULL"}),
    ("VACUUM (FULL, ANALYZE) users;", {"VACUUM_FULL"}),
    ("VACUUM ANALYZE users;", set()),
    ("LOCK TABLE users IN ACCESS EXCLUSIVE MODE;", {"LOCK_TABLE"}),
    ("CREATE UNIQUE INDEX i ON t (c);", {"CREATE_INDEX_BLOCKING"}),
    ("CREATE INDEX CONCURRENTLY i ON t (c);", set()),
])
def test_cases(sql, expected):
    assert ids(sql) == expected


def test_line_numbers():
    assert [(r[0], r[1]) for r in scan("SELECT 1;\n\n  DROP TABLE x;\nTRUNCATE y;")] == [(3, "DROP_TABLE"), (4, "TRUNCATE")]

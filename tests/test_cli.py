import json
import subprocess
import sys
from pathlib import Path

import pytest

from schemasafe.cli import main

ROOT = Path(__file__).resolve().parent.parent


def write(tmp_path, name, text):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_clean_file_exits_0(tmp_path, capsys):
    f = write(tmp_path, "ok.sql", "SELECT 1;\n")
    assert main([f]) == 0
    assert "No risky statements found." in capsys.readouterr().out


def test_risky_file_exits_1_and_reports_line(tmp_path, capsys):
    f = write(tmp_path, "bad.sql", "SELECT 1;\nDROP TABLE users;\n")
    assert main([f]) == 1
    assert ":2 [HIGH] DROP_TABLE" in capsys.readouterr().out


def test_min_severity_filters_findings_and_exit_code(tmp_path, capsys):
    f = write(tmp_path, "rename.sql", "ALTER TABLE t RENAME COLUMN a TO b;\n")
    assert main([f]) == 1
    capsys.readouterr()
    assert main([f, "--min-severity", "high"]) == 0
    assert "No risky statements found." in capsys.readouterr().out


def test_json_output_with_findings(tmp_path, capsys):
    f = write(tmp_path, "bad.sql", "DROP TABLE users;\n")
    assert main([f, "--format", "json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert {d["rule"] for d in data} == {"DROP_TABLE"}
    assert data[0]["severity"] == "high"
    assert data[0]["line"] == 1
    assert data[0]["file"] == f


def test_json_output_clean_is_empty_list(tmp_path, capsys):
    f = write(tmp_path, "ok.sql", "SELECT 1;\n")
    assert main([f, "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_directory_is_searched_recursively_for_sql_only(tmp_path, capsys):
    write(tmp_path, "migrations/a.sql", "DROP TABLE a;\n")
    write(tmp_path, "migrations/sub/b.sql", "TRUNCATE b;\n")
    write(tmp_path, "migrations/c.txt", "DROP TABLE c;\n")
    assert main([str(tmp_path / "migrations")]) == 1
    out = capsys.readouterr().out
    assert "a.sql" in out
    assert "b.sql" in out
    assert "c.txt" not in out


def test_duplicate_paths_are_scanned_once(tmp_path, capsys):
    f = write(tmp_path, "bad.sql", "DROP TABLE users;\n")
    assert main([f, f]) == 1
    assert capsys.readouterr().out.count("DROP_TABLE") == 1


def test_missing_file_exits_2(tmp_path, capsys):
    assert main([str(tmp_path / "nope.sql")]) == 2
    assert "nope.sql" in capsys.readouterr().err


def test_non_utf8_file_exits_2(tmp_path, capsys):
    p = tmp_path / "bad.sql"
    p.write_bytes(b"\xff\xfe\x00 SELECT 1;")
    assert main([str(p)]) == 2
    assert capsys.readouterr().err != ""


def test_empty_directory_exits_2(tmp_path, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert main([str(empty)]) == 2
    assert "no .sql files found" in capsys.readouterr().err


def test_bad_arguments_exit_2(tmp_path):
    f = write(tmp_path, "ok.sql", "SELECT 1;\n")
    with pytest.raises(SystemExit) as exc:
        main([f, "--format", "xml"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_python_dash_m_passes_exit_code(tmp_path):
    clean = write(tmp_path, "ok.sql", "SELECT 1;\n")
    risky = write(tmp_path, "bad.sql", "DROP TABLE users;\n")
    run = lambda path: subprocess.run(
        [sys.executable, "-m", "schemasafe", path],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    assert run(clean).returncode == 0
    r = run(risky)
    assert r.returncode == 1
    assert "DROP_TABLE" in r.stdout

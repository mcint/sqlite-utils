from sqlite_utils import cli, Database
from click.testing import CliRunner
import pytest


def test_memory_basic():
    result = CliRunner().invoke(cli.cli, ["memory", "select 1 + 1"])
    assert result.exit_code == 0
    assert result.output.strip() == '[{"1 + 1": 2}]'


@pytest.mark.parametrize("sql_from", ("test", "t", "t1"))
@pytest.mark.parametrize("use_stdin", (True, False))
def test_memory_csv(tmpdir, sql_from, use_stdin):
    content = "id,name\n1,Cleo\n2,Bants"
    input = None
    if use_stdin:
        input = content
        csv_path = "-"
        if sql_from == "test":
            sql_from = "stdin"
    else:
        csv_path = str(tmpdir / "test.csv")
        open(csv_path, "w").write(content)
    result = CliRunner().invoke(
        cli.cli,
        ["memory", csv_path, "select * from {}".format(sql_from), "--nl"],
        input=input,
    )
    assert result.exit_code == 0
    assert (
        result.output.strip()
        == '{"id": "1", "name": "Cleo"}\n{"id": "2", "name": "Bants"}'
    )


@pytest.mark.parametrize("extra_args", ([], ["select 1"]))
def test_memory_dump(extra_args):
    result = CliRunner().invoke(
        cli.cli,
        ["memory", "-"] + extra_args + ["--dump"],
        input="id,name\n1,Cleo\n2,Bants",
    )
    assert result.exit_code == 0
    assert result.output.strip() == (
        "BEGIN TRANSACTION;\n"
        "CREATE TABLE [stdin] (\n"
        "   [id] TEXT,\n"
        "   [name] TEXT\n"
        ");\n"
        "INSERT INTO \"stdin\" VALUES('1','Cleo');\n"
        "INSERT INTO \"stdin\" VALUES('2','Bants');\n"
        "CREATE VIEW t1 AS select * from [stdin];\n"
        "CREATE VIEW t AS select * from [stdin];\n"
        "COMMIT;"
    )


@pytest.mark.parametrize("extra_args", ([], ["select 1"]))
def test_memory_save(tmpdir, extra_args):
    save_to = str(tmpdir / "save.db")
    result = CliRunner().invoke(
        cli.cli,
        ["memory", "-"] + extra_args + ["--save", save_to],
        input="id,name\n1,Cleo\n2,Bants",
    )
    assert result.exit_code == 0
    db = Database(save_to)
    assert list(db["stdin"].rows) == [
        {"id": "1", "name": "Cleo"},
        {"id": "2", "name": "Bants"},
    ]

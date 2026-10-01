"""Journals and templates are converted from txt2tags to Markdown once."""

import zipfile

import pytest

from rednotebook import storage
from rednotebook.configuration import Config, JournalConfig
from rednotebook.data import Month
from rednotebook.util import migration


def write_month(journal, name, content):
    (journal / name).write_text(content, encoding="utf-8")


@pytest.fixture
def legacy_journal(tmp_path):
    journal = tmp_path / "journal"
    journal.mkdir()
    write_month(
        journal,
        "2020-01.txt",
        '1: {text: "== Title ==\\n//italic// and #tag"}\n'
        "2: {text: 'Plain text'}\n"
        "3: {text: 'Tagged day', 'Work': {'//meeting//': null, '5*': null}, 'Idea': null}\n",
    )
    write_month(journal, "2020-02.txt", "4: {text: '+ numbered item'}\n")
    return journal


def load(journal):
    return storage.load_all_months_from_disk(str(journal))


def convert_journal(journal):
    return migration.convert_journal(load(journal), str(journal), JournalConfig(str(journal)))


def uses_markdown(journal):
    return not migration.needs_conversion(JournalConfig(str(journal)))


def test_journal_config(tmp_path):
    config = JournalConfig(str(tmp_path))
    assert migration.needs_conversion(config)
    config.save_to(str(tmp_path))
    assert not (tmp_path / JournalConfig.FILENAME).exists()

    config["markup"] = "markdown"
    config.save_to(str(tmp_path))
    text = (tmp_path / JournalConfig.FILENAME).read_text()
    assert text.startswith("# ") and text.endswith("\nmarkup=markdown\n")
    assert not migration.needs_conversion(JournalConfig(str(tmp_path)))

    # "Save As" writes the settings to the new directory.
    new_dir = tmp_path / "new"
    new_dir.mkdir()
    config.save_to(str(new_dir))
    assert (new_dir / JournalConfig.FILENAME).read_text() == text


def test_unknown_markup_is_not_converted(tmp_path):
    (tmp_path / JournalConfig.FILENAME).write_text("markup=asciidoc\n")
    assert not migration.needs_conversion(JournalConfig(str(tmp_path)))


def test_journal_is_converted_and_saved(legacy_journal):
    backup = convert_journal(legacy_journal)

    assert uses_markdown(legacy_journal)
    days = load(legacy_journal)["2020-01"].days
    assert days[1].text == "## Title\n\n*italic* and #tag"
    assert days[2].text == "Plain text"
    assert load(legacy_journal)["2020-02"].days[4].text == "1. numbered item"
    # Tag names only change if their formatting has to be translated.
    assert days[3].content == {
        "text": "Tagged day",
        "Work": {"*meeting*": None, "5*": None},
        "Idea": None,
    }

    with zipfile.ZipFile(backup) as archive:
        assert sorted(archive.namelist()) == ["2020-01.txt", "2020-02.txt"]
        assert "//italic//" in archive.read("2020-01.txt").decode("utf-8")


def test_unchanged_months_are_not_rewritten(legacy_journal):
    write_month(legacy_journal, "2020-03.txt", "5: {text: Plain}\n")
    before = (legacy_journal / "2020-03.txt").read_bytes()
    months = load(legacy_journal)
    migration.convert_journal(months, str(legacy_journal), JournalConfig(str(legacy_journal)))
    assert (legacy_journal / "2020-03.txt").read_bytes() == before
    assert not months["2020-03"].edited


def test_empty_journal_only_gets_settings(tmp_path):
    assert convert_journal(tmp_path) is None
    assert sorted(path.name for path in tmp_path.iterdir()) == [JournalConfig.FILENAME]
    assert uses_markdown(tmp_path)


def test_backups_are_not_included_in_later_backups(legacy_journal):
    first = migration.backup_directory(str(legacy_journal), migration.BACKUP_PREFIX)
    second = migration.backup_directory(str(legacy_journal), migration.BACKUP_PREFIX + "-2")
    with zipfile.ZipFile(second) as archive:
        assert first.split("/")[-1] not in archive.namelist()


def test_tag_names_are_merged_if_they_become_equal():
    content = {"text": "", "//a//": {"x": None}, "*a*": {"y": None}}
    assert migration.convert_day_content(content) == {"text": "", "*a*": {"x": None, "y": None}}


def test_convert_months_marks_months_as_edited():
    month = Month(2020, 1, {1: {"text": "//italic//"}, 2: {"text": "plain"}})
    assert migration.convert_months({"2020-01": month}) == 1
    assert month.edited
    assert month.days[1].text == "*italic*"


@pytest.fixture
def user_config(tmp_path):
    return Config(str(tmp_path / "configuration.cfg"))


def test_templates_are_converted_once(tmp_path, user_config):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "1.txt").write_text("=== Monday ===\n//plan//\n", encoding="utf-8")
    (templates / "Plain.txt").write_text("Nothing to convert\n", encoding="utf-8")

    assert migration.convert_templates(str(templates), user_config) == 1
    assert (templates / "1.txt").read_text() == "### Monday\n\n*plan*"
    assert (templates / "Plain.txt").read_text() == "Nothing to convert\n"
    assert "templateMarkup=markdown" in (tmp_path / "configuration.cfg").read_text()
    assert len(list(templates.glob(f"{migration.BACKUP_PREFIX}-Templates-*.zip"))) == 1

    # Converting again must not change the Markdown.
    (templates / "1.txt").write_text("//not italic in Markdown//", encoding="utf-8")
    assert migration.convert_templates(str(templates), Config(user_config.filename)) == 0
    assert (templates / "1.txt").read_text() == "//not italic in Markdown//"


def test_new_template_directory_is_only_marked(tmp_path, user_config):
    assert migration.convert_templates(str(tmp_path), user_config) == 0
    assert user_config["templateMarkup"] == "markdown"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["configuration.cfg"]

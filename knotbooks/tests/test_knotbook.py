import os
import pathlib
import shutil

import nbformat
import pytest

import knotbooks.project
import knotbooks.book


@pytest.fixture
def kbproject():
    return knotbooks.project.KBProject("test_project")


@pytest.fixture
def template(kbproject):
    return kbproject.get_template()
    

def test_get_inserts(template):
    assert template.get_inserts() == [{'tag': 'content', 'cell_idx': 1},
                                      {'tag': 'other_stuff', 'cell_idx': 3}]


def test_iter_notebook_paths(kbproject):
    books = list(kbproject.iter_knotbooks())
    assert len(books) == 3
    assert len(books[0]) == 4
    assert isinstance(books[0]["kb"], knotbooks.book.Knotbook)
    nb1_path = pathlib.Path(r"content/a/01.ipynb")
    assert books[1]["kb"].path.relative_to(kbproject.project_path) == nb1_path


def test_commands():
    kbook = knotbooks.book.Book()

    cell_source = r"{% insert content %}"
    kbook.cells.append(kbook.new_markdown(
       source=cell_source))
    assert kbook.get_command(kbook[0])["command"] == "insert"
    assert kbook.get_command(kbook[0])["args"] == ["content"]

    kbook.cells.append(kbook.new_markdown())
    assert kbook.get_command(kbook[1])["command"] is None
    kbook.cells[1]["source"] = r"{% endblock %}"
    command = kbook.get_command(kbook[1])
    assert command["command"] == "endblock"
    assert command["args"] == []

    cell_source = r"{% multi-args 1 two %}"
    kbook.cells.append(kbook.new_markdown(source=cell_source))
    command = kbook.get_command(kbook[2])
    assert command["command"] == "multi-args"
    assert command["args"] == ["1", "two"]


def test_get_blocks(kbproject):
    books = list(kbproject.iter_knotbooks())
    blocks = books[1]["kb"].get_blocks()
    assert len(blocks.keys()) == 3
    assert knotbooks.book.Enums.KB_PAGE_COMMANDS in blocks
    assert len(blocks["content"]) == 3
    assert len(blocks["other_stuff"]) == 1


def test_build(kbproject):
    kbproject.first_pass()
    assert (kbproject.output_path / "a").exists()
    assert (kbproject.output_path / "x").exists()


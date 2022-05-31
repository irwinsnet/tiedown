import copy
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

@pytest.fixture
def project_passed1(kbproject):
    project_first_pass = copy.deepcopy(kbproject)
    project_first_pass.first_pass()
    return project_first_pass
    

def test_get_inserts(template):
    assert template.get_inserts() == [{'tag': 'content', 'cell_idx': 1},
                                      {'tag': 'other_stuff', 'cell_idx': 3}]


def test_iter_notebook_paths(kbproject):
    books = list(kbproject.iter_notebooks())
    assert len(books) == 3
    assert len(books[0]) == 4
    assert isinstance(books[0], knotbooks.book.Knotbook)
    nb1_path = pathlib.Path(r"content/a/01.ipynb")
    assert books[1].path.relative_to(kbproject.project_path) == nb1_path


def test_commands():
    kbook = knotbooks.book.Book()

    cell_source = r"{% insert content %}"
    kbook.cells.append(kbook.new_markdown(
       source=cell_source))
    cmd = kbook.get_commands(0)
    assert "insert" in cmd
    assert cmd["insert"] == ["content"]

    kbook.cells.append(kbook.new_markdown())
    assert not kbook.get_commands(kbook[1])

    kbook.cells[1]["source"] = r"{% endblock %}"
    command = kbook.get_commands(1)
    assert "endblock" in command
    assert command["endblock"] == []

    cell_source = r"{% multi-args 1 two %}"
    kbook.cells.append(kbook.new_markdown(source=cell_source))
    commands = kbook.get_commands(2)
    assert "multi-args" in commands
    assert commands["multi-args"] == ["1", "two"]


def test_get_blocks(kbproject):
    books = list(kbproject.iter_notebooks())
    blocks = books[1].get_blocks()
    assert len(blocks.keys()) == 3
    assert knotbooks.book.Enums.KB_PAGE_COMMANDS in blocks
    assert len(blocks["content"]) == 3
    assert len(blocks["other_stuff"]) == 1

def test_inserts(project_passed1):
    notebooks = list(project_passed1.iter_notebooks(output=True))
    parsed_cell = project_passed1.parse_inserts(notebooks[1][3], notebooks[1])
    assert parsed_cell == r"[Link to Lesson 2](../x/02.ipynb)"

    parsed_cell = project_passed1.parse_inserts(notebooks[0][2], notebooks[0])
    assert parsed_cell == "* [Lesson 1](a/01.ipynb)\n* [Lesson 2](x/02.ipynb)"


def test_build(project_passed1):
    assert (project_passed1.output_path / "a").exists()
    assert (project_passed1.output_path / "x").exists()



    




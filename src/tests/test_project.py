import copy
import pathlib
import pytest

import src.project
import src.book


@pytest.fixture
def tdproject():
    return src.project.Project("test_project")


@pytest.fixture
def template(tdproject):
    return tdproject._get_template()

@pytest.fixture
def project_passed1(tdproject):
    project_first_pass = copy.deepcopy(tdproject)
    project_first_pass.first_pass()
    return project_first_pass
    

def test_iter_notebook_paths(tdproject):
    books = list(tdproject.iter_notebooks())
    assert len(books) == 3
    assert len(books[0]) == 4
    assert isinstance(books[0], src.book.NoteBook)
    nb1_path = pathlib.Path(r"content/a/01.ipynb")
    assert books[1].path.relative_to(tdproject.project_path) == nb1_path


def test_commands():
    cbook = src.book.Book()

    cell_source = r"insert: content"
    cbook.cells.append(cbook.new_raw(source=cell_source))
    cmd = cbook.get_rawcell_commands(0)
    assert "insert" in cmd
    assert cmd["insert"] == "content"

    cbook.cells.append(cbook.new_raw())
    assert not cbook.get_rawcell_commands(cbook[1])

    cbook.cells[1]["source"] = r"endblock: "
    command = cbook.get_rawcell_commands(1)
    assert "endblock" in command
    assert command["endblock"] == None

    cell_source = r"multi-args: [1, two]"
    cbook.cells.append(cbook.new_raw(source=cell_source))
    commands = cbook.get_rawcell_commands(2)
    assert "multi-args" in commands
    assert commands["multi-args"] == [1, "two"]


def test_get_blocks(tdproject):
    books = list(tdproject.iter_notebooks())
    blocks = books[1].get_blocks()
    assert len(blocks.keys()) == 3
    assert src.book.Enums.KB_PAGE_COMMANDS in blocks
    assert len(blocks["content"]) == 3
    assert len(blocks["other_stuff"]) == 2

def test_inserts(project_passed1):
    notebooks = list(
        project_passed1.iter_notebooks(project_passed1.output_path))
    parsed_cell = project_passed1.parse_inserts(notebooks[1][4], notebooks[1])
    assert parsed_cell == r"[Link to Lesson 2](../x/02.ipynb)"

    parsed_cell = project_passed1.parse_inserts(notebooks[0][2], notebooks[0])
    assert parsed_cell == "* [Lesson 1](a/01.ipynb)\n* [Lesson 2](x/02.ipynb)"

    parsed_cell = project_passed1.parse_inserts(notebooks[0][3], notebooks[0])
    assert parsed_cell == (
        "1. [This is the title of Chapter 1](a/01.ipynb)\n"
        "2. [This is the title of Chapter 2](x/02.ipynb)")


def test_build(project_passed1):
    assert (project_passed1.output_path / "a").exists()
    assert (project_passed1.output_path / "x").exists()



    




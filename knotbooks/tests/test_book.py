import os
import pathlib
import shutil

import nbformat
import pytest

import knotbooks.project
import knotbooks.book


@pytest.fixture
def book1():
    path = pathlib.Path.cwd() / "test_project" / "content" / "a" / "01.ipynb"
    return knotbooks.book.Knotbook(path)

@pytest.fixture
def book2():
    path = pathlib.Path.cwd() / "test_project" / "content" / "x" / "02.ipynb"
    return knotbooks.book.Knotbook(path)

@pytest.fixture
def toc():
    path = pathlib.Path.cwd() / "test_project" / "content" / "TOC.ipynb"
    return knotbooks.book.Knotbook(path) 

@pytest.fixture
def template():
    path = pathlib.Path.cwd() / "test_project" / "templates" / "main.ipynb"
    return knotbooks.book.Template(path)

def test_folder():
    assert pathlib.Path.cwd().name == "knotbook"

def test_knotbook(book1):
    assert len(book1) == 10
    assert book1[0]["source"] == "{% target lesson_1 %}"

def test_get_applicable_template(book1, book2, toc):
    assert book1.get_applicable_template() == ""
    assert book2.get_applicable_template() == ""
    assert toc.get_applicable_template() is None


def test_inserts(template):
    inserts = template.get_inserts()
    assert len(inserts) == 2
    assert inserts[0]["tag"] == "content"
    assert inserts[0]["cell_idx"] == 1
    assert inserts[1]["tag"] == "other_stuff"
    assert inserts[1]["cell_idx"] == 3


def test_get_titles(book1, book2, toc):
    assert book1.get_title() == "This is the title of Chapter 1"
    assert book2.get_title() is None
    toc_entry = book2.get_commands(0)["toc_entry"]
    assert " ".join(toc_entry) == "This is the title of Chapter 2"
    assert toc.get_title() is None






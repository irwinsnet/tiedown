import os
import pathlib
import shutil

import nbformat
import pytest

import tiedown.book
import tiedown.project
import tiedown.utils as utils


@pytest.fixture
def book1():
    path = pathlib.Path.cwd() / "test_project" / "content" / "a" / "01.ipynb"
    return tiedown.book.Knotbook(path)


@pytest.fixture
def book2():
    path = pathlib.Path.cwd() / "test_project" / "content" / "x" / "02.ipynb"
    return tiedown.book.Knotbook(path)


@pytest.fixture
def toc():
    path = pathlib.Path.cwd() / "test_project" / "content" / "TOC.ipynb"
    return tiedown.book.Knotbook(path) 


@pytest.fixture
def template():
    path = pathlib.Path.cwd() / "test_project" / "templates" / "main.ipynb"
    return tiedown.book.Template(path)


def test_folder():
    assert pathlib.Path.cwd().name == "knotbook"


def test_knotbook(book1):
    assert len(book1) == 10
    assert book1[0]["source"] == "{% target lesson_1 %}"


def test_get_applicable_template(book1, book2, toc):
    assert book1.get_template_name() == ""
    assert book2.get_template_name() == ""
    assert toc.get_template_name() is None


def test_inserts(template):
    inserts = template.get_inserts()
    assert len(inserts) == 2
    assert inserts[0]["tag"] == "content"
    assert inserts[0]["cell_idx"] == 2
    assert inserts[1]["tag"] == "other_stuff"
    assert inserts[1]["cell_idx"] == 4


def test_get_titles(book1, book2, toc):
    assert book1.get_title() == "This is the title of Chapter 1"
    assert book2.get_title() is None
    toc_entry = book2.get_commands(0)["toc_entry"]
    assert " ".join(toc_entry) == "This is the title of Chapter 2"
    assert toc.get_title() is None


def test_roman():
    arabic = [1, 3, 4, 5, 7, 9, 11, 21, 29, 40, 49, 75, 99, 101, 1001, 3899]
    roman_upper = [utils.roman_from_int(x) for x in arabic]
    roman_lower = [utils.roman_from_int(x, lower=True) for x in arabic]
    roman = ['I', 'III', 'IV', 'V', 'VII', 'IX', 'XI', 'XXI', 'XXIX',
             'XL', 'XLIX', 'LXXV', 'XCIX', 'CI', 'MI', 'MMMDCCCXCIX']
    assert roman_upper == roman
    assert roman_lower == [rm.lower() for rm in roman]

    with pytest.raises(ValueError):
        utils.roman_from_int(0)

    with pytest.raises(ValueError):
       utils.roman_from_int(4000)


def test_letters():
    arabic = list(range(1, 150, 5))
    letters_upper = [utils.letters_from_int(x) for x in arabic]
    letters_lower = [utils.letters_from_int(x, lower=True) for x in arabic]
    alpha = ['A', 'F', 'K', 'P', 'U', 'Z', 'AE', 'AJ', 'AO', 'AT', 'AY', 'BD',
             'BI', 'BN', 'BS', 'BX', 'CC', 'CH', 'CM', 'CR', 'CW', 'DB', 'DG',
             'DL', 'DQ', 'DV', 'EA', 'EF', 'EK', 'EP']
    assert letters_upper == alpha
    assert letters_lower == [a.lower() for a in alpha]

    with pytest.raises(ValueError):
        utils.letters_from_int(0)



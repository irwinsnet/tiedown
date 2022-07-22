import pytest

import src.project

def test_toc():
    tdp = src.project.Project("pyclass")
    tdp.first_pass()
    tdp.second_pass()
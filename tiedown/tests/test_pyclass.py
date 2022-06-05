import pytest

import tiedown.project

def test_toc():
    tdp = tiedown.project.TdProject("pyclass")
    tdp.first_pass()
    tdp.second_pass()
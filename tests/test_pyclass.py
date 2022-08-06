import pytest

import project

def test_toc():
    tdp = project.Project("example_project")
    tdp.first_pass()
    tdp.second_pass()
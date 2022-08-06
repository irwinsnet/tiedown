import pathlib

import tiedown as td

def test_getting_started_build():
    repo_path = pathlib.Path(__file__).parents[1]
    getting_started_path = (
        repo_path / 
        "example_project" / 
        "content" / 
        "section-01-getting-started" /
        "getting-started-project")
   
    project = td.Project(getting_started_path)
    project.build()
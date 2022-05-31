import os.path
import pathlib
import re
import shutil

import nbformat

import knotbooks.book as book

class KBProject:

    def __init__(self, project_path,
                 notebook_prefix=""):
        """Creates a knotebook project.

        Args:
            project_path: path to knotbook templates and content files.
            notebook_prefix: knotbooks will ignore notebook files that
                don't start with this prefix.
        """
        self.project_path = pathlib.Path(project_path).resolve()
        self.content_path = self.project_path / "content"
        self.template_folder_path = self.project_path / "templates"
        self.notebook_prefix = notebook_prefix
        self.default_template = "main.ipynb"
        self.output_path = None
        self.links = {}
        self.toc = []

        self.ptn_insert = re.compile(r"{{\s*rel_link\s+([^}\s]+)\s*}}",
                                     re.IGNORECASE)

    def get_folders(self, output=False):
        """Gets list of subfolders in project folder.

        Args:
            output: boolean. If True, iterates over output folders,
                otherwise iterates over content folders. Optional.
                Default is False (content folders).
        Raises:
            ValueError if self.output_path has not been defined.
        Returns:
            List of pathlib.Path objects.
        """
        path = self.output_path if output else self.content_path
        if path is None:
            raise ValueError("Output path has not yet been defined.")
        folders = list(path.iterdir())
        folders = [folder for folder in folders
                   if folder.is_dir() and folder.name != ".ipynb_checkpoints"]
        folders = [path] + sorted(folders, key=lambda x: x.name)
        return folders

    def iter_notebooks(self, output=False):
        """Iterates over all notebooks in project.

        Args:
            output: boolean. If True, iterates over output notebooks,
                otherwise iterates over content notebooks. Optional.
                Default is False (content notebooks).
        Returns:
            A dictionary with keys "nb", "path", "folder_index",
            and "nb_index".
        """
        index = 0
        for folder_idx, folder in enumerate(self.get_folders(output)):
            nb_paths = list(folder.glob(f"{self.notebook_prefix}*.ipynb"))
            sorted_nbpaths = sorted(nb_paths, key=lambda x: x.name)
            for path_idx, path in enumerate(sorted_nbpaths):
                yield book.Knotbook(path)
                index += 1

    def _create_output_folder(self, output_path=None):
        """Creates a folder at output_path"""
        if output_path is None:
            output_path = "output"
        output_path = self.project_path / output_path
        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir()
        return output_path

    def get_template(self, template_name=""):
        """Retrieves the main template."""
        if template_name == "":
            template_name = self.default_template
        return book.Template(self.template_folder_path / template_name)      

    def first_pass(self, output_path=None):
        self.output_path = self._create_output_folder(output_path)

        subfolder = None
        for kb in self.iter_notebooks():
            # Get each knotbook and its output location
            if kb.path != subfolder:
                # Check for knotbooks in top-level folder
                if kb.path.parent == self.content_path:
                    subfolder = self.output_path
                # Process knotbooks in subfolders
                else:
                    subfolder = self.output_path / kb.path.parts[-2]
                    subfolder.mkdir()
            # Create new notebook from knotbook and template
            template_name = kb.get_applicable_template()
            if template_name is not None:
                template = self.get_template(template_name)
                nb = template.embed_knotbook(kb)
            else:
                nb = kb

            nb.path = subfolder / kb.path.parts[-1]

            # Process page-level commands
            cmds = nb.get_commands(0)
            if "target" in cmds:
                self.links[cmds["target"][0]] = nb
            if "toc_exclude" not in cmds:
                if "toc_entry" in cmds:
                    toc_entry = " ".join(cmds["toc_entry"])
                else:
                    toc_entry = kb.get_title()
                if toc_entry is not None:
                    self.toc.append((toc_entry, nb.path))


            # Write notebook to output folder
            nbformat.write(nb.book, nb.path, 4)

    def write_toc(self, relative_to=None):
        if relative_to is None:
            relative_to = self.output_path
        toc = []
        for entry in self.toc:
            toc_line = f"[{entry[0]}]({entry[1]})"


    def parse_inserts(self, cell, nb):
        def _make_link(match):
            tgt_nb = self.links[match.group(1)]
            return "(" + tgt_nb.rel_link_to(nb) + ")"
        return self.ptn_insert.sub(_make_link, cell["source"])

    def second_pass(self):
        for nb in self.iter_notebooks(output=True):
            for cell in nb.cells:
               cell["source"] = self.parse_inserts(cell, nb)
            nbformat.write(nb.book, nb.path, 4)


        

           

    




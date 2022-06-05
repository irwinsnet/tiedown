import pathlib
import re
import shutil

import nbformat

import tiedown.book as book

class TdProject:

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
        self.ignored_files_on_copy = []

        self.ptn_insert = re.compile(r"{{\s*rel_link\s+([^}\s]+)\s*}}",
                                     re.IGNORECASE)
        self.ptn_toc = re.compile(r"{{\s*toc\s*}}", re.IGNORECASE)

    def get_folders(self, path=None):
        """Gets list of subfolders in project folder.

        Args:
            path: Parent folder of returned folders as pathlib.Path
                object.
        Returns:
            Sorted list of folders as pathlib.Path objects.
        """
        path = self.content_path if path is None else self.output_path
        folders = list(path.iterdir())
        folders = [folder for folder in folders
                   if folder.is_dir() and folder.name != ".ipynb_checkpoints"]
        folders = [path] + sorted(folders, key=lambda x: x.name)
        return folders

    def iter_notebooks(self, path=None):
        """Iterates over all notebooks in project.

        Args:
            path: Parent folder of returned Knotbooks. Pathlib.Path
                object.
        Returns:
            Knotbooks from the folder specified in path or its child
            folders.
        """
        index = 0
        for folder in self.get_folders(path):
            nb_paths = list(folder.glob(f"{self.notebook_prefix}*.ipynb"))
            sorted_nbpaths = sorted(nb_paths, key=lambda x: x.name)
            for path in sorted_nbpaths:
                yield book.NoteBook(path)
                index += 1

#region FIRST PASS #####################################################
#     Tiedown conducts two different passes over the project files.
# The methods in this section are used for the first pass.
########################################################################

    def first_pass(self, output_path=None):
        """Builds output notebooks from content files.
        
        The following actions occur during the first pass:
        * All files in the output folder are erased and a new output
          folder is created.
        * Each content notebook is combined with a template to create
          a new output notebook.
        * Each notebook is scanned for relative links and TOC entries.
        * Sections are numbered.
        * Output notebooks are saved to disk in the output folder.
        * Copies other top-level files and folders in the content folder.

        Args:
            output_path: Optional. The name of the output folder as
              a string. Defaults to "output". 
        """
        self.output_path = self._create_output_folder(output_path)
        for obook in self._iter_output_notebooks():
            cmds = obook.get_commands(0)  # Get page-level commands
            self._append_links(obook, cmds)
            self._append_toc_entries(obook, cmds)
            obook = self._add_section_numbers(obook, cmds)
            obook.write()
        self._copy_other_files()

    def _create_output_folder(self, output_path=None):
        """Creates a folder at output_path"""
        if output_path is None:
            output_path = "output"
        output_path = self.project_path / output_path
        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir()
        return output_path

    def _iter_output_notebooks(self):
        subfolder = None
        for cbook in self.iter_notebooks():
            subfolder = self._update_subfolder(subfolder, cbook)
            yield self._create_output_notebook(subfolder, cbook)

    def _update_subfolder(self, subfolder, cbook):
        if cbook.path != subfolder:
            # Check for knotbooks in top-level folder
            if cbook.path.parent == self.content_path:
                subfolder = self.output_path
            # Process knotbooks in subfolders
            else:
                subfolder = self.output_path / cbook.path.parts[-2]
                self._copy_subfolder_contents(cbook.path.parent, subfolder)
                # subfolder.mkdir()
        return subfolder

    def _create_output_notebook(self, subfolder, cbook):
        template_name = cbook.get_template_name()
        if template_name is not None:
            template = self._get_template(template_name)
            nb = template.embed_knotbook(cbook)
        else:
            nb = cbook
        nb.path = subfolder / cbook.path.parts[-1]
        nb.title = cbook.get_title()
        return nb

    def _get_template(self, template_name=""):
        """Retrieves a template file."""
        if template_name == "":
            template_name = self.default_template
        return book.Template(self.template_folder_path / template_name)

    def _append_links(self, obook, cmds):
        if "target" in cmds:
            self.links[cmds["target"]] = obook

    def _append_toc_entries(self, obook, cmds):
        if "toc_exclude" not in cmds:
            if "toc_entry" in cmds:
                toc_entry = cmds["toc_entry"]
            else:
                toc_entry = obook.title
            if toc_entry is not None:
                self.toc.append((toc_entry, obook))

    def _copy_subfolder_contents(self, subfolder, output):
        ignored = self.ignored_files_on_copy
        ignored.extend([".ipynb_checkpoints", ".ipynb"])
        shutil.copytree(
            subfolder, output, ignore=shutil.ignore_patterns(*ignored))

    def _add_section_numbers(self, obook, cmds):
        if "outline" in cmds:
            if cmds["outline"] != "None":
                obook.number_headers(cmds["outline"])
        elif obook.template is not None:
            tcmds = obook.template.get_commands(0)
            if "outline" in tcmds and tcmds["outline"] != "None":
                obook.number_headers(tcmds["outline"])
        return obook

    def _copy_other_files(self):
        """Copy top-level content files and folders without notebooks."""
        for content_item in self.content_path.iterdir():
            output_item = self.output_path / content_item.name
            if output_item.exists():
                continue
            if content_item.is_dir() and content_item != ".ipynb_checkpoints":
                self._copy_subfolder_contents(content_item, output_item)
            else:
                shutil.copy(content_item, output_item)
        
#endregion

#region SECOND PASS ####################################################
#     The second pass is conducted over the notebooks in the output
# folder.
########################################################################

    def second_pass(self):
        for obook in self.iter_notebooks(self.output_path):
            for cell in obook.cells:
               cell["source"] = self.parse_inserts(cell, obook)
            obook.remove_command_cells()
            obook.write()

    def parse_inserts(self, cell, obook):
        def _make_link(match):
            tgt_nb = self.links[match.group(1)]
            return "(" + tgt_nb.rel_link_to(obook) + ")"
        parsed =  self.ptn_insert.sub(_make_link, cell["source"])

        def _make_toc(match):
            return self.write_toc(obook)
        parsed = self.ptn_toc.sub(_make_toc, parsed)

        return parsed

    def write_toc(self, obook):
        toc = []
        entry_num = 1
        for entry in self.toc:
            text = entry[0]
            link = entry[1].rel_link_to(obook)
            toc.append(f"{entry_num}. [{text}]({link})")
            entry_num += 1
        return "\n".join(toc)

#endregion   
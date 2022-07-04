import pathlib
import re
import shutil
import string

import yaml

import tiedown.book as book
import tiedown.utils as utils

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
        self.index = {}
        self.ignored_files_on_copy = []

        self.ptn_insert = None
        self.ptn_toc = None

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
            obook.add_cell_ids()            
            self._append_page_links(obook)
            self._append_toc_entries(obook)
            self._add_section_numbers(obook)
            self._append_index_entries(obook)
            obook.remove_raw_cells()
            obook.write()
        self._copy_other_files()

    def _create_output_folder(self, output_path=None):
        """Creates a folder at output_path.
        
        Args:
            output_path: str or pathlib path. Path to project's output
                folder.
        
        Returns: Pathlib path to the output folder.
        """
        if output_path is None:
            output_path = "output"
        output_path = self.project_path / output_path
        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir()
        return output_path

    def _iter_output_notebooks(self):
        """Iterator for output notebooks.
        
        Creates and yields a new output notebook for each content
        notebook.
        """
        subfolder = None
        for cbook in self.iter_notebooks():
            subfolder = self._copy_folder_contents(subfolder, cbook)
            yield self._create_output_notebook(subfolder, cbook)

    def _copy_folder_contents(self, subfolder, cbook):
        """Copies folder contents to the output folder."""
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
        """Creates an output notebook."""
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

    def _append_page_links(self, obook):
        """Adds page link to project links table."""
        cmds = obook.get_commands(0)
        if "target" in cmds:
            self.links[cmds["target"]] = obook

    def _append_toc_entries(self, obook):
        """Adds TOC entry to project toc table."""
        cmds = obook.get_commands(0)
        if "toc_exclude" not in cmds:
            if "toc_entry" in cmds:
                toc_entry = cmds["toc_entry"]
            else:
                toc_entry = obook.title
            if toc_entry is not None:
                self.toc.append((toc_entry, obook))

    def _append_index_entries(self, obook):
        """Appends index entries to project index table."""
        def _add_index(match):
            cmd = yaml.load(match.group(1), Loader=yaml.FullLoader)
            if "index" in cmd:
                index_entries = cmd["index"]
                if isinstance(index_entries, str):
                    index_entries = [{index_entries: None}]
                for entry in index_entries:
                    exp_entry = {entry: None} if isinstance(entry, str) else entry
                    for term, modifier in exp_entry.items():
                        if modifier == 'code':
                            index_key = term
                        elif modifier == 'preserve_case':
                            index_key = term
                        else:
                            index_key = term.lower()
                        link_data = (obook, idx)
                        if (index_key, modifier) in self.index:
                            self.index[(index_key, modifier)].append(link_data)
                        else:
                            self.index[(index_key, modifier)] = [link_data]
                return ""
            else:
                return match.group(0)

        if self.ptn_insert is None:
            self.ptn_insert= re.compile(r"{{([^}]*)}}", re.IGNORECASE)
        for cell in obook.md_cells:
            idx = cell["metadata"][utils.Keys.td_cell_index.value]
            self.ptn_insert.sub(_add_index, cell["source"])

    def _copy_subfolder_contents(self, subfolder, output):
        ignored = self.ignored_files_on_copy
        ignored.extend([".ipynb_checkpoints", ".ipynb"])
        shutil.copytree(
            subfolder, output, ignore=shutil.ignore_patterns(*ignored))

    def _add_section_numbers(self, obook):
        """Adds section numbers to each output notebook."""
        cmds = obook.get_commands(0)
        if "outline" in cmds:
            if cmds["outline"] != "None":
                obook.number_headers(cmds["outline"])
        elif obook.template is not None:
            tcmds = obook.template.get_commands(0)
            if "outline" in tcmds and tcmds["outline"] != "None":
                obook.number_headers(tcmds["outline"])
        # return obook

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
        """Passes over all output notebooks again for finalization.
        * Adds TOC and/or index.
        * Removes raw cells.
        * Removes cell outputs.
        """
        for obook in self.iter_notebooks(self.output_path):
            for cell in obook.md_cells:
               cell["source"] = self.parse_inserts(cell, obook)
            obook.remove_raw_cells()
            obook.remove_code_outputs()
            obook.write()

    def parse_inserts(self, cell, obook):
        """Evalutes inline commands in output book."""
        def _replace(match):
            cmd = yaml.load(match.group(1), Loader=yaml.FullLoader)
            if "rel_link" in cmd:
                link_parts = cmd["rel_link"].split("#")
                tgt_nb = self.links[link_parts[0]]
                rel_link = tgt_nb.rel_link_to(obook)
                if len(link_parts) > 1:
                    rel_link = rel_link + "#" + link_parts[1]
                return "(" + rel_link + ")"
            elif "toc" in cmd:
                return self.write_toc(obook)
            elif "write_index_section" in cmd:
                return self.write_index_section(cmd["write_index_section"],
                                                obook)
            elif "skip" in cmd:
                return ""
            elif "id" in cmd:
                return f'<span id="{cmd["id"]}"/>'

        if self.ptn_insert is None:
            self.ptn_insert = re.compile(r"{{([^}]*)}}", re.IGNORECASE)
        return self.ptn_insert.sub(_replace, cell["source"])

    def write_toc(self, obook):
        """Writes Table of Contents (TOC).
        
        Args:
            obook: Output notebook that will contain TOC.

        Returns: TOC as HTML text.        
        """
        toc = []
        entry_num = 1
        for entry in self.toc:
            text = entry[0]
            link = entry[1].rel_link_to(obook)
            toc.append(f"{entry_num}. [{text}]({link})")
            entry_num += 1
        return "\n".join(toc)

    def get_index_section(self, section_range):
        section = {}
        for char in section_range:
            if char.upper() in string.ascii_uppercase:
                section.update({key: val for key, val in self.index.items()
                                if key[0][0].upper() == char.upper()})
            else:
                section.update(
                    {key: val for key, val in self.index.items()
                     if key[0][0].upper() not in string.ascii_uppercase})
        return section

    def write_index_section(self, section_start, obook=None):
        index_path = self.output_path if obook is None else obook.path
        index_section = self.get_index_section(section_start)
        index = ["| Term | Links | Term | Links |"]
        index.append("| --- | --- | --- | --- |")
        index_keys = sorted(list(index_section.keys()),
                            key=lambda x: x[0].lower())
        if len(index_keys) % 2 == 1:
            index_keys.append(None)
        left_keys = index_keys[:len(index_keys)//2]
        right_keys = index_keys[len(index_keys)//2:]
        for left_key, right_key in zip(left_keys, right_keys):
            left_cells = self.get_index_cell_html(left_key, index_path)
            right_cells = self.get_index_cell_html(right_key, index_path)
            index.append(f" | {left_cells} | {right_cells} |")
        return "\n".join(index)

    def get_index_cell_html(self, key, index_path):
        """Generates a markdown table row.

        Args:
            key: A two-element tuple containing the index term and
                either `None` or the term's modifier.

        Returns a string containing markdown table markup.        
        """
        if key is None:
            return " | "
        term, modifier = key
        if modifier is None:
            term = term.title()
        elif modifier == "code":
            term = f"`{term}`"
        html = []
        html.append(f"{term} |")
        for link in self.index[key]:
            link_text = link[0].get_title()
            if link_text is None:
                link_text = link[0].path.name
            link_href = link[0].rel_link_to(index_path, link[1])
            html.append(f'[{link_text}]({link_href})<br/>')
        return " ".join(html)


#endregion   
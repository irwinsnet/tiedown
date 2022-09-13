import datetime
import logging
import pathlib
import re
import shutil
import string

import yaml

from tiedown.instructions import Actions, Inserts
import tiedown.book
import tiedown.toc
import tiedown.utils


# TODO: Mechanism to have raw cells in notebook.
# TODO: Remove {% ignore %} statement.


class Project:

    def __init__(self, project_path,
                 notebook_prefix="", log=False):
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
        self.books = []
        self.labels = {}
        self.index = {}
        self.ignored_files_on_copy = []

        self.ptn_action = re.compile(r"{%([^%]*)%}", re.IGNORECASE)
        self.ptn_insert = re.compile(r"{{([^}]*)}}", re.IGNORECASE)

        self._ignore = False

        self.ext = {}
        self.add_tiedown_extension(tiedown.toc.Toc(self))

        if log:
            log_filename = ("build-log-" + 
                datetime.datetime.now().strftime("%Y%M%d-%H%M%S"))
            log_path = project_path / log_filename
            logging.basicConfig(filename=log_path, encoding="UTF-8",
                                level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)
        logging.info("Tiedown Build Log")
        logging.info(f"Commenced Build: {datetime.datetime.now()}")
        logging.info("Project Path: %s", self.project_path)
        logging.info("Content Path: %s", self.content_path)

    def add_tiedown_extension(self, extension):
        self.ext[extension.name] = extension


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
                yield tiedown.book.NoteBook(path)
                index += 1

    def build(self, output_path=None):
        self.first_pass(output_path)
        self.second_pass()

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
        prior_book = None
        self.output_path = self._create_output_folder(output_path)
        logging.info("Output Path: %s", self.output_path)
        for obook in self._iter_output_notebooks():
            logging.debug("Parsing: %s", obook.path)
            obook.add_cell_ids()
            logging.debug("\t\tAdded cell IDs")        
            self._append_command_cell_labels(obook)

            # run book-level first-pass extension methods
            extensions = sorted(self.ext.values(),
                                key=lambda x: x.bookpass1_priority)
            for extension in extensions:
                extension.bookpass1(obook)
            # self._append_toc_entries(obook)
            self._add_section_numbers(obook)
            self._parse_markdown_cells(obook)
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
        for cbook in self.iter_notebooks():
            output_subfolder = self._prepare_output_subfolder(cbook)
            yield self._create_output_notebook(cbook, output_subfolder)

    def _prepare_output_subfolder(self, cbook):
        """Creates new output folder (if needed) and copies files.

        Args:
            cbook: A content notebook.
        
        Returns: pathlib.Path to output folder that will contain
        corresponding output notebook.
        """
        if cbook.path.parent == self.content_path:
            subfolder = self.output_path
        else:
            subfolder = self.output_path / cbook.path.parts[-2]

        if not subfolder.exists():
            self._copy_subfolder_contents(cbook.path.parent, subfolder)
        return subfolder

    def _create_output_notebook(self, cbook, subfolder):
        """Creates an output notebook."""
        template_name = cbook.get_template_name()
        if template_name is not None:
            template = self._get_template(template_name)
            nb = template.embed_knotbook(cbook)
        else:
            nb = cbook
        nb.path = subfolder / cbook.path.parts[-1]
        # nb.title = cbook.get_title()
        return nb

    def _get_template(self, template_name=""):
        """Retrieves a template file."""
        if template_name == "":
            template_name = self.default_template
        return tiedown.book.Template(self.template_folder_path / template_name)

    def _append_command_cell_labels(self, obook):
        """Adds page link to project links table."""
        logging.debug("\t\tAppending Command Cell labels")      
        cmds = obook.get_rawcell_commands(0)
        if Actions.label in cmds:
            self.labels[cmds[Actions.label]] = (obook, None)

    def _append_toc_entries(self, obook):
        """Adds TOC entry to project toc table."""
        logging.debug("\t\tAppending TOC Entries")      
        cmds = obook.get_rawcell_commands(0)
        if Actions.toc_exclude not in cmds:
            if Actions.toc_entry in cmds:
                toc_entry = cmds[Actions.toc_entry]
            else:
                toc_entry = obook.title
            if toc_entry is not None:
                self.toc.append((toc_entry, obook))
                obook.metadata["tiedown_toc_index"] = len(self.ext["tiedown_toc"]) - 1

    @staticmethod
    def _load_commands(match):
        cmd = yaml.load(match.group(1), Loader=yaml.FullLoader)
        return {cmd: None} if isinstance(cmd, str) else cmd


    def _parser_pass1(self, match, obook, idx):
        # Figure out whether actions or inserts should be ignored.
        cmd = self._load_commands(match)
        if Actions.end_ignore in cmd:
            self._ignore = False
        elif Actions.label in cmd:
            self.labels[cmd[Actions.label]] = (obook, idx)
        elif Actions.ignore in cmd:
            self._ignore = True

        if not self._ignore:
            if Actions.index in cmd:
                index_entries = cmd[Actions.index]
                if isinstance(index_entries, str):
                    index_entries = [{index_entries: None}]
                for entry in index_entries:
                    exp_entry = {entry: None} if isinstance(entry, str) else entry
                    for term, modifier in exp_entry.items():
                        if modifier == Actions.code:
                            index_key = term
                        elif modifier == Actions.preserve_case:
                            index_key = term
                        else:
                            index_key = term.lower()
                        link_data = (obook, idx)
                        if (index_key, modifier) in self.index:
                            self.index[(index_key, modifier)].append(link_data)
                        else:
                            self.index[(index_key, modifier)] = [link_data]
            if Actions.label in cmd:
                self.labels[cmd[Actions.label]] = (obook, idx)
        return match.group(0)

    def _parse_markdown_cells(self, obook):
        """Appends index entries to project index table."""
        for cell_number, cell in enumerate(obook.md_cells):
            logging.debug(f"\tCell: {cell_number}, Source: {cell.source[:25]}")    
            self._ignore = False
            idx = cell["metadata"][tiedown.utils.Keys.td_cell_index.value]
            self.ptn_action.sub(
                lambda match: self._parser_pass1(match, obook, idx),
                cell.source)

    def _copy_subfolder_contents(self, subfolder, output):
        ignored = self.ignored_files_on_copy
        ignored.extend([".ipynb_checkpoints", ".ipynb"])
        shutil.copytree(
            subfolder, output, ignore=shutil.ignore_patterns(*ignored))

    def _add_section_numbers(self, obook):  
        """Adds section numbers to each output notebook."""
        logging.debug("\t\tAdding Section Numbers")    
        # First check the current content book for numbering instructions.
        # If present, current content book settingw will override
        # template.
        cmds = obook.get_rawcell_commands(0)
        if Actions.outline in cmds:
            if cmds[Actions.outline] != "None":
                obook.number_headers(cmds[Actions.outline])
        # If no outline command in current content book, check the template.
        elif obook.template is not None:
            tcmds = obook.template.get_rawcell_commands(0)
            if Actions.outline in tcmds and tcmds[Actions.outline] != "None":
                obook.number_headers(tcmds[Actions.outline])
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
        logging.info("Starting 2nd Pass")
        for obook in self.iter_notebooks(self.output_path):
            logging.debug("Parsing: %s", obook.path)
            for cell in obook.md_cells:
                self._ignore = False
                source_actions_processed = self.ptn_action.sub(
                    lambda match: self._parser_actions_pass2(match, obook, cell),
                    cell.source)
                cell.source = self.ptn_insert.sub(
                    lambda match: self._parser_inserts_pass2(match, obook, cell),
                    source_actions_processed).strip()
            obook.remove_raw_cells()
            obook.remove_code_outputs()
            obook.write()
        logging.shutdown()

    def _parser_actions_pass2(self, match, obook, cell):
        logging.debug("Match: %s", match)
        logging.debug("Match Group: %s", match.group(1))
        cmd = self._load_commands(match)

        if Actions.end_ignore in cmd and self._ignore:
            self._ignore = False
            return ""
        elif Actions.ignore in cmd and not self._ignore:
            self._ignore = True
            return ""
        elif self._ignore:
            return match.group(0)
        else:
            return ""

    def iter_extension_inserts(self):
        extensions = sorted(self.ext.values(),
                            key=lambda x: x.cellpass2_inserts_priority)
        for extension in extensions:
            for insert in dir(extension.Inserts()):
                yield insert, extension

    def _parser_inserts_pass2(self, match, obook, cell):
        logging.debug("Match: %s", match)
        logging.debug("Match Group: %s", match.group(1))
        cmd = self._load_commands(match)

        for insert, extension in self.iter_extension_inserts():
            if insert in cmd:
                return extension.cellpass2_inserts(match, obook, cell)


        if not self._ignore:
            if Inserts.rel_path in cmd:
                target_label = cmd[Inserts.rel_path]
                target_nb, target_id = self.labels[target_label]
                return target_nb.rel_link_to(obook, cell_id=target_id)
            # elif Inserts.toc in cmd:
            #     return self.write_toc(obook)
            elif Inserts.write_index_section in cmd:
                return self.write_index_section(
                    cmd[Inserts.write_index_section], obook)
            elif Inserts.id in cmd:
                return f'<span id="{cmd["id"]}"/>'
            elif Inserts.link_prev in cmd:
                toc_idx = obook.metadata.get("tiedown.toc_index")
                if toc_idx in [0, None]:
                    return ""
                else:
                    prev_book = self.ext["tiedown_toc"][toc_idx - 1][1]
                    if cmd[Inserts.link_prev] is None:
                        link_text = self.ext["tiedown_toc"][toc_idx - 1][0]
                    else:
                        link_text = cmd[Inserts.link_prev]
                    return f"[{link_text}]({prev_book.rel_link_to(obook)})"
            elif Inserts.link_next in cmd:
                toc_idx = obook.metadata.get("tiedown.toc_index")
                if (toc_idx is None or
                    toc_idx >= len(self.ext["tiedown_toc"]) - 1):
                    return ""
                else:
                    next_book = self.ext["tiedown_toc"][toc_idx + 1][1]
                    if cmd[Inserts.link_next] is None:
                        link_text = self.ext["tiedown_toc"][toc_idx + 1][0]
                    else:
                        link_text = cmd[Inserts.link_next]
                    return f"[{link_text}]({next_book.rel_link_to(obook)})"

        else:
            return match.group(0) # Return match unchanged when ignoring

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
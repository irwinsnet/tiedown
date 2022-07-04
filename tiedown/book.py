
import enum
import os.path
import pathlib
import re

import nbformat
import yaml

import tiedown.utils as utils

class Enums(enum.Enum):
    KB_PAGE_COMMANDS = 0


class Book:
    def __init__(self, path=None):
        if path is None:
            self.book = nbformat.v4.new_notebook()
        else:
            self.book = nbformat.read(path, 4)
        self.path = path
        self.ptn_outline = None

    def __getitem__(self, idx):
        return self.cells[idx]

    def __len__(self):
        return len(self.cells)

    def __getattr__(self, name):
        """Provide nbformat object attributes."""
        return getattr(self.book, name)

    @property
    def raw_cells(self):
        return [cell for cell in self.cells
                if cell["cell_type"] == "raw"]

    @property
    def md_cells(self):
        return [cell for cell in self.cells
                if cell["cell_type"] == "markdown"]

    @property
    def code_cells(self):
        return [cell for cell in self.cells
                if cell["cell_type"] == "code"]

    @staticmethod
    def new_raw(source=None):
        if source is None:
            return nbformat.v4.new_raw_cell()
        else:
            return nbformat.v4.new_raw_cell(source=source)

    @staticmethod
    def new_code(source=None):
        if source is None:
            return nbformat.v4.new_code_cell()
        else:
            return nbformat.v4.new_code_cell(source=source)

    def write(self, path=None):
        if path is None:
            path = self.path
        nbformat.write(self.book, path, 4)

    def get_commands(self, cell):
        if isinstance(cell, int):
            cell = self.cells[cell]
        if cell["cell_type"] == "raw":
            return yaml.load(cell["source"], Loader=yaml.FullLoader)
        else:
            return {}


class Template(Book):
    def get_inserts(self):
        """Extracts all insert commands from the template.

        Returns a list of dictionaries containing the tag and cell
        index:
        [{"tag": "content_tag", "cell_idx": 1},
         {"tag": "a_different_content_tag": 3}
        """
        inserts = []
        for cell_idx, cell in enumerate(self.book.cells):
            cmds = self.get_commands(cell)
            if "insert" in cmds:
                inserts.append({"tag": cmds["insert"], "cell_idx": cell_idx})
        return inserts

    def embed_knotbook(self, cbook):
        """Embeds content from a kntobook into a template.

        Args:
            * kb: A Knotbook object.

        Returns:
            A Knotbook object containing content from both the template
            and the content Knotbook.
        """
        # Create new output notebook
        output_nb = NoteBook()
        if "kernelspec" in self.metadata:
            output_nb.metadata["kernelspec"] = self.metadata["kernelspec"]
        
        # Merge content from template and Knotbook
        content_blocks = cbook.get_blocks()            
        if Enums.KB_PAGE_COMMANDS in content_blocks:
            output_nb.cells.append(content_blocks[Enums.KB_PAGE_COMMANDS][0])
        for cell in self.cells:
            commands = cbook.get_commands(cell)
            if "insert" in commands:
                block_name = commands["insert"]
                if block_name in content_blocks:
                    output_nb.cells.extend(content_blocks[block_name])
            else:
                output_nb.cells.append(cell)
        output_nb.template = self
        return output_nb


class NoteBook(Book):

    def __init__(self, path=None):
        super().__init__(path)
        self.template = None
        self.title = None
        self.links = []

    def get_template_name(self):
        """Determines which template should be used.

        Returns:
            * If None, No template should be used.
            * If the empty string (""), use the default template.
            * Otherwise returns the file name (e.g. my-template.ipynb)
              that should be used for this notebook.
        """
        template = ""  # Case if no {% template ... %} command - use default.
        # Check for {% template ... %} command
        cmds = self.get_commands(0)
        if "template" in cmds:
            if cmds["template"] == "None":
                template = None
            else:
                template = cmds["template"] + ".ipynb"
        return template

    def get_blocks(self):
        """Extracts blocks from a notebook.

        Args:
            notebook: An nbformat notebook object.
        
        Returns: A dictionary. The keys are the block names and the
        values are lists of cells contained in the block. If the
        content notebook contains a command cell, that cell will be
        included in the dictionary with key `Enums.KB_PAGE_COMMANDS`.
        """
        blocks = {}
        if self.get_commands(0):
            blocks[Enums.KB_PAGE_COMMANDS] = [self[0]]

        in_block = False
        block_name = None
        for cell in self.book.cells:
            commands = self.get_commands(cell)
            if not in_block:
                if "block" in commands:
                    in_block = True
                    block_name = commands["block"]
                    blocks[block_name] = []
            else:
                if "endblock" in commands:
                    in_block = False
                    block_name = None
                else:
                    blocks[block_name].append(cell)
        return blocks

    def get_title(self):
        """Finds first H1 Markdown line in notebook. """
        pattern = re.compile(r"^#[^#](.*)$", flags=re.MULTILINE)
        for cell in self.cells:
            if cell["cell_type"] == "markdown":
                match = pattern.search(cell["source"])
                if match is not None:
                    return match.group(1)
        return None

    def rel_link_to(self, from_path=None, cell_id=None):
        """Returns relative link (POSIX) to notebook from another notebook.
        
        Args:
            from_path: A pathlib.Path object from which the relative
                path will be determined.

        Returns: A relative HTML link, suitable for including in
            an <a> tag's href element or in a Markdown link.
        """
        if isinstance(from_path, Book):
            from_path = from_path.path
        from_folder = from_path.parent.as_posix()
        rel_link = os.path.relpath(self.path, from_folder)
        rel_link_posix = pathlib.Path(rel_link).as_posix()
        if cell_id is not None:
            rel_link_posix = f"{rel_link_posix}#{cell_id}"
        return rel_link_posix

    def number_headers(self, outline_format):

        if self.ptn_outline is None:
                    self.ptn_outline = re.compile(
                        r"^(#{2,5})\s(?=[^{]{2})",
                        re.MULTILINE)
        counter = utils.get_counter(outline_format)
        current = [1 for count in counter]
        for cell in self.md_cells:
            lines = cell["source"].split("\n")
            for line_num, line in enumerate(lines):
                match = self.ptn_outline.search(line)
                if match is not None:
                    level = len(match.group(1))
                    numbered_header = (
                        match.group(1) + " " + 
                        counter[level-1](current[level-1]) + ". ")
                    lines[line_num] = self.ptn_outline.sub(numbered_header, line)
                    current[level-1] += 1
                    current[level:] = [1] * (len(current) - level)
            cell["source"] = "\n".join(lines)


    def add_cell_ids(self):
        """Adds a <span> element with a unique ID to each markdown cell."""
        cell_index = 1
        for cell in self.md_cells:
            cell["metadata"][utils.Keys.td_cell_index.value] = f"cid{cell_index}"
            cell_span = f'<span id="cid{cell_index}"/>\n'
            cell["source"] = cell_span + "\n" + cell["source"]
            cell_index += 1

    def remove_raw_cells(self):
        self.book.cells = list(
            filter(lambda x: x["cell_type"] != "raw", self.cells))

    def remove_code_outputs(self):
        for cell in self.code_cells:
            cell["outputs"].clear()
            cell["execution_count"] = None








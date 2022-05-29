
import enum
import re

import nbformat

class Enums(enum.Enum):
    KB_PAGE_COMMANDS = 0



class Book:
    def __init__(self, path=None):
        if path is None:
            self.book = nbformat.v4.new_notebook()
        else:
            self.book = nbformat.read(path, 4)
        self.path = path
        self.pattern_command = re.compile(r"{%\s+(.+)\s+%}")

    def __getitem__(self, idx):
        return self.cells[idx]

    @property
    def cells(self):
        return self.book.cells

    @property
    def metadata(self):
        return self.book.metadata

    @property
    def nbformat(self):
        return self.book.nbformat

    @property
    def nbformat_minor(self):
        return self.book.nbformat_minor

    @staticmethod
    def new_markdown(source=None):
        if source is None:
            return nbformat.v4.new_markdown_cell()
        else:
            return nbformat.v4.new_markdown_cell(source=source)

    @staticmethod
    def new_code(source=None):
        if source is None:
            return nbformat.v4.new_code_cell()
        else:
            return nbformat.v4.new_code_cell(source=source)

    def write(self, path):
        nbformat.write(self, path, 4)


    def get_command(self, cell):
        """Extracts a command and arguments from a cell.
        
        Args:
            cell: A dictionary object from an nbformat notebook object.

        Returns a dictionary with two keys:
            * "command": The command name, such as "insert" or "block".
            * "args": A list of the arguments that followed the command.
                      Returns an empty list if there are no arguments.

        If the cell doesn't contain a command or is not a markdown
        cell, returns {"command": None, "args": []}
        """
        command = {"command": None, "args": []}
        if cell["cell_type"] == "markdown":
            match = self.pattern_command.match(cell["source"])
            if match is not None:
                tokens = match.group(1).split()
                command = {"command": tokens[0].lower(),
                           "args": tokens[1:]}
        return command

    def get_commands(self, cell, as_dict=False):
        """Extracts all commands from a cell.

        Args:
            cell: A nbformat cell string the cell index value.

        Returns a list of command dictionaries, or an empty list if the
        cell contains no commands. For example:
        [{"command": "template", "args": [None]},
         {"command": "link", "args": ["page_1"]}]

        Or if as_dict is True:
        {"template": [None], "link": ["page_1"]}
        """
        if isinstance(cell, int):
            cell = self.cells[cell]
        if cell["cell_type"] == "markdown":
            cmd_strings = self.pattern_command.findall(cell["source"])
            token_lists = [cmd_string.split() for cmd_string in cmd_strings]
            commands = [{"command": tokens[0].lower(), "args": tokens[1:]}
                        for tokens in token_lists]
        else:
            commands = []
        if as_dict:
            commands = {cmd["command"]: cmd["args"] for cmd in commands}
        return commands


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
            cmd = self.get_command(cell)
            if cmd["command"] == "insert" and len(cmd["args"]) >= 1:
                    insert = {"tag": cmd["args"][0],
                              "cell_idx": cell_idx}
                    inserts.append(insert)
        return inserts

    def embed_knotbook(self, kb):
        """Embeds content from a kntobook into a template.

        Args:
            * kb: A Knotbook object.

        Returns:
            A Knotbook object containing content from both the template
            and the content Knotbook.
        """
        # Create new output notebook
        output_nb = Knotbook()
        if "kernelspec" in self.metadata:
            output_nb.metadata["kernelspec"] = self.metadata["kernelspec"]
        
        # Merge content from template and Knotbook
        content_blocks = kb.get_blocks()            
        if Enums.KB_PAGE_COMMANDS in content_blocks:
            output_nb.cells.append(content_blocks[Enums.KB_PAGE_COMMANDS])
        for cell in self.cells:
            commands = kb.get_commands(cell)
            if "insert" in commands:
                block_name = commands["insert"][0]
                if block_name in content_blocks:
                    output_nb.cells.extend(content_blocks[block_name])
            else:
                output_nb.cells.append(cell)
        return output_nb


class Knotbook(Book):

    def get_applicable_template(self):
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
        for cmd in cmds:
            if cmd["command"] == "template":
                if cmd["args"][0] == "None":
                    template = None
                else:
                    template =cmd["args"][0] + ".ipynb"
        return template

    def get_blocks(self):
        """Extracts blocks from a notebook.

        Args:
            notebook: An nbformat notebook object.
        
        Returns: A dictionary. The keys are the block names and the
        values are lists of cells contained in the block.        
        """
        blocks = {}
        if self.get_commands(0, True):
            blocks[Enums.KB_PAGE_COMMANDS] = self[0]

        in_block = False
        block_name = None
        for cell in self.book.cells:
            command = self.get_command(cell)
            if not in_block:
                if command["command"] == "block":
                    in_block = True
                    block_name = command["args"][0]
                    blocks[block_name] = []
            else:
                if command["command"] == "endblock":
                    in_block = False
                    block_name = None
                else:
                    blocks[block_name].append(cell)
        return blocks

    def get_title(self):
        pattern = re.compile(r"^#[^#](.*)$", flags=re.MULTILINE)
        for cell in self.cells:
            if cell["cell_type"] == "markdown":
                match = pattern.search(cell["source"])
                if match is not None:
                    return match.group(1)
        return None


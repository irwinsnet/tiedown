import logging
import tiedown.extension


class Toc(tiedown.extension.Extension):

    class Actions:
        toc_exclude = "toc_exclude"  # Excludes notebook from TOC
        toc_entry = "toc_entry"      # Specify text for TOC entry

        def __dir__(self):
            return ["toc_exclude", "toc_entry"]

    class Inserts:
        toc = "toc"            # Insert a TOC

        def __dir__(self):
            return ["toc"]

    def __init__(self, project):
        super().__init__(project)
        self.set_priorities(3)
        self.name = "tiedown_toc"
        self.toc = []

    def __len__(self):
        return len(self.toc)

    def __getitem__(self, idx):
        return self.toc[idx]

    def bookpass1(self, obook):
        """Adds TOC entry to project toc table."""
        logging.debug("\t\tAppending TOC Entries")      
        cmds = obook.get_rawcell_commands(0)
        if self.actions.toc_exclude not in cmds:
            if self.actions.toc_entry in cmds:
                toc_entry = cmds[self.actions.toc_entry]
            else:
                toc_entry = obook.get_title()
            if toc_entry is not None:
                self.toc.append((toc_entry, obook))
                obook.metadata["tiedown.toc_index"] = len(self.toc) - 1

    def cellpass2_inserts(self, match, obook, cell):
        """Writes Table of Contents (TOC).
        
        Args:
            obook: Output notebook that will contain TOC.

        Returns: TOC as HTML text.        
        """
        toc_table = []
        entry_num = 1
        for entry in self.toc:
            text = entry[0]
            link = entry[1].rel_link_to(obook)
            toc_table.append(f"{entry_num}. [{text}]({link})")
            entry_num += 1
        return "\n".join(toc_table)

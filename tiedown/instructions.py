
class Actions():
    # Assigns label to notebook, can be used to create relative path.
    label = "label"
    # Template Actions
    block = "block"          # Starts a content block
    endblock = "endblock"    # Ends a conent block
    insert = "insert"        # Inserts content block into template
    template = "template"    # Specifies which template should be used.
    # Table of Content Actions
    toc_exclude = "toc_exclude"  # Excludes notebook from TOC
    toc_entry = "toc_entry"      # Specify text for TOC entry
    # Section Numbering
    outline = "outline"     # Sets section numbering formats
    skip = "skip"           # Skips header when numbering
    # Index Actions
    index = "index"                  # Identifies index terms
    code = "code"                    # Highlights term as code
    preserve_case = "preserve_case"  # Do not change term to title case
    # Ignore tiedown commands in cell
    ignore = "ignore"
    end_ignore = "end_ignore"

class Inserts():
    toc = "toc"            # Insert a TOC
    rel_path = "rel_path"  # Creates a relative path to another notebook
    write_index_section = "write_index_section"  # Writes part of index
    id = "id"
    link_prev = "link_prev"
    link_next = "link_next"



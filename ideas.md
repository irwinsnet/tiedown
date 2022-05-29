# Design Ideas for Knotbook Package
Knotbooks is used to create an ordered collection of Jupyter notebooks. Each
notebook is like a chapter in a book or a section in a long document. Unlike
the *Jupyter {book}* package, knotbooks is not intended to convert notebooks
to a different file format (i.e., PDF, HTML). Each notebook will remain
an interactive notebook with text and code cells.

The word *knot* in knotbooks implies that knotbooks *ties everything
together*.

## Features
### Templates
Users will create a notebook template that defines headers and footers and
other content that will be the same for each notebook. The template itself
will be a Jupyter notebook, with a special markdown syntax for specifying
where content from other notebooks should be placed.

### Automatic Section Numbering
It's common for notebook authors to use markdown header tags to create
an outline structure. Unless Jupyter extensions are used, authors must
manually maintain the outline numbering system. This is tedious. Knotbooks
will automatically number notebook sections.

### Table of Content Generation
Knotbooks will automatically create a hyperlinked table of contents
that can be placed in any notebook.

### Index Generation
Knotbooks will create a searchable index of tems.

### Internal Hyperlink Generation
Maintaining internal hyperlinks is a pain because the paths change
frequently as we edit our notebooks. Knotbooks provides a path-independent
mechanism to specify and generate hyperlinks.

### Variable Substitution
Knotbooks will have local and global variables that will be able to be
substituted into notebooks and templates.

## Workflow
Knotbooks uses standard Jupyter notebooks, using standard markdown as much as
possible to define special knotbook features. Knotbooks adds a special syntax,
inspired by Jinja, for specifying index terms, internal hyperlinks, etc.

Knotbooks primarily uses a Jupyter notebook as a user interface. A 
command-line interface is also available.
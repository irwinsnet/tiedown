# Knotbooks Commands

## Templates
```{% template <template_name> %}```
* Used in a content file.
* Specifies which template the content should be inserted into.
* Looks for a template file called `<template_name>.py` located in the *templates* folder.
* If `<template_name>` is set to `None`, no template is used.
* If this command is missing, Knotbooks will use the `main.py` template.

```{% block: <block_name> %}```
* Used in a content file.
* Identifies the start of a block.

```{% endblock %}```
* Used in a content file.
* Identifies the end of a block.

```{% insert <block_name> %}```
* Used in a template file.
The commend cell will be replaced with the block named `<block_name>`.

### Template Notes
* Blocks cannot be nested.
* Template commands are cell commands, meaning there can be no other
  content in a markdown cell that contains a template command.

## Links
```{{ rel_link <page_name> }}```
* Used in content or template file.
* Creates internal hyperlink to notebook with corresponding target command.
* Place link text in square brackets before rel_link command. Example:
  `[This page contains cool stuff.]{{rel_link: page-with-cool-stuff}}`

```{% target <page_name> %}```
* Used in content file.
* Should be placed in first cell of notebook.

```{{ id: section_id}}```
* Used in content or template file
* Creates a `<span>` tag with the specified id attribute.

## Table of Contents (TOC)
```{% toc_entry <toc_entry>%}```
* If this command is included, the TOC will use `<toc_entry>` in the
table of contents. Otherwise, Knotbooks will find the first top-level
markdown heading and use that as the TOC entry. Note that knotbooks
searches the content file for the first H1 (i.e., '#') heading.
It will ignore H1 headings that appear in the template file.

```{% toc_exclude %}```
* Exclude from Table of Contents

```{{ toc }}```
Insert table of contents at this location.

## Section Numbering
Section numbering parameters will be defined in the template, so that
all documents that use the same template will have the same numbering
scheme. The available sequences will be:
* I: Uppercase Roman numerals
* i: Lowercase Roman numerals
* 1: Integers
* A: Uppercase letters
* a: Lowercase letters

```{% outline I.A.1.a %}```
Outline numbering will be defined as a string. For example, "I.A.1.a" will
cause the H2 headers to use uppercase Roman numerals, H3 headers to use
Uppercase letters, etc. (H1 headers are only used for the page title.)
All numbers will be separated with a period.

If the `{% outline ... %}` command is omitted from the template, there
will be no automatic section numbering.

If the `{% outline ... %}` is present in the knotbook, it will override
the template's `{% outline ... %}` command. The command `{% outline None %}`
in a content book will prevent section numbers from being added to the
notebook.

To skip a header, place {% skip %} in front of the header text.

To place the outline number somewhere other than the beginning of the
line, place {{number}} at the desired location.

## Variables
Variables can't use the following reserved names:
* `toc`
* `skip`
* `rel_link`

Define variables in top command cell.
`{% define mod_date 2022-06-04 }`



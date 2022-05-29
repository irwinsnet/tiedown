# Knotbooks Commands

## Templates
```{% template <template_name> %}```
* Used in a content file.
* Specifies which template the content should be inserted into.
* Looks for a template file called `<template_name>.py` located in the *templates* folder.
* If `<template_name>` is set to `None`, no template is used.
* If this command is missing, Knotbooks will use the `main.py` template.

```{% block <block_name> %}```
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

```{% target <page_name> %}```
* Used in content file.
* Should be placed in first cell of notebook.

## Table of Contents (TOC)
```{% toc_entry <toc_entry>%}```
* If this command is included, the TOC will use `<toc_entry>` in the
table of contents. Otherwise, Knotbooks will find the first top-level
markdown heading and use that as the TOC entry. 

```{% toc_exclude %}```
* Exclude from Table of Contents



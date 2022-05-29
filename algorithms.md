# Algorithms

## Notebook Build Sequence
1. Create a new, empty output path.
2. Call knotbook iterator to get a content file.
3. Identify correct template
4. Build output notebook from template and content file, or just 
   content file if `{% tempate None %}` is specified.
5. Scan output notebook for more commands, filling in variables, links, etc.
6. Copy supporting files, e.g., images, data, etc., to output folder
7. Build table of contents and index.

## Command Parsing
* The command must appear at the very beginning of the markdown cell.
  Otherwise it will not be recognized (uses `re.match()`).
* Matches a string starting with `{% ` and ` %}`. Note there must be
  whitespace immedeiately after the opening token and immediately before
  the closing token. Pattern is `r"{%\s+(.+)\s+%}"`
* The `.split()` method will be run on the matched string. This will
  split the string into tokens using any whitespae as a delimeter.
* The first token is automatically converted to lower case by `get_command()`.
* Will need to refactor later to use `re.findall()`, but am using something
  simple for now.
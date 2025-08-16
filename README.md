# Introduction

`pytex` automates the entire processing pipeline to generate a PDF from .tex
files. It is strongly based on the script with the same name developed by
[Stefan Schinkel](https://github.com/stefanSchinkel/pytex). Indeed, I used that
script for years!

It supports:

- Different encodings.
- Cross-references.
- Tables of Contents, Figures, etc.
- Bibliographical references. Only `bibtex` and `biber` are fully supported
- Index creation. Only `makeindex` and `splitindex` are fully supported

and it provides a meaningful view of the important messages generated:

- It parses the output generated and shows only the relevant warnings.
- If a bib or index tool is required to be executed it shows the entire output
  since this is usually very manageable in size.

It is very similar to `rubber` with the exception that it provides support for
index creation.

Hence, from a given `.tex` file it runs a processor (e.g., `latex`, `pdflatex`,
`xelatex`, etc.), and it immediately after guesses the following steps: whether
to process bib directives, index entries, re-compile, etc. Some pathological
files might require an arbitrary number of passes. The maximum number is set to
5 and in case this limit is reached the user is warned.

# Install

The package will be eventually available in Pypi. In the meantime, just clone
the repo:

``` sh
    $ git clone https://github.com/clinaresl/pytex
```

and install the package in your Python ecosystem with:

``` sh
    $ python -m build .
    $ python -m pip install dist/pytex-*.whl

```

from the root directory of `pytex`. Installing the software will make the script
`pytex` available in your system.

# Usage

`pytex` supports the `--help` directive. The only mandatory argument is the name
of the main `.tex` file to process, e.g.:

``` sh
 $ pytex main
 Using encoding UTF-8
 pdflatex main.tex
 ./examen.sty
	[Package pgf Warning] This package is obsolete. Use \usetikzlibrary {arrows} ins tead on input line 10.
	[Package pgf Warning] This package is obsolete. Use \usetikzlibrary {snakes} ins tead on input line 11.
	[Package pgf Warning] Snakes have been superseded by decorations. Use the decora tion libraries instead of the snakes library on input line 12.
	[LaTeX Warning] Reference `ex2025:jun:2:a' on page 3 undefined on input line 244 .
	[LaTeX Warning] Reference `tab:curso-1' on page 3 undefined on input line 252.
	[LaTeX Warning] Reference `tab:curso-4' on page 3 undefined on input line 252.

 ./ejercicio-3.tex
	[Package tabularx Warning] X Columns too narrow (table too wide) (tabularx) on input line 43.
	[Class exam Warning] Point totals have changed. Rerun to get point totals right.

 ./main.aux
	[LaTeX Warning] There were undefined references.
	[LaTeX Warning] Label(s) may have changed. Rerun to get cross-references right.

 No errors found
 Number of warnings: 10

 pdflatex main.tex
 ./examen.sty
	[Package pgf Warning] This package is obsolete. Use \usetikzlibrary {arrows} ins tead on input line 10.
	[Package pgf Warning] This package is obsolete. Use \usetikzlibrary {snakes} ins tead on input line 11.
	[Package pgf Warning] Snakes have been superseded by decorations. Use the decora tion libraries instead of the snakes library on input line 12.

 ./ejercicio-3.tex
	[Package tabularx Warning] X Columns too narrow (table too wide) (tabularx) on input line 43.
	[Class exam Warning] Point totals have changed. Rerun to get point totals right.

 ./main.aux
	[LaTeX Warning] Label(s) may have changed. Rerun to get cross-references right.

 No errors found
 Number of warnings: 6

 pdflatex main.tex
 ./examen.sty
	[Package pgf Warning] This package is obsolete. Use \usetikzlibrary {arrows} ins tead on input line 10.
	[Package pgf Warning] This package is obsolete. Use \usetikzlibrary {snakes} ins tead on input line 11.
	[Package pgf Warning] Snakes have been superseded by decorations. Use the decora tion libraries instead of the snakes library on input line 12.

 ./ejercicio-3.tex
	[Package tabularx Warning] X Columns too narrow (table too wide) (tabularx) on input line 43.

 No errors found
 Number of warnings: 4

 main.pdf generated
```

In this case, the same file (`main.tex`) had to be processed three times. In
each pass, it provides information about the warnings generated under the file where they were found.

It is also possible to avoid all these messages with `--quiet` (the following
example being run on a different case than the previous one):

``` sh
 $ pytex main --quiet
 Using encoding UTF-8
 pdflatex main.tex
 Number of warnings: 28
 bibtex main
	This is BibTeX, Version 0.99d (TeX Live 2026/dev/Arch Linux)
	The top-level auxiliary file: main.aux
	The style file: dinat.bst
	Database file #1: main.bib
 splitindex main
	This is makeindex, version 2.17 [TeX Live 2026/dev] (kpathsea + Thai support).
	Scanning input file main-keywords.idx....done (321 entries accepted, 0 rejected).
	Sorting entries......done (3057 comparisons).
	Generating output file main-keywords.ind....done (234 lines written, 0 warnings).
	Output written in main-keywords.ind.
	Transcript written in main-keywords.ilg.
	This is makeindex, version 2.17 [TeX Live 2026/dev] (kpathsea + Thai support).
	Scanning input file main-concepts.idx....done (351 entries accepted, 0 rejected).
	Sorting entries......done (3171 comparisons).
	Generating output file main-concepts.ind....done (339 lines written, 0 warnings).
	Output written in main-concepts.ind.
	Transcript written in main-concepts.ilg.
 pdflatex main.tex
 Number of warnings: 28
 splitindex main
	This is makeindex, version 2.17 [TeX Live 2026/dev] (kpathsea + Thai support).
	Scanning input file main-concepts.idx....done (351 entries accepted, 0 rejected).
	Sorting entries......done (3171 comparisons).
	Generating output file main-concepts.ind....done (339 lines written, 0 warnings).
	Output written in main-concepts.ind.
	Transcript written in main-concepts.ilg.
	This is makeindex, version 2.17 [TeX Live 2026/dev] (kpathsea + Thai support).
	Scanning input file main-keywords.idx....done (321 entries accepted, 0 rejected).
	Sorting entries......done (3057 comparisons).
	Generating output file main-keywords.ind....done (234 lines written, 0 warnings).
	Output written in main-keywords.ind.
	Transcript written in main-keywords.ilg.
 pdflatex main.tex
 Number of warnings: 26
 main.pdf generated

```

In this case, it was necessary to process both *bib* and *index* entries. As it
can be seen, its output is shown even if `--quiet` is given, because it is
manageable in size. Warnings generated when processing the `.tex` file are not
shown, but every pass informs about the number of warnings found which can be
checked in the corresponding `.aux` file or just by running `pytex` again
without `--quiet`.

Other than that, `pytex` accepts specific hints for the processor, the bib and
index tools with `--processor`, `--bib` and `--index`. The default value for the
processor is `pdflatex`. The correct values for the bib and index tools are
guessed so that in general there is no need to provide them.

To ease embedding `pytex` into other workflows (e.g., makefile), it is also
possible to provide the name of the resulting PDF file with `--output`. If it is
not given, the resulting PDF file will be named after the main tex file
processed.

# Acknowledgements

To Stefan Schinkel, whose work I used for several years in many of my projects.

# License

MIT License

Copyright (c) 2025 Carlos Linares López

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

# Author #

Carlos Linares Lopez <carlos.linares@uc3m.es>  
Computer Science and Engineering Department <https://www.inf.uc3m.es/en>  
Universidad Carlos III de Madrid <https://www.uc3m.es/home>

# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = "local-ai-pi"
copyright = "2026, local-ai-pi contributors"
author = "local-ai-pi contributors"

extensions = [
    "myst_parser",  # MyST Markdown support
    "sphinx.ext.viewcode",  # Add links to source code
    "sphinx.ext.todo",  # Support for to do items
    "sphinx.ext.intersphinx",  # Cross-reference external docs
]

# MyST configuration
myst_parse_frontmatter = True
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "smartquotes",
    "substitution",
    "tasklist",
]

pygments_style = "sphinx"
pygments_dark_style = "monokai"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_static_path = ["_static"]

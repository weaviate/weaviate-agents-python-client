# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "weaviate-agents-python-client"
copyright = "2025, Weaviate"
author = "Weaviate"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "sphinxcontrib.autodoc_pydantic",
]

# Autodoc settings for pydantic
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_model_undoc_members = False
autodoc_pydantic_model_members = False

autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_dataclass_fields = False

# Make sure the target is unique
autosectionlabel_prefix_document = True

autoclass_content = "both"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "README.rst"]

suppress_warnings = [
    "docutils",
    "autodoc",
    "autosectionlabel",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


import re


def convert_markdown_links(lines):
    """Convert Markdown-style [text](url) links to reST-style `text <url>`_ links."""
    md_link_pattern = re.compile(r"\[([^\]]+)\]\((http[^\)]+)\)")
    return [md_link_pattern.sub(r"`\1 <\2>`_", line) for line in lines]


def autodoc_process_docstring(app, what, name, obj, options, lines):
    """Apply the conversion to all docstrings."""
    lines[:] = convert_markdown_links(lines)


def setup(app):
    app.add_css_file("custom.css")
    app.connect("autodoc-process-docstring", autodoc_process_docstring)

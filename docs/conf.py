# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------

project = "AGRF Documentation"
copyright = "2025, Ahyangyi"
author = "Ahyangyi"

# -- General configuration ---------------------------------------------------

extensions = ["myst_parser"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]

# Theme options for Furo
html_theme_options = {
    "light_css_variables": {"color-brand-primary": "#2962FF", "color-brand-content": "#2962FF"},
    "dark_css_variables": {"color-brand-primary": "#82B1FF", "color-brand-content": "#82B1FF"},
}

# The master toctree document.
master_doc = "index"

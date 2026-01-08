"""
PyInstaller hook for Flask and extensions.

Ensures Flask templates and static files are properly included.
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all Flask submodules
hiddenimports = collect_submodules('flask')
hiddenimports += collect_submodules('werkzeug')
hiddenimports += collect_submodules('jinja2')

# Additional hidden imports
hiddenimports += [
    'flask.app',
    'flask.blueprints',
    'flask.cli',
    'flask.config',
    'flask.ctx',
    'flask.globals',
    'flask.helpers',
    'flask.json',
    'flask.logging',
    'flask.sessions',
    'flask.signals',
    'flask.templating',
    'flask.views',
    'flask.wrappers',
    'werkzeug.routing',
    'werkzeug.security',
    'werkzeug.serving',
    'werkzeug.urls',
    'werkzeug.utils',
    'jinja2.ext',
    'markupsafe',
]

# Collect data files
datas = collect_data_files('flask', include_py_files=True)
datas += collect_data_files('werkzeug', include_py_files=True)
datas += collect_data_files('jinja2', include_py_files=True)

"""
PyInstaller hook for Celery.

Ensures all Celery modules are properly included in the executable.
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all Celery submodules
hiddenimports = collect_submodules('celery')
hiddenimports += collect_submodules('kombu')
hiddenimports += collect_submodules('billiard')

# Additional hidden imports that might be missed
hiddenimports += [
    'celery.app',
    'celery.app.task',
    'celery.app.base',
    'celery.worker',
    'celery.backends',
    'celery.backends.redis',
    'celery.concurrency',
    'celery.concurrency.prefork',
    'celery.concurrency.solo',
    'celery.concurrency.threads',
    'kombu.transport.redis',
    'kombu.serialization',
    'billiard.pool',
    'billiard.process',
]

# Collect data files if any
datas = collect_data_files('celery', include_py_files=True)

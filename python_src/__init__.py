__version__ = '1.18b'

def version():
    return __version__

from .database import get_tables, get_DT_tables, manifolds_path, original_manifolds_path

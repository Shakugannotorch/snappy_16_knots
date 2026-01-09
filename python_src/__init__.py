__version__ = '1.00'

def version():
    return __version__

from .database import get_tables, get_DT_tables, manifolds_path, original_manifolds_path

try:
    import snappy
    table_dict = snappy.database.add_tables_from_package('snappy_16_knots', False)
    for name, table in table_dict.items():
        setattr(snappy, name, table)
        if name not in snappy.database_objects:
            snappy.database_objects.append(name)
except ImportError:
    raise RuntimeError('Error happened when loading data of knots of 16 crossings to SnapPy')
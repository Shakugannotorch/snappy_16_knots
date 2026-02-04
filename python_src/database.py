from __future__ import print_function
import sys, sqlite3, re, os, random
import snappy_15_knots

# This module uses sqlite3 databases with multiple tables.
# The path to the database file is specified at the module level.
from .sqlite_files import __path__ as manifolds_paths
manifolds_path = manifolds_paths[0]
database_path = os.path.join(manifolds_path, '16_knots.sqlite')

split_filling_info = re.compile('(.*?)((?:\([0-9 .+-]+,[0-9 .+-]+\))*$)')

original_manifolds_path = snappy_15_knots.manifolds_path
original_database_path = os.path.join(original_manifolds_path, '15_knots.sqlite')

def get_tables(ManifoldTable):
    """
    Functions such as this one are meant to be called in the
    __init__.py module in snappy proper.  To avoid circular imports,
    it takes as argument the class ManifoldTable from database.py in
    snappy. From there, it builds all of the Manifold tables from, for example
    here the sqlite databases 16_knots.sqlite in manifolds_src and 
    15_knots.sqlite from snappy_15_knots, and returns the merged table as
    an element in a list.
    """

    class LinkExteriorsTable(ManifoldTable):
        """
        Link exteriors usually know a DT code describing the assocated link.
        """
        _select = 'select name, triangulation, DT from %s '

        def _finalize(self, M, row):
            M.set_name(row[0])
            M._set_DTcode(row[2])


    class HTLinkExteriors(LinkExteriorsTable):
        """
        This table extends the HTLinkExteriors table from snappy_15_knots
        with 16 crossing knots (no links with multiple components),
        by attaching this table of 16 crossing knots to the table in snappy_15_knots

        >>> HTLinkExteriors.identify(LinkExteriors['8_20'])
        K8n1(0,0)
        >>> Mylist = HTLinkExteriors(alternating=False)[32.0:32.1]
        >>> len(Mylist)
        4
        >>> for L in Mylist:
        ...   print( L.name(), L.volume() )
        ... 
        K16n883306 32.0352925448859
        K16n916708 32.0248070639116
        K16n931674 32.0386444405200
        K16n996627 32.0366528043146
        """

        _regex = re.compile('[KL][0-9]+[an]([0-9]+)$')
        
        def __init__(self, **kwargs):
            LinkExteriorsTable.__init__(self,
                                        table='HT_links_view',
                                        db_path=original_database_path,
                                        **kwargs)

            view_name = 'all_HT_links_view'

            conn = self._connection
            cursor = conn.cursor()

            # Dictionary specifying tables to append
            # Keys: paths of databases -> Values: tables contained by given databases
            # All tables specified will be appended to the view <view_name>
            sql_dict = {
                database_path : ['HT_links']
            }

            table_dict = dict() 
            # records the aliases of databases containing a given table
            alias_dict = dict() 
            # records the alias of a given database file (1-to-1)

            for i, sql_path in enumerate(sql_dict.keys(), start = 1):
                alias = f'db{i}'
                alias_dict.update({sql_path : alias})

                for table_name in sql_dict[sql_path]:
                    if table_name not in table_dict.keys():
                        table_dict.update({table_name : [alias]})
                    else:
                        table_dict.update({table_name : table_dict[table_name] + [alias]})

                cursor.execute('ATTACH DATABASE ? AS ?', (sql_path, alias))

            select_statements = [f'SELECT * FROM {self._table}']
            for table_name in table_dict.keys():
                for alias in table_dict[table_name]:
                    select_statements.append(f"SELECT * FROM {alias}.{table_name}")
            union_query = ' UNION ALL '.join(select_statements)

            create_view_sql = f"CREATE TEMPORARY VIEW {view_name} AS {union_query}"
            cursor.execute(create_view_sql)
            cursor.close()

            self._table = view_name
            self._select = f'select name, triangulation, DT, id from {view_name} '

            self._get_length()
            self._get_max_volume()
                            
        def _configure(self, **kwargs):
            """
            Process the ManifoldTable filter arguments and then add
            the ones which are specific to links.
            """
            ManifoldTable._configure(self, **kwargs)
            conditions = []

            alt = kwargs.get('alternating', None)
            if alt == True:
                conditions.append("name like '%a%'")
            elif alt == False:
                conditions.append("name like '%n%'")
            flavor = kwargs.get('knots_vs_links', None)
            if flavor == 'knots':
                conditions.append('cusps=1')
            elif flavor == 'links':
                conditions.append('cusps>1')
            if 'crossings' in kwargs:
                N = int(kwargs['crossings'])
                conditions.append(
                    "(name like '_%da%%' or name like '_%dn%%')"%(N,N))
            if self._filter:
                if len(conditions) > 0:
                    self._filter += (' and ' + ' and '.join(conditions))
            else:
                self._filter = ' and '.join(conditions)

    return [HTLinkExteriors()]

def connect_to_db(db_path):
    """
    Open the given sqlite database, ideally in read-only mode.
    """
    if sys.version_info >= (3,4):
        uri = 'file:' + db_path + '?mode=ro'
        return sqlite3.connect(uri, uri=True)
    elif sys.platform.startswith('win'):
        try:
            import apsw
            return apsw.Connection(db_path, flags=apsw.SQLITE_OPEN_READONLY)
        except ImportError:
            return sqlite3.connect(db_path)
    else:
        return sqlite3.connect(db_path)

def get_DT_tables():
    """
    Returns a barebone databases for looking up DT codes by name. 
    """
    class DTCodeTable(object):
        """
        A barebones database for looking up a DT code by knot/link name.
        """
        def __init__(self, name='', table='', db_path=database_path, **filter_args):
            self._table = table
            self._select = 'select DT from ' + table + ' '
            self.name = name
            self._connection = connect_to_db(db_path)
            self._cursor = self._connection.cursor()

        def __repr__(self):
            return self.name

        def __getitem__(self, link_name):
            select_query = self._select + ' where name="{}"'.format(link_name)
            return self._cursor.execute(select_query).fetchall()[0][0]
        
        def __len__(self):
            length_query = 'select count(*) from ' + self._table
            return self._cursor.execute(length_query).fetchone()[0]

    class ExtendedDTCodeTable(DTCodeTable):
        """
        This table extends the DTCodeTable from snappy_15_knots,
        appending the 16 crossing knots.
        """
        def __init__(self, **kwargs):
            DTCodeTable.__init__(self, 
                                 table = 'HT_links_view',
                                 db_path = original_database_path,
                                 **kwargs)
            
            view_name = 'all_HT_links_view'

            conn = self._connection
            cursor = conn.cursor()

            # Dictionary specifying tables to append
            # Keys: paths of databases -> Values: tables contained by given databases
            # All tables specified will be appended to the view <view_name>
            sql_dict = {
                database_path : ['HT_links']
            }

            table_dict = dict() 
            # records the aliases of databases containing a given table
            alias_dict = dict() 
            # records the alias of a given database file (1-to-1)

            for i, sql_path in enumerate(sql_dict.keys(), start = 1):
                alias = f'db{i}'
                alias_dict.update({sql_path : alias})

                for table_name in sql_dict[sql_path]:
                    if table_name not in table_dict.keys():
                        table_dict.update({table_name : [alias]})
                    else:
                        table_dict.update({table_name : table_dict[table_name] + [alias]})

                cursor.execute('ATTACH DATABASE ? AS ?', (sql_path, alias))

            select_statements = [f'SELECT * FROM {self._table}']
            for table_name in table_dict.keys():
                for alias in table_dict[table_name]:
                    select_statements.append(f"SELECT * FROM {alias}.{table_name}")
            union_query = ' UNION ALL '.join(select_statements)

            create_view_sql = f"CREATE TEMPORARY VIEW {view_name} AS {union_query}"
            cursor.execute(create_view_sql)
            cursor.close()

            self._table = view_name
            self._select = f'select DT from {view_name} '
            
    return [ExtendedDTCodeTable()]
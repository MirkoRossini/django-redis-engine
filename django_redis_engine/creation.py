from djangotoolbox.db.base import NonrelDatabaseCreation

TEST_DATABASE_PREFIX = 'test_'

class DatabaseCreation(NonrelDatabaseCreation):
    """Database Creation class.
    """
    data_types = {
        'DateTimeField':                'datetime',
        'DateField':                    'date',
        'TimeField':                    'time',
        'FloatField':                   'float',
        'EmailField':                   'unicode',
        'URLField':                     'unicode',
        'BooleanField':                 'bool',
        'NullBooleanField':             'bool',
        'CharField':                    'unicode',
        'CommaSeparatedIntegerField':   'unicode',
        'IPAddressField':               'unicode',
        'SlugField':                    'unicode',
        'FileField':                    'unicode',
        'FilePathField':                'unicode',
        'TextField':                    'unicode',
        'XMLField':                     'unicode',
        'IntegerField':                 'int',
        'SmallIntegerField':            'int',
        'PositiveIntegerField':         'int',
        'PositiveSmallIntegerField':    'int',
        'BigIntegerField':              'int',
        'GenericAutoField':             'objectid',
        'StringForeignKey':             'objectid',
        'AutoField':                    'objectid',
        'RelatedAutoField':             'objectid',
        'OneToOneField':                'int',
        'DecimalField':                 'float',
    }

    def sql_indexes_for_field(self, model, field, **kwargs):
        """Create Indexes for field in model. 

        Indexes are created rundime, no need for this.
	Returns an empty List. (Django Compatibility)
        """

        """if field.db_index:
            kwargs = {}
            opts = model._meta
            col = getattr(self.connection.db_connection, opts.db_table)
            descending = getattr(opts, "descending_indexes", [])
            direction =  (field.attname in descending and -1) or 1
            kwargs["unique"] = field.unique
            col.ensure_index([(field.name, direction)], **kwargs)"""
        return []

    def index_fields_group(self, model, group, **kwargs):
        """Create indexes for fields in group that belong to model.
            TODO: Necessary?
        """
        """if not isinstance(group, dict):
            raise TypeError("Indexes group has to be instance of dict")

        fields = group.pop("fields")

        if not isinstance(fields, (list, tuple)):
            raise TypeError("index_together fields has to be instance of list")

        opts = model._meta
        col = getattr(self.connection.db_connection, opts.db_table)
        checked_fields = []
        model_fields = [ f.name for f in opts.local_fields]

        for field in fields:
            field_name = field
            direction = 1
            if isinstance(field, (tuple, list)):
                field_name = field[0]
                direction = (field[1] and 1) or -1
            if not field_name in model_fields:
                from django.db.models.fields import FieldDoesNotExist
                raise FieldDoesNotExist('%s has no field named %r' % (opts.object_name, field_name))
            checked_fields.append((field_name, direction))
        col.ensure_index(checked_fields, **group)"""

    def sql_indexes_for_model(self, model, *args, **kwargs):
        """Creates ``model`` indexes.

        Probably not necessary 
	TODO Erase?
        """
        """if not model._meta.managed or model._meta.proxy:
            return []
        fields = [f for f in model._meta.local_fields if f.db_index]
        if not fields and not hasattr(model._meta, "index_together") and not hasattr(model._meta, "unique_together"):
            return []
        print "Installing index for %s.%s model" % (model._meta.app_label, model._meta.object_name)
        for field in fields:
            self.sql_indexes_for_field(model, field)
        for group in getattr(model._meta, "index_together", []):
            self.index_fields_group(model, group)

        #unique_together support
        unique_together = getattr(model._meta, "unique_together", [])
        # Django should do this, I just wanted to be REALLY sure.
        if len(unique_together) > 0 and isinstance(unique_together[0], basestring):
            unique_together = (unique_together,)
        for fields in unique_together:
            group = { "fields" : fields, "unique" : True}
            self.index_fields_group(model, group)"""
        return []

    def sql_create_model(self, model, *args, **kwargs):
        """TODO delete...
        """
	return [], {}
        

    def set_autocommit(self):
        "Make sure a connection is in autocommit mode."
        pass

    def create_test_db(self, verbosity=1, autoclobber=False):
        if self.connection.settings_dict.get('TEST_NAME'):
            test_database_name = self.connection.settings_dict['TEST_NAME']
        elif 'NAME' in self.connection.settings_dict:
            test_database_name = TEST_DATABASE_PREFIX + self.connection.settings_dict['NAME']
        elif 'DATABASE_NAME' in self.connection.settings_dict:
            if self.connection.settings_dict['DATABASE_NAME'].startswith(TEST_DATABASE_PREFIX):
                test_database_name = self.connection.settings_dict['DATABASE_NAME']
            else:
                test_database_name = TEST_DATABASE_PREFIX + \
                  self.connection.settings_dict['DATABASE_NAME']
        else:
            raise ValueError("Name for test database not defined")

        self.connection.settings_dict['NAME'] = test_database_name
        # This is important. Here we change the settings so that all other code
        # thinks that the chosen database is now the test database. This means
        # that nothing needs to change in the test code for working with
        # connections, databases and collections. It will appear the same as
        # when working with non-test code.

        # In this phase it will only drop the database if it already existed
        # which could potentially happen if the test database was created but
        # was never dropped at the end of the tests
        self._drop_database(test_database_name)

        return test_database_name

    def destroy_test_db(self, old_database_name, verbosity=1):
        """
        Destroy a test database, prompting the user for confirmation if the
        database already exists. Returns the name of the test database created.
        """
        if verbosity >= 1:
            print "Destroying test database '%s'..." % self.connection.alias
        test_database_name = self.connection.settings_dict['NAME']
        self._drop_database(test_database_name)
        self.connection.settings_dict['NAME'] = old_database_name

    def _drop_database(self, database_name):
        """Drops the database with name database_name
	
        """
        for k in self.connection._cursor().keys(database_name+'*'):
		del self.connection._cursor()[k]

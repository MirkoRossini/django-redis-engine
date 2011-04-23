from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

import redis
from .creation import DatabaseCreation
from .client import DatabaseClient

from djangotoolbox.db.base import (
    NonrelDatabaseFeatures,
    NonrelDatabaseWrapper,
    NonrelDatabaseValidation,
    NonrelDatabaseIntrospection,
    NonrelDatabaseOperations
)

from datetime import datetime

class ImproperlyConfiguredWarning(Warning):
    pass

class DatabaseFeatures(NonrelDatabaseFeatures):
    string_based_auto_field = True
    supports_dicts = True

class DatabaseOperations(NonrelDatabaseOperations):
    compiler_module = __name__.rsplit('.', 1)[0] + '.compiler'

    def max_name_length(self):
        return 254

    def check_aggregate_support(self, aggregate):
        raise NotImplementedError("django-redis-engine does not support %r "
                                      "aggregates" % type(aggregate))

    def sql_flush(self, style, tables, sequence_list):
        """
        Returns a list of SQL statements that have to be executed to drop
        all `tables`. Not implemented yes, returns an empty list.
        """
        
        return []

    def value_to_db_date(self, value):
        if value is None:
            return None
        return datetime(value.year, value.month, value.day)

    def value_to_db_time(self, value):
        if value is None:
            return None
        return datetime(1, 1, 1, value.hour, value.minute, value.second,
                                 value.microsecond)


class DatabaseValidation(NonrelDatabaseValidation):
    pass


class DatabaseIntrospection(NonrelDatabaseIntrospection):
    """Database Introspection"""

    def table_names(self):
        """ Show defined models """
        return []#self.connection.db_connection.collection_names()

    def sequence_list(self):
        # Only required for backends that support ManyToMany relations
        pass


class DatabaseWrapper(NonrelDatabaseWrapper):
    safe_inserts = False
    wait_for_slaves = 0
    _connected = False

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.validation = DatabaseValidation(self)
        self.introspection = DatabaseIntrospection(self)

    def _cursor(self):
	
	try:
		return self._connection
	except:
		pass
        self._connect()
        return self._connection

    @property
    def db_connection(self):
        """
        Returns the db_connection instance
         
        """
	try:
		if self._connection is not None:
			return self._connection
	except:
	        self._connect()
        return self._db_connection

    def _connect(self):
	import traceback
	import sys
	#print '-------------------'
	#traceback.print_stack()
	#print '-------------------'
        if not self._connected:
            host = self.settings_dict['HOST'] or None
            port = self.settings_dict.get('PORT', None) or None
            user = self.settings_dict.get('USER', None)
            password = self.settings_dict.get('PASSWORD')
            self.db_name = self.settings_dict['NAME']
            try:
              self.exact_all = settings.REDIS_EXACT_ALL
            except AttributeError:
              self.exact_all = True

            self.safe_inserts = self.settings_dict.get('SAFE_INSERTS', False)

            self.wait_for_slaves = self.settings_dict.get('WAIT_FOR_SLAVES', 0)
            slave_okay = self.settings_dict.get('SLAVE_OKAY', False)

            try:
                if host is not None:
                    assert isinstance(host, basestring), \
                    'If set, HOST must be a string'

                if port:
                    try:
                        port = int(port)
                    except ValueError:
                        raise ImproperlyConfigured(
                        'If set, PORT must be an integer')

                assert isinstance(self.safe_inserts, bool), \
                'If set, SAFE_INSERTS must be True or False'
                assert isinstance(self.wait_for_slaves, int), \
                'If set, WAIT_FOR_SLAVES must be an integer'
            except AssertionError, e:
                raise ImproperlyConfigured(e)

            self._connection = redis.Redis(host=host,
                                                  port=port,
                                          #        slave_okay=slave_okay
						)

            if user and password:
                auth = self._connection[self.db_name].authenticate(user,
                                                                   password)
                if not auth:
                    raise ImproperlyConfigured("Username and/or password for "
                                               "the Redis db are not correct")

            self._db_connection = self._connection#[self.db_name]

            
            self._connected = True

        # TODO: signal! (see Alex' backend)

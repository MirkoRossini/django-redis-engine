import sys
import re
import datetime

from functools import wraps

from django.db.utils import DatabaseError
from django.db.models.fields import NOT_PROVIDED
from django.db.models import F

from django.db.models.sql import aggregates as sqlaggregates
from django.db.models.sql.constants import MULTI, SINGLE
from django.db.models.sql.where import AND, OR
from django.utils.tree import Node
from redis_entity import RedisEntity,split_db_type,hash_for_redis,get_hash_key,get_set_key,get_list_key,enpickle,unpickle

from index_utils import get_indexes,create_indexes,delete_indexes,filter_with_index,isiterable

import pickle
import redis


from djangotoolbox.db.basecompiler import NonrelQuery, NonrelCompiler, \
    NonrelInsertCompiler, NonrelUpdateCompiler, NonrelDeleteCompiler



#TODO pipeline!!!!!!!!!!!!!!!!!!!!!

def safe_regex(regex, *re_args, **re_kwargs):
    def wrapper(value):
        return re.compile(regex % re.escape(value), *re_args, **re_kwargs)
    wrapper.__name__ = 'safe_regex (%r)' % regex
    return wrapper

OPERATORS_MAP = {
    'exact':        lambda val: val,
#    'iexact':       safe_regex('^%s$', re.IGNORECASE),
#    'startswith':   safe_regex('^%s'),
#    'istartswith':  safe_regex('^%s', re.IGNORECASE),
#    'endswith':     safe_regex('%s$'),
#    'iendswith':    safe_regex('%s$', re.IGNORECASE),
#    'contains':     safe_regex('%s'),
#    'icontains':    safe_regex('%s', re.IGNORECASE),
#    'regex':    lambda val: re.compile(val),
#    'iregex':   lambda val: re.compile(val, re.IGNORECASE),
#    'gt':       lambda val: {'$gt': val},
#    'gte':      lambda val: {'$gte': val},
#    'lt':       lambda val: {'$lt': val},
#    'lte':      lambda val: {'$lte': val},
#    'range':    lambda val: {'$gte': val[0], '$lte': val[1]},
#    'year':     lambda val: {'$gte': val[0], '$lt': val[1]},
#    'isnull':   lambda val: None if val else {'$ne': None},
    'in':       lambda val: {'$in': val},
}

NEGATED_OPERATORS_MAP = {
    'exact':    lambda val: {'$ne': val},
    'gt':       lambda val: {'$lte': val},
    'gte':      lambda val: {'$lt': val},
    'lt':       lambda val: {'$gte': val},
    'lte':      lambda val: {'$gt': val},
    'isnull':   lambda val: {'$ne': None} if val else None,
    'in':       lambda val: val
}


def first(test_func, iterable):
    for item in iterable:
        if test_func(item):
            return item

def safe_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception,e:
            raise DatabaseError, DatabaseError(str(e)), sys.exc_info()[2]
    return wrapper


class DBQuery(NonrelQuery):
    # ----------------------------------------------
    # Public API
    # ----------------------------------------------
    def __init__(self, compiler, fields):
        super(DBQuery, self).__init__(compiler, fields)
	#print fields
	#print dir(self.query.get_meta())
        self.db_table = self.query.get_meta().db_table
	self.indexes = get_indexes()
	self.indexes_for_model =  self.indexes.get(self.query.model,{})
	self._collection = self.connection.db_connection
	self.db_name = self.connection.db_name
	#self.connection.exact_all
        self._ordering = []
        self.db_query = {}

    # This is needed for debugging
    def __repr__(self):
        return '<DBQuery: %r ORDER %r>' % (self.db_query, self._ordering)

    @property
    def collection(self):
        return self._collection

    def fetch(self, low_mark, high_mark):

        results = self._get_results()
	#print 'here results ',results
        primarykey_column = self.query.get_meta().pk.column
        for e_id in results:
            yield RedisEntity(e_id,self._collection,self.db_table,primarykey_column,self.query.get_meta(),self.db_name)

    @safe_call
    def count(self, limit=None): #TODO is this right?
        results = self._get_results()
        if limit is not None:
            results = results[:limit]
        return len(results)

    @safe_call
    def delete(self):

	db_table = self.query.get_meta().db_table
	results = self._get_results()
	
	pipeline = self._collection.pipeline(transaction = False)
	for res in results:
		pipeline.hgetall(get_hash_key(self.db_name,db_table,res))
	hmaps_ret = pipeline.execute()
	hmaps = ((results[n],hmaps_ret[n]) for n in range(len(hmaps_ret)))

	pipeline = self._collection.pipeline(transaction = False)
	for res,hmap in hmaps:
		pipeline.delete(get_hash_key(self.db_name,db_table,res))
		for field,val in hmap.iteritems():
			val = unpickle(val)
			if val is not None:
				#INDEXES
				if field in self.indexes_for_model or self.connection.exact_all:
					try:
						indexes_for_field = self.indexes_for_model[field]
					except KeyError:
						indexes_for_field = ()
					if 'exact' not in indexes_for_field and self.connection.exact_all:
						indexes_for_field += 'exact',
					delete_indexes(	field,
							val,
							indexes_for_field,
							pipeline,
							get_hash_key(self.db_name,db_table,res),
							db_table,
							res,
							self.db_name,
							)
		pipeline.srem(self.db_name+'_'+db_table+'_ids' ,res)
	pipeline.execute()


    @safe_call
    def order_by(self, ordering):
        if len(ordering) > 1:
		raise DatabaseError('Only one order is allowed')
        for order in ordering:
            if order.startswith('-'):
                order, direction = order[1:], 'desc'
            else:
                direction = 'asc'
            if order == self.query.get_meta().pk.column:
                order = '_id'
            else:
		pass #raise DatabaseError('You can only order by PK') TODO check when order index support is active
            self._ordering.append((order, direction))
        return self

    @safe_call
    def add_filter(self, column, lookup_type, negated, db_type, value):
	"""add filter
		used by default add_filters implementation
	
	"""
	#print "ADD FILTER  --  ",column, lookup_type, negated, db_type, value
	if column == self.query.get_meta().pk.column:
		if lookup_type in ('exact','in'):
			#print "cisiamo"
			#print "db_query?"
			#print self.db_query
			try:
				self.db_query[column][lookup_type]
				raise DatabaseError("You can't apply multiple AND filters " #Double filter on pk
                                        "on the primary key. "
                                        "Did you mean __in=[...]?")

			except KeyError:
				self.db_query.update({column:{lookup_type:value}})
	
	else:
		if lookup_type in ('exact','in'):
			if not self.connection.exact_all and 'exact' not  in self.indexes_for_model.get(column,()):
				raise DatabaseError('Lookup %s on column %s is not allowed (have you tried redis_indexes? )' % (lookup_type,column))
			else:self.db_query.update({column:{lookup_type:value}})
		else:
			if lookup_type  in self.indexes_for_model.get(column,()):
				self.db_query.update({column:{lookup_type:value}})
			
			else:
				raise DatabaseError('Lookup %s on column %s is not allowed (have you tried redis_indexes? )' % (lookup_type,column))
        

    def _get_results(self):
	"""
	see self.db_query, lookup parameters format: {'column': {lookup:value}}
	
	"""
	pk_column = self.query.get_meta().pk.column
	db_table = self.query.get_meta().db_table	
	
	results = self._collection.smembers(self.db_name+'_'+db_table+'_ids')


	for column,filteradd in self.db_query.iteritems():
		lookup,value = filteradd.popitem()#TODO tuple better?

		if pk_column == column:
			if lookup == 'in': #TODO meglio??
				results = results & set(value)   #IN filter
			elif lookup == 'exact':
				results = results & set([value,])
				
		else:
			if lookup == 'exact':
				results = results & self._collection.smembers(get_set_key(self.db_name,db_table,column,value))
			elif lookup == 'in': #ListField or empty
				tempset = set()
				for v in value:
					tempset = tempset.union(self._collection.smembers(get_set_key(self.db_name,db_table,column,v) ) )
				results = results & tempset
			else:
				tempset = filter_with_index(lookup,value,self._collection,db_table,column,self.db_name)
				if tempset is not None:
					results = results & tempset
				else:
					results = set()
								

        if self._ordering:
	    if self._ordering[0][1] == 'desc': 
		results.reverse()
	
	if self.query.low_mark > 0 and self.query.high_mark is not None:
		results = list(results)[self.query.low_mark:self.query.high_mark]
        elif self.query.low_mark > 0:

            results = list(results)[self.query.low_mark:]

        elif self.query.high_mark is not None:
            results = list(results)[:self.query.high_mark]

        return list(results)

class SQLCompiler(NonrelCompiler):
    """
    A simple query: no joins, no distinct, etc.
    """
    query_class = DBQuery

    def _split_db_type(self, db_type):
        try:
            db_type, db_subtype = db_type.split(':', 1)
        except ValueError:
            db_subtype = None
        return db_type, db_subtype

    @safe_call # see #7
    def convert_value_for_db(self, db_type, value):
	#print db_type,'   ',value
        if db_type is None or value is None:
            return value

        db_type, db_subtype = self._split_db_type(db_type)
        if db_subtype is not None:
            if isinstance(value, (set, list, tuple)):
                
                return [self.convert_value_for_db(db_subtype, subvalue)
                        for subvalue in value]
            elif isinstance(value, dict):
                return dict((key, self.convert_value_for_db(db_subtype, subvalue))
                            for key, subvalue in value.iteritems())

        if isinstance(value, (set, list, tuple)):
            # most likely a list of ObjectIds when doing a .delete() query
            return [self.convert_value_for_db(db_type, val) for val in value]

        if db_type == 'objectid':
            return value
        return value

    @safe_call # see #7
    def convert_value_from_db(self, db_type, value):
        if db_type is None:
            return value

        if value is None or value is NOT_PROVIDED:
            # ^^^ it is *crucial* that this is not written as 'in (None, NOT_PROVIDED)'
            # because that would call value's __eq__ method, which in case value
            # is an instance of serializer.LazyModelInstance does a database query.
            return None

        db_type, db_subtype = self._split_db_type(db_type)
        if db_subtype is not None:
            for field, type_ in [('SetField', set), ('ListField', list)]:
                if db_type == field:
                    return type_(self.convert_value_from_db(db_subtype, subvalue)
                                 for subvalue in value)
            if db_type == 'DictField':
                return dict((key, self.convert_value_from_db(db_subtype, subvalue))
                            for key, subvalue in value.iteritems())

        if db_type == 'objectid':
            return unicode(value)

        if db_type == 'date':
            return datetime.date(value.year, value.month, value.day)

        if db_type == 'time':
            return datetime.time(value.hour, value.minute, value.second,
                                 value.microsecond)
        return value

    def insert_params(self):
        conn = self.connection
        params = {'safe': conn.safe_inserts}
        if conn.wait_for_slaves:
            params['w'] = conn.wait_for_slaves
        return params

    @property
    def _collection(self):
        #TODO multi db
	return self.connection.db_connection
    @property
    def db_name(self):
        return self.connection.db_name

    def _save(self, data, return_id=False):

	db_table = self.query.get_meta().db_table
	indexes = get_indexes()
	indexes_for_model =  indexes.get(self.query.model,{})

	pipeline = self._collection.pipeline(transaction = False)

	h_map = {}
	h_map_old = {}

	if '_id' in data:
		pk = data['_id']
		new = False
		h_map_old = self._collection.hgetall(get_hash_key(self.db_name,db_table,pk))
	else:
		pk = self._collection.incr(self.db_name+'_'+db_table+"_id")
		new = True		
	
	for key,value in data.iteritems():
		
		if new:
			old = None
			h_map[key] = pickle.dumps(value)			
		else:
			if key == "_id": continue
			old = pickle.loads(h_map_old[key])

			if old != value:
				h_map[key] = pickle.dumps(value)

		if key in indexes_for_model or self.connection.exact_all:
			try:
				indexes_for_field = indexes_for_model[key]
			except KeyError:
				indexes_for_field = ()
			if 'exact' not in indexes_for_field and self.connection.exact_all:
				indexes_for_field += 'exact',
			create_indexes(	key,
					value,
					old,
					indexes_for_field,
					pipeline,
					db_table+'_'+str(pk),
					db_table,
					pk,
					self.db_name,
					)
	
        if '_id' not in data: pipeline.sadd(self.db_name+'_'+db_table+"_ids" ,pk)
	
	pipeline.hmset(get_hash_key(self.db_name,db_table,pk),h_map)			
	pipeline.execute()
        if return_id:
            return unicode(pk)

    def execute_sql(self, result_type=MULTI):
        """
        Handles aggregate/count queries
        """
	
	
	raise NotImplementedError('Not implemented')
	

class SQLInsertCompiler(NonrelInsertCompiler, SQLCompiler):
    @safe_call
    def insert(self, data, return_id=False):
        pk_column = self.query.get_meta().pk.column
        try:
            data['_id'] = data.pop(pk_column)
        except KeyError:
            pass
        return self._save(data, return_id)

class SQLUpdateCompiler(NonrelUpdateCompiler, SQLCompiler):
    pass
class SQLDeleteCompiler(NonrelDeleteCompiler, SQLCompiler):
    pass

from django.conf import settings
from django.utils.importlib import import_module
from md5 import md5
from redis_entity import *
_MODULE_NAMES = getattr(settings, 'REDIS_SETTINGS_MODULES', ())
from redis.exceptions import WatchError

#TODO update might overwrite field indexes

INDEX_KEY_INFIX = "redis_index"

SWITH_INDEX_SEPARATOR = '\x00'

isiterable = lambda obj: getattr(obj, '__iter__', False)



def val_for_insert(d):
	if isinstance(d,unicode):
	  d = d
	elif isinstance(d,basestring) : d = unicode(d.decode('utf-8'))
	else: d = unicode(d)
        return d


def get_indexes():
        indexes = {}
        for name in _MODULE_NAMES:
            try:
                indexes.update(import_module(name).INDEXES)
            except (ImportError, AttributeError):
                pass
        
	return indexes


def create_indexes(column,data,old,indexes,conn,hash_record,table,pk,db_name):
		for index in indexes:
			if index in ('startswith','istartswith','endswith','iendswith'):
				if old is not None:
					if not isiterable(old):
						old = (old,)	
					for d in old:
						if index == 'istartswith': d = d.lower()
						if index == 'endswith': d = d[::-1]
						if index == 'iendswith': d = d.lower()[::-1]
						conn.zrem(get_zset_index_key(db_name,table,INDEX_KEY_INFIX,column,index),
										d+SWITH_INDEX_SEPARATOR+str(pk))
				if not isiterable(data):
					data = (data,)
				for d in data:
					d = val_for_insert(d)
					if index == 'istartswith': d = d.lower()
					if index == 'endswith': d = d[::-1]
					if index == 'iendswith': d = d.lower()[::-1]
						
					conn.zadd(get_zset_index_key(db_name,table,INDEX_KEY_INFIX,column,index),
										d+SWITH_INDEX_SEPARATOR+str(pk),0)
			if index == 'exact':
				if old is not None:
					if not isiterable(old):
						old = (old,)	
					for d in old:
						conn.srem(get_set_key(db_name,table,column,d),str(pk))
				if not isiterable(data):
					data = (data,)
				for d in data:
					d = val_for_insert(d)
					conn.sadd(get_set_key(db_name,table,column,d),pk)

def delete_indexes(column,data,indexes,conn,hash_record,table,pk,db_name):
		for index in indexes:
			if index in ('startswith','istartswith','endswith','iendswith'):
				if not isiterable(data):
					data = (data,)
				for d in data:
					d = val_for_insert(d)
					if index == 'istartswith': d = d.lower()
					if index == 'endswith': d = d[::-1]
					if index == 'iendswith': d = d.lower()[::-1]
					conn.zrem(get_zset_index_key(db_name,table,INDEX_KEY_INFIX,column,index),
									d+SWITH_INDEX_SEPARATOR+str(pk))
			if index == 'exact':
				if not isiterable(data):
					data = (data,)
				for d in data:
					d = val_for_insert(d)
					conn.srem(get_set_key(db_name,table,column,d),str(pk))

def filter_with_index(lookup,value,conn,table,column,db_name):
	if lookup in ('startswith','istartswith','endswith','iendswith'):
		if not isinstance(value,unicode):
			if isinstance(value,basestring):
				value = unicode(value.decode('utf-8'))
			else: value = unicode(value)
		if lookup == 'startswith':v = value
		elif lookup == 'istartswith': v = value.lower()
		elif lookup == 'iendswith': v = value.lower()[::-1]
		elif lookup == 'endswith': v = value[::-1]
		
		#v2 = v[:-1]+chr(ord(v[-1])+1) #last letter=next(last letter)
		key = get_zset_index_key(db_name,table,INDEX_KEY_INFIX,column,lookup)

		pipeline = conn.pipeline()		
		conn.zadd(key,v,0)
		#pipeline.zadd(key,v2,0)
		#pipeline.execute()
		while True:
			try:
				conn.watch(key)
				up = conn.zrank(key,v)
				#down = conn.zrank(key,v2)

				pipeline.zrange(key,up+1,-1)#down-1)
				pipeline.zrem(key,v)
				#pipeline.zrem(key,v2)
		
				l = pipeline.execute()
				#print l
				r = l[0]
				#print l
				#print 'erre: ',r
				#print 'second pipeline',pipeline.execute()
				ret = set()
				for i in r:
					i = unicode(i.decode('utf8'))
					if i.startswith(v):
						splitted_string = i.split(SWITH_INDEX_SEPARATOR)
						if len(splitted_string) > 1:
							ret.add(splitted_string[-1])
					else:
						break
				return ret
			except WatchError:
				pass
#		print pipeline.execute()
	else:
		raise Exception('Lookup type not supported') #TODO check at index creation?
	


# 

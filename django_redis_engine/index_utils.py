from django.conf import settings
from django.utils.importlib import import_module
from md5 import md5

_MODULE_NAMES = getattr(settings, 'REDIS_SETTINGS_MODULES', ())

#TODO update might overwrite field indexes

INDEX_KEY_INFIX = "redis_index"



isiterable = lambda obj: getattr(obj, '__iter__', False)

def hash_for_redis(val):
	if isinstance(val,unicode):
		return md5(val.encode('utf-8')).hexdigest()
	return md5(str(val)).hexdigest()

def val_for_insert(d):
	if isinstance(d,unicode):
	  d = d
	else : d = unicode(d)
        return d


def get_indexes():
        indexes = {}
        for name in _MODULE_NAMES:
            try:
                indexes.update(import_module(name).INDEXES)
            except (ImportError, AttributeError):
                pass
        
	return indexes


def create_indexes(column,data,indexes,conn,hash_record,table,pk):
		for index in indexes:
			if index == 'startswith':
				if not isiterable(data):
					data = (data,)
				for d in data:
					d = val_for_insert(d)
					conn.zadd(table +'_' + INDEX_KEY_INFIX + '_' + column + '_startswith',d+'_'+str(pk),0)
			if index == 'istartswith':
				if not isiterable(data):
					data = (data,)
				for d in data:
					d = val_for_insert(d).lower()
					conn.zadd(table +'_' + INDEX_KEY_INFIX + '_' + column + '_istartswith',d+'_'+str(pk),0)

def delete_indexes(column,data,indexes,conn,hash_record,table,pk):
		for index in indexes:
			if index == 'startswith':
				if not isiterable(data):
					data = (data,)
				for d in data:
					d = val_for_insert(d)
					conn.zrem(table +'_' + INDEX_KEY_INFIX + '_' + column + '_startswith',d+'_'+str(pk))
			if index == 'istartswith':
				if not isiterable(data):
					data = (data,)
				for d in data:
					d = val_for_insert(d).lower()
					conn.zrem(table +'_' + INDEX_KEY_INFIX + '_' + column + '_istartswith',d.lower()+'_'+str(pk))

def filter_with_index(lookup,value,conn,table,column):
	if lookup in ('startswith','istartswith'):
		if isinstance(value,unicode):
			if lookup == 'startswith':v = value
			else: v = value.lower()
		else: v = unicode(value)
		#v2 = v[:-1]+chr(ord(v[-1])+1) #last letter=next(last letter)
		key = table +'_' + INDEX_KEY_INFIX + '_' + column + '_startswith'

		pipeline = conn.pipeline()		
		pipeline.zadd(key,v,0)
		#pipeline.zadd(key,v2,0)
		pipeline.execute()
		
		conn.watch(key)
		up = conn.zrank(key,v)
		#down = conn.zrank(key,v2)

		pipeline.zrange(key,up+1,-1)#down-1)
		pipeline.zrem(key,v)
		#pipeline.zrem(key,v2)
		l = pipeline.execute()
		#print l
		r = l[0]
		
		#print 'erre: ',r
		#print 'second pipeline',pipeline.execute()
		ret = set()
		for i in r:
			i = unicode(i.decode('utf8'))
			if i.startswith(v):
				ret.add(i.split('_')[-1])
			else:
				break
		return ret
#		print pipeline.execute()
	else:
		raise Exception('Lookup type not supported') #TODO check at index creation?
	

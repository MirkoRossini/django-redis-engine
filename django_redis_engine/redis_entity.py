from django.db.models.fields import FieldDoesNotExist
from md5 import md5


class RedisEntity(object):
	def __init__(self,e_id,connection,db_table, pkcolumn, querymeta, db_name):
		self.id = e_id
		self.connection = connection
		self.db_table = db_table
		self.pkcolumn = pkcolumn
		self.querymeta = querymeta
		self.db_name = db_name
	def get(self,what,value):
		if what == self.pkcolumn:
			return self.id
		else:
			
			try:
				db_type, db_subtype =  split_db_type(self.querymeta.get_field_by_name(what)[0].db_type())

				if db_type in ('ListField','SetField'):
					return self.connection.lrange(get_list_key(self.db_name,self.db_table,what,self.id),0,-1)

			except FieldDoesNotExist: #Field does not exist, related. TODO Clean this up, find a smarter way
				pass
			return self.connection.hget(get_hash_key(self.db_name,self.db_table,self.id), what)
						


def split_db_type(db_type):
	#TODO move somewhere else
        try:
            db_type, db_subtype = db_type.split(':', 1)
        except ValueError:
            db_subtype = None
        return db_type, db_subtype

def get_hash_key(db_name,db_table,pk):
	return db_name+'_'+db_table+'_'+str(pk)

def get_zset_index_key(db_name,db_table,infix,column,index):
	return db_name+'_'+db_table +'_' + infix + '_' + column + '_'+index

def get_list_key(db_name,db_table,key,pk):
	return db_name+'_'+db_table+'_'+key+'_'+str(pk)


def get_set_key(db_name,db_table,key,value):
	return db_name+'_'+db_table+'_'+key+'_'+hash_for_redis(value)

def hash_for_redis(val):
	if isinstance(val,unicode):
		return md5(val.encode('utf-8')).hexdigest()
	return md5(str(val)).hexdigest()

from django.db.models.fields import FieldDoesNotExist

class RedisEntity(object):
	def __init__(self,e_id,connection,db_table, pkcolumn, querymeta):
		self.id = e_id
		self.connection = connection
		self.db_table = db_table
		self.pkcolumn = pkcolumn
		self.querymeta = querymeta
	def get(self,what,value):
		if what == self.pkcolumn:
			return self.id
		else:
			
			try:
				db_type, db_subtype =  split_db_type(self.querymeta.get_field_by_name(what)[0].db_type())

				if db_type in ('ListField','SetField'):
					return self.connection.lrange(self.db_table+'_'+what+'_'+str(self.id),0,-1)

			except FieldDoesNotExist: #Field does not exist, related. TODO Clean this up, find a smarter way
				pass
			return self.connection.hget(self.db_table+'_'+str(self.id), what)
						


def split_db_type(db_type):
	#TODO move somewhere else
        try:
            db_type, db_subtype = db_type.split(':', 1)
        except ValueError:
            db_subtype = None
        return db_type, db_subtype

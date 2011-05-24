from models import Post
from django.contrib.sessions.models import Session


INDEXES = {
    Post: {'idxf_title_l_contains': ('startswith',),
	'text':('iendswith',),
	'title':('startswith','endswith'),
	'time':('gt','lte'),
	},
    Session : {'expire_date' : ('gt',)
	},
    
}


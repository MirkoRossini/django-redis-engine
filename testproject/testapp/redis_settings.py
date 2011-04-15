from models import Post

INDEXES = {
    Post: {'idxf_title_l_contains': ('startswith',),
	},
    
}


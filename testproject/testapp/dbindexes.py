from models import Post
from dbindexer.api import register_index


register_index(Post, {'title': 'contains',})

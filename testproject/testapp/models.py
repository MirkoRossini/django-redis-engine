from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Post(models.Model):
	title = models.CharField(max_length = 100)
	text = models.TextField()

class Answer(models.Model):
	text = models.TextField()
	post = models.ForeignKey(Post)

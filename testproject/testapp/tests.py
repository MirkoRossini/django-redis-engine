#-*- encoding:utf-8 -*-

from django.test import TestCase
from models import *
from md5 import md5
import random

from django_redis_engine import redis_transaction
from django.db import transaction
class SimpleTest(TestCase):

    def test_update_and_filters(self):
	"""
	test effects of updates on filters
	"""
	post = Post.objects.create(
                                text = "to be updated text",
                                title = "to be updated title"
                                )
	post.text = "updated text"
	post.save()
	posts = Post.objects.filter(text = "to be updated text")
	self.failUnlessEqual(len(posts), 0)
	posts = Post.objects.filter(text = "updated text")
	self.failUnlessEqual(len(posts), 1)
	post.title = "updated title"
	post.save()
	posts = Post.objects.filter(title__contains = "to be updated title")
        self.failUnlessEqual(len(posts), 0)
        posts = Post.objects.filter(title__contains = "updated title")
        self.failUnlessEqual(len(posts), 1)
	post.delete()
	
    def atest_insert_transaction(self):
	"""
	stress test, used to find out how much network latency
	affects performance using transactions.
	"""
	n = 100
	ng = 100
	ngc = 100
	l = []
	#print redis_transaction.commit_manually(using = 'native')
	#print transaction.commit_manually()
	with redis_transaction.commit_manually(using = 'native'):
		print "begin"
		for i in range(n):
			tit = md5(str(random.random())+str(i)).hexdigest()
			l.append(tit)
			Post.objects.create(
					title = tit,
					text = " ".join(
							[md5(
								str(random.random())+\
								str(t)+\
								str(i)).hexdigest() for t in range(20)]
							)
					)
		redis_transaction.commit()
	for i in range(ng):
		p = Post.objects.get(title = l[random.randint(0,n-1)] )
	for i in range(ngc):
		Post.objects.filter(title__contains = l[random.randint(0,n-1)])
		#self.failUnlessEqual(len(posts), 1)

    def test_add_post_answers_and_filters(self):
        """
        Create some posts, create answers to them,
	test contains filter on post title
	test startswith filter on post title
	test endswith filter on post title
	test iendswith filter on post text
	test exact filter on all fields
	test gt and lte filters
	test deletion of objects and indexes 
        """
        post1 = Post.objects.create(
				text = "text1",
				title = "title1"
				)

        post2 = Post.objects.create(
				text = "text2",
				title = "title2"
				)
        post3 = Post.objects.create(
				text = "RrRQqà",
				title = "AaABbB"
				)
	answer1 = Answer.objects.create(
				text= "answer1 to post 1",
				post = post1
				)
	answer2 = Answer.objects.create(
				text= "answer2 to post 1",
				post = post1
				)
	answer3 = Answer.objects.create(
				text= "answer1 to post 2",
				post = post2
				)
	posts = Post.objects.all()
	self.failUnlessEqual(len(posts), 3)
	posts = Post.objects.filter(title__contains = 'title')
	self.failUnlessEqual(len(posts), 2)
	p = Post.objects.get(title = 'title1')
	self.failUnlessEqual(p.pk, post1.pk)
	p = Post.objects.get(text = 'text2')
	self.failUnlessEqual(p.pk, post2.pk)
	a = Answer.objects.get(text = 'answer2 to post 1')
	self.failUnlessEqual(a.pk, answer2.pk)
	
	p.delete()
	posts = Post.objects.all()
        self.failUnlessEqual(len(posts), 2)
        posts = Post.objects.filter(title__contains = 'title')
        self.failUnlessEqual(len(posts), 1)
        posts = Post.objects.filter(title__startswith = 'Aa')
        self.failUnlessEqual(len(posts), 1)
        posts = Post.objects.filter(title__startswith = 'AA')
        self.failUnlessEqual(len(posts), 0)

        posts = Post.objects.filter(title__endswith = 'bB')
        self.failUnlessEqual(len(posts), 1)

        posts = Post.objects.filter(title__endswith = 'BB')
        self.failUnlessEqual(len(posts), 0)
	posts = Post.objects.filter(text__iendswith = 'qqà')
        self.failUnlessEqual(len(posts), 1)
        posts = Post.objects.filter(text__iendswith = 'QQÀ')
        self.failUnlessEqual(len(posts), 1)

	
	a.delete()
	answers = Answer.objects.filter(text = 'answer2 to post 1')
	self.failUnlessEqual(len(answers), 0)
	
	import datetime
	posts = Post.objects.filter(text__iendswith = 'QQÀ',
				time__gt = datetime.datetime.now() - datetime.timedelta(minutes = 10))
	self.failUnlessEqual(len(posts), 1)
	posts = Post.objects.filter(time__gt = datetime.datetime.now() - datetime.timedelta(minutes = 10))
	self.failUnlessEqual(len(posts), 2)

	posts = Post.objects.filter(time__lte = posts[0].time)
	self.failUnlessEqual(len(posts), 1)

	posts = Post.objects.filter(time__lte = posts[0].time + datetime.timedelta(minutes = 10))
	self.failUnlessEqual(len(posts), 2)






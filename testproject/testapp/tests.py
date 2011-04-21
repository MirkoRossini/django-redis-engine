from django.test import TestCase
from models import *


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
	
	
    def test_add_post_answers_and_filters(self):
        """
        Create some posts, create answers to them,
	test icontains filter on post title
	test exact filter on all fields
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
	self.failUnlessEqual(len(posts), 2)
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
        self.failUnlessEqual(len(posts), 1)
        posts = Post.objects.filter(title__contains = 'title')
        self.failUnlessEqual(len(posts), 1)
	a.delete()
	answers = Answer.objects.filter(text = 'answer2 to post 1')
	self.failUnlessEqual(len(answers), 0)

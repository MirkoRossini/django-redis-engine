# Create your views here.
from models import Post, Answer
from django.shortcuts import render_to_response
from forms import *
from django.template import RequestContext
from django.http import HttpResponseRedirect

def add_post(request,):
  #VIEW CODE  
  if request.method == 'POST':
    form = MyForm(request.POST)
    if form.is_valid():
      # Process the data in form.cleaned_data
      form.save()
      return HttpResponseRedirect('/posts/')
  else:
    form = MyForm()
  ret_dict = {
              'form':form,
              } 
  return render_to_response("testapp/add_post.html", 
                        ret_dict,
                        context_instance = RequestContext(request),)



def add_answer(request,post_id):
  #VIEW CODE  
  if request.method == 'POST':
    form = AnswerForm(request.POST)
    post = Post.objects.get(pk = post_id)
    if form.is_valid():
      # Process the data in form.cleaned_data
      form.instance.post = post
      form.save()
      return HttpResponseRedirect('/posts/')
  else:
    form = AnswerForm()
  ret_dict = {
              'form':form,
              } 
  return render_to_response("testapp/add_answer.html", 
                        ret_dict,
                        context_instance = RequestContext(request),)



def posts(request,):
  ret_dict = {}
  if request.method == 'POST' and request.POST['title_filter'] is not None and request.POST['title_filter'] != '':
    posts = Post.objects.filter(title__contains = request.POST['title_filter'])
    ret_dict['filter'] = request.POST['title_filter']
  else:
    posts = Post.objects.all()
  
  ret_dict['posts'] = posts
    
  return render_to_response("testapp/posts.html", 
                        ret_dict,
                        context_instance = RequestContext(request),)



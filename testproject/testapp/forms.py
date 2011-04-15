from django import forms
from models import *


class MyForm(forms.ModelForm):
	class Meta:
		model = Post


class AnswerForm(forms.ModelForm):
	class Meta:
		model = Answer
		exclude = ("post")


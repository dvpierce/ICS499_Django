from django import forms

class DocumentForm(forms.Form):
	docfile = forms.FileField(label='Select a file', help_text='helptext')



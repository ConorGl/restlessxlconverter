from django import forms
from django.urls import reverse_lazy
from django.views.generic import FormView


class NameSubmitForm(forms.Form):
    name = forms.FileField(label='Enter your name')


class Dashboard(FormView):
    template_name = 'index.html'
    form_class = NameSubmitForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        # Do shit to file here.

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(data={'4': 5}, **kwargs)


dashboard = Dashboard.as_view()

from django import forms
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import FormView

import mimetypes
import openpyxl
from main.get_donation_amount import DonationGetter


HEADERS = {"content-type": "application/json"}
API_URL = "https://api.justgiving.com/{}/v1/fundraising/pages/{}"
APP_ID = "3533468f"
FUND_URL = "https://www.justgiving.com/fundraising/"

class NameSubmitForm(forms.Form):
    name = forms.FileField(label="Submit your file")


class Dashboard(FormView):
    template_name = 'index.html'
    form_class = NameSubmitForm
    success_url = reverse_lazy('dashboard2')

    def form_valid(self, form):
        workbook = openpyxl.load_workbook(form.files['name'].open())
        restless_getter = DonationGetter(APP_ID, HEADERS, API_URL, FUND_URL)
        workbook = restless_getter.process_workbook(workbook)
        workbook.save('processed.xlsx')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return super().get_context_data(data={'4': 5}, **kwargs)

    def download_file(self, request):
        filename = 'processed.xlsx'

        file = open('','r')
        mime_type, _ = mimetypes.guess_type('')
        response = HttpResponse()

dashboard = Dashboard.as_view()
dashboard2 = Dashboard.as_view()
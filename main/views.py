from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView
import django_rq
import uuid
import boto3
import openpyxl
import requests
import os
from rq.job import Job

from main.get_donation_amount import DonationGetter

HEADERS = {"content-type": "application/json"}
API_URL = "https://api.justgiving.com/{}/v1/fundraising/pages/{}"
APP_ID = "3533468f"
FUND_URL = "https://www.justgiving.com/fundraising/"

redis_conn = django_rq.get_connection()
# q = django_rq.get_queue(connection=redis_conn)  # no args implies the default queue

class NameSubmitForm(forms.Form):
    file = forms.FileField(label="Submit your file")

def process_file(file):
    url = save_file_get_url(file)
    response = requests.get(url)
    filename = file._get_name()
    with open('/tmp/{}'.format(filename), 'wb') as temp_file:
        temp_file.write(response.content)
    return generate_file(filename)

def generate_file(filename):
    workbook = openpyxl.load_workbook('/tmp/{}'.format(filename))
    restless_getter = DonationGetter(APP_ID, HEADERS, API_URL, FUND_URL)
    streamed_workbook = restless_getter.process_workbook(workbook)
    return streamed_workbook, filename

def save_file_get_url(form_file):
    client = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY'],
        aws_secret_access_key=os.environ['AWS_SECRET_KEY'],
        region_name='eu-west-2'
    )
    kwargs = dict(Bucket=os.environ['BUCKET'], Key=form_file.name)
    client.upload_fileobj(Fileobj=form_file.open(), **kwargs)
    url = client.generate_presigned_url('get_object', Params=kwargs, ExpiresIn=600)
    return url

class GenerateExport(FormView):
    template_name = 'index.html'
    form_class = NameSubmitForm
    success_url = reverse_lazy('dashboard')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.job_status = ''

    def form_valid(self, form):
        job_id = str(uuid.uuid4())
        print("enqueuing file")
        django_rq.enqueue(process_file, form.files['file'], job_id=job_id)
        print("file enqueued")
        return redirect(f'/processing?j={job_id}')

    def get_context_data(self, **kwargs):
        return super().get_context_data(job_status=self.job_status, **kwargs)


class GenerateExportPro(FormView):
    template_name = 'index2.html'
    form_class = NameSubmitForm
    success_url = reverse_lazy('processing')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.job_status = ''

    def dispatch(self, request, *args, **kwargs):
        job_id = self.request.GET.get('j')
        if job_id:
            job = Job.fetch(job_id, connection=redis_conn)
            if job.get_status() == 'ongoing':
                # Show loading
                self.job_status = 'ongoing'
                pass
            elif job.get_status() == 'finished':
                print("Job Finished")
                streamed_workbook, filename = job.return_value
                response = HttpResponse(content=streamed_workbook, content_type='application/ms-excel')
                response['Content-Disposition'] = "attachment; filename={}".format(filename)
                return response
            # elif job.get_status() == TrackedJobStatus.FAILED:
            #    print("Why though?")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(job_status=self.job_status, **kwargs)

# class Dashboard(FormView):
#     form_class = NameSubmitForm
#
#     def form_valid(self, form):
#         filename = form.files['name']._get_name()
#         workbook = openpyxl.load_workbook(form.files['name'].open())
#         restless_getter = DonationGetter(APP_ID, HEADERS, API_URL, FUND_URL)
#         streamed_workbook = restless_getter.process_workbook(workbook)
#         response = HttpResponse(content=streamed_workbook, content_type='application/ms-excel')
#         response['Content-Disposition'] = "attachment; filename={}".format(filename)
#         return response
#
#     def get_context_data(self, **kwargs):
#         return super().get_context_data(data={'4': 5}, **kwargs)
#

dashboard = GenerateExport.as_view()
processing = GenerateExportPro.as_view()


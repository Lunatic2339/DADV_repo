from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.views import View
from . import forms
from . import models
# Create your views here.

def add(request):
    if request.method == "POST":
        form = forms.StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(add)
    if request.method == "GET":
        students = models.Student.objects.all()
        form = forms.StudentForm()
        return render(request, "main/add.html", {"form": form, "students": students})
    else:
        return HttpResponse("Invalid request method.", status=400)
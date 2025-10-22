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

def hello1(request):
    return HttpResponse("<h1>Hello, World!</h1><h2>Well...</h2>")
def hello2(request):
    return HttpResponse("Hello, World! with no name")

def toGoogle(request):
    return redirect("https://google.com")

# continued.

def not_found(request):
    raise Http404("Sorry... no page here. LOL")
def api_example(request):
    data={"message": "Hello, this is a JSON response","status": "success"}
    return JsonResponse(data)

def content(request):
    if request.method == 'POST':
        #process(request)
        return HttpResponse("POST request received")
    elif request.method == 'GET':
        data = {
            "message": "This is a GET request or a JSON reponse",
            "status": "success"
        }
        return JsonResponse(data)
    else:
        return HttpResponse("Invalid request")
    
class contentView(View):
    def get(self, request):
        return HttpResponse("This is a GET request")
    
    
    def post(self, request):
        return HttpResponse("POST request received")
    


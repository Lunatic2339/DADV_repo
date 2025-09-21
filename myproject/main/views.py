from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.views import View

# Create your views here.

def index(request):
    context = {
        "title": "myTitle",
        "context": "myContent"
    }
    return render(request, 'main/index.html', context=context)



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

from django.urls import path
from . import views # . == this path
urlpatterns  = [ 
    path('', views.add),

]
from django.urls import path
from . import views # . == this path
urlpatterns  = [ 
    path('', views.index, name='index'),
    path('hello', views.hello1, name='hello'),
    path('hello/', views.hello2),
    path('google', views.toGoogle),
    path('notfound', views.not_found),
    path('api', views.api_example),
    path('content', views.content),
    path('content/', views.contentView.as_view()),
    path('add', views.add, name='add'),
]
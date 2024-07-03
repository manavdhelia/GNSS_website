from django.urls import path
from .import viewsTest

urlpatterns = [
    path('', viewsTest.home, name='gnss-home'),

]

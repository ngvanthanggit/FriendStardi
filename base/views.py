from django.shortcuts import render
from django.http import HttpResponse, Http404
from .models import Room

# Create your views here.

# rooms = [
#     {'id': 1, 'name': 'Lets learn python!'},
#     {'id': 2, 'name': 'Design with me'},
#     {'id': 3, 'name': 'Django is a good name'},
# ]

def home(request):
    rooms = Room.objects.all()
    context = {'rooms': rooms}
    return render(request, 'base/home.html', context)

def room(request, pk):
    this_room = Room.objects.get(id=pk)
    context = {"room": this_room}
    return render(request, 'base/room.html', context)

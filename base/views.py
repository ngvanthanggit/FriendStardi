from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from .models import Room, Topic, Message
from .forms import RoomForm


def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Incorrect password')
        
    context = {'page': "login"}
    return render(request, 'base/login_register.html', context)

def logout_user(request):
    logout(request)
    return redirect('home')

def registerUser(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during the registration!')
    context = {'page': "register", 'form': form}
    return render(request, 'base/login_register.html', context)

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) |
        Q(host__username__icontains=q)
    )
    room_count = rooms.count()
    topics = Topic.objects.all()
    
    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count}
    return render(request, 'base/home.html', context)

def room(request, pk):
    this_room = Room.objects.get(id=pk)
    room_messages = this_room.message_set.all().order_by('-created')
    room_participants = this_room.participants.all()
    
    if request.method == 'POST':
        new_message = Message.objects.create(
            user=request.user,
            room=this_room,
            body=request.POST.get('new_comment')
        )
        if not request.user in room_participants:
            this_room.participants.add(request.user)
        return redirect('room', pk=this_room.id)
    
    context = {"room": this_room, "room_messages": room_messages, 'room_participants': room_participants}
    return render(request, 'base/room.html', context)

@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
        else:
            messages.error(request, 'An error occurred!')
            
    context = {'form': form}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    
    if request.user != room.host:
        return HttpResponse('You are not allowed here!')
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')
        else:
            messages.error(request, 'An error occurred!')
    
    context = {'form': form}
    
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def delete_room(request, pk):
    room = Room.objects.get(id=pk)
    
    if request.user != room.host:
        return HttpResponse('You are not allowed here!')
    
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    context = {'obj': room}
    
    return render(request, 'base/delete.html', context)

@login_required(login_url='login')
def delete_message(request, room_id, pk):
    del_message = Message.objects.get(id=pk)
    
    if del_message.user != request.user:
        return HttpResponse('You are not allowed!')
    
    if request.method == 'POST':
        del_message.delete()
        current_room = Room.objects.get(id=room_id)
        current_user = request.user
        
        # current_room.message_set().remove(del_message)
        
        all_room_messages = current_room.message_set.all()
        
        count_user_messages = all_room_messages.filter(user=current_user).count()
        if count_user_messages == 0:
            current_room.participants.remove(current_user)
            
        return redirect('room', pk=room_id)
    
    context = {'obj': del_message}
    return render(request, 'base/delete.html', context)
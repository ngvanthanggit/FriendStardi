from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Count
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
    return render(request, 'base/login.html', context)

def logout_user(request):
    logout(request)
    return redirect('home')

def registerUser(request):
    form = UserCreationForm()
    if request.method == 'POST':
        if request.POST.get('password') == request.POST.get('confirm_password'):
            
            if User.objects.filter(username=request.POST.get('username')).exists():
                messages.error(request, 'Username has already existed')
            else:
                user = User.objects.create_user(
                    first_name = request.POST.get('first_name'),
                    last_name = request.POST.get('last_name'),
                    username = request.POST.get('username'),
                    password = request.POST.get('password')
                )
                user.save()
                login(request, user)
                return redirect('home')
        else:
            messages.error(request, 'Your password and confirm password are not the same!')
        # if form.is_valid():
        #     user = form.save(commit=False)
        #     user.username = user.username.lower()
        #     user.save()
            
        #     login(request, user)
        #     return redirect('home')
        # else:
        #     messages.error(request, 'An error occurred during the registration!')
    context = {'page': "register", 'form': form}
    return render(request, 'base/signup.html', context)

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) |
        Q(host__username__icontains=q)
    )
    room_count = rooms.count()
    topics = Topic.objects.annotate(num_rooms=Count('room')).order_by('-num_rooms')[:5]
    
    recent_messages = Message.objects.filter(
        Q(user__username__icontains=q) |
        Q(room__name__icontains=q) |
        Q(body__icontains=q)).order_by('-updated')[:3]
    
    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count, 'recent_messages': recent_messages}
    return render(request, 'base/home.html', context)

def room(request, pk, comment_id=0):
    this_room = Room.objects.get(id=pk)
    room_messages = this_room.message_set.all()
    room_participants = this_room.participants.all()
    
    #print(room_participants);
    
    if request.method == 'POST':
        new_message = Message.objects.create(
            user=request.user,
            room=this_room,
            body=request.POST.get('new_comment')
        )
        if not request.user in room_participants:
            this_room.participants.add(request.user)
        return redirect('room', pk=this_room.id)
    
    if comment_id:
        room_messages = [it_message for it_message in room_messages if it_message.id == comment_id]
    all_messages = (comment_id == 0)
    
    context = {"room": this_room, "room_messages": room_messages, "all_messages": all_messages, 'room_participants': room_participants}
    return render(request, 'base/room.html', context)

@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),
        )
        return redirect('home')
        # form = RoomForm(request.POST)
        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     room.save()
        #     room.participants.add(room.host)
        #     return redirect('home')
        # else:
        #     messages.error(request, 'An error occurred!')
            
    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    
    if request.user != room.host:
        return HttpResponse('You are not allowed here!')
    
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    
    context = {'form': form, 'topics': topics, 'room': room}
    
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

def profile(request, username):
    user = User.objects.get(username=username)
    
    user_messages = user.message_set.all()
    rooms = user.room_set.all()
    
    topics = Topic.objects.all()
    
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = rooms.filter(
        Q(topic__name__icontains=q)
    )
    
    context = {"user": user, "topics": topics, "rooms": rooms, "recent_messages": user_messages}
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')
def edit_user(request):
    
    if request.method == "POST":
        user = request.user
        
        #new_avatar = request.POST.get('avatar')
        new_first_name = request.POST.get('firstname')
        new_last_name = request.POST.get('lastname')
        #new_email = request.POST.get('email')
        #new_bio = request.POST.get('bio')
        
        user.first_name = new_first_name
        user.last_name = new_last_name
        user.save()
        
        return redirect('profile', username=user.username)
    
    context = {'user': request.user}
    return render(request, 'base/edit_user.html', context)

def topic_page(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.annotate(num_rooms=Count('room')).order_by('-num_rooms').filter(
        Q(name__icontains=q)
    )
    
    context = {'topics': topics}
    
    return render(request, 'base/topics.html', context)

def activities_page(request):
    recent_messages = Message.objects.all().order_by('-updated')[:7]
    context = {'recent_messages': recent_messages}
    return render(request, 'base/activities.html', context)
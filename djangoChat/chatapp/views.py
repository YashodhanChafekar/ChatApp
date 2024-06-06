from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ChatGroup, Messages

# Create your views here.

@login_required
def chatroom(request, room_name):
    user = request.user
    chat_group = ChatGroup.objects.filter(name=f"chat_{room_name}", users=user)
    messages = Messages.objects.filter(room=chat_group.first())
    print("messages")
    return render(
        request=request,
        template_name='chatapp/chat.html',
        context={
            "room_name": room_name,
            "old_messages": messages,
        }
    )

def direct_chatroom(request, room_name):
    return render(
        request=request,
        template_name='chatapp/direct_chat.html',
        context={
            "room_name": room_name
        }
    )
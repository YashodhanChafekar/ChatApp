from django.urls import path
from .views import chatroom, direct_chatroom

urlpatterns = [
    path('<str:room_name>', chatroom, name="chatroom"),
    path('direct/<str:room_name>', direct_chatroom, name="direct_chatroom")
]

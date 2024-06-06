from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()


class ChatGroup(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_groups", related_query_name="owned_group", null=True)
    users = models.ManyToManyField(User, related_name="chatgroups", related_query_name="chatroom")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = "ChatGroup"
        verbose_name_plural = "ChatGroups"


class Messages(models.Model):
    message = models.TextField(name="message", verbose_name="Message", blank=True)
    date = models.DateTimeField(auto_now_add=True)
    room = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name="messages", related_query_name="message")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages", related_query_name="message")

    class Meta:
        verbose_name = "Message"
        verbose_name_plural= "Messages"

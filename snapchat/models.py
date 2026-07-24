from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class FriendRequest(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        
    
    def __str__(self):
        return f"FriendRequest(from={self.from_user.username}, to={self.to_user.username}, status={self.status})"

class Conversation(models.Model):
   participants = models.ManyToManyField(User, related_name='conversations')
   created_at = models.DateTimeField(auto_now_add=True)
   
   
   def __str__(self):
       user = ", ".join(
           user.username
            for user in self.participants.all()
        )
       return user
   
    
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)
    
    
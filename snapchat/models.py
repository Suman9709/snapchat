from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class FriendRequest(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        
    from_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        
    
    def __str__(self):
        return f"FriendRequest(from={self.from_user.username}, to={self.to_user.username}, status={self.status})"
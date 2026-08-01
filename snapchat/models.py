from django.db import models
from django.contrib.auth.models import  AbstractUser
from django.contrib.auth import get_user_model


# Create your models here.
class SnapUser(AbstractUser):
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    bio = models.CharField(max_length=256, blank=True, null=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)


class UserLocation(models.Model):
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='location',
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.latitude}, {self.longitude}"

class FriendRequest(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        
    from_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        
    
    def __str__(self):
        return f"FriendRequest(from={self.from_user.username}, to={self.to_user.username}, status={self.status})"

class Conversation(models.Model):
    
   class Mode(models.TextChoices):
        KEEP='keep','Keep'
        ON_CLOSE='on_close','ON_CLOSE',
        AFTER_24HR = "after_24_hr","After_24_hr"
        
   participants = models.ManyToManyField(get_user_model(), related_name='conversations')
   mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.KEEP)
   streak = models.PositiveIntegerField(default=0, editable=False)
   last_snap_date = models.DateField(null=True, blank=True)
   last_snap_send = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='last_snap_sent' )
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   
   @property 
   def last_message(self):    
        return self.messages.order_by("-created_at").first()
   def __str__(self):
       user = ", ".join(
           user.username
            for user in self.participants.all()
        )
       return user
   
    
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField(blank=True)
    image = models.ImageField(upload_to='snaps', blank=True, null=True)
    seen = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Message(from={self.sender.username}, message={self.message[:20]}...)"
    
class Snap(models.Model):
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='sent_snaps')
    image = models.ImageField(upload_to='snaps/')
    caption = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f"{self.sender.username}'s snap"
    
    
class SnapReceiver(models.Model):
    snap = models.ForeignKey(Snap, on_delete=models.CASCADE, related_name='receiver')
    receiver = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='received_snaps')
    opend = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.receiver.username} received {self.snap.id}"

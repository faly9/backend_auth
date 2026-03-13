from django.db import models
from django.conf import settings  # <-- important pour AUTH_USER_MODEL

class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ← utiliser ça à la place de User
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ← idem
        on_delete=models.CASCADE,
        related_name="received_messages"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.content}"
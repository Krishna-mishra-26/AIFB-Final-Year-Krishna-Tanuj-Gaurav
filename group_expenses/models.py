from django.db import models
from django.conf import settings


class Group(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"

class GroupExpense(models.Model):
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
    date = models.DateField()
    paid_by = models.ForeignKey(GroupMember, on_delete=models.CASCADE, related_name="expenses")
    split_members = models.ManyToManyField(GroupMember)
    split_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.description

class Settlement(models.Model):
    member = models.ForeignKey(GroupMember, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    settled = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.member.name} - {self.amount}"


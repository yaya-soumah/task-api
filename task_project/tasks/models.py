from django.db.models.fields import CharField
from django.utils import timezone

from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator
from django.contrib.auth.models import User


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Project: {self.name}"

    def get_progress(self):
        tasks = UrgentTask.objects.filter(project=self)
        if not tasks:
            return 0
        completed = sum(1 for t in tasks if  t.taskstatus.completed)
        return (completed / len(tasks)) * 100

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1),MaxValueValidator(5)], db_index=True)
    user=models.ForeignKey(User,on_delete=models.CASCADE, default=1, db_index=True)
    tags = models.ManyToManyField(Tag, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.title} (Priority: {self.priority})"

    class Meta:
        abstract = True

class UrgentTask(Task):
    # deadline = models.CharField(max_length=50)
    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subtasks')
    depth = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.parent:
            self.depth = self.parent.depth + 1
            if self.depth > 5:
                raise ValueError("Max subtask depth exceeded")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (Priority: {self.priority}, Deadline: {self.deadline})"

    class Meta:
        indexes = [
            models.Index(fields=['user','priority'], name='user_priority_idx'),
        ]

class TaskStatus(models.Model):
    task = models.OneToOneField(UrgentTask, on_delete=models.CASCADE, primary_key=True)
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

class TaskComment(models.Model):
    task = models.ForeignKey(UrgentTask, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['task','created_at'])]

class RegularTask(Task):
    notes = models.TextField()

    def __str__(self):
        return f"{self.title} (Priority: {self.priority}, Notes: {self.notes})"


class Deadline(models.Model):
    date = models.DateTimeField(default=timezone.now)
    task = models.OneToOneField(UrgentTask, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return f"Due: {self.date}"


class TaskAssignment(models.Model):
    task = models.ForeignKey(UrgentTask, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('owner','Owner'),('reviewer','Reviewer')], default='owner')

    class Meta:
        unique_together = ('task','user')
        indexes= [models.Index(fields=['task','user'])]

class TaskPriorityHistory(models.Model):
    task = models.ForeignKey(UrgentTask, on_delete=models.CASCADE, related_name='priority_history')
    old_priority = models.IntegerField(null=True)
    new_priority = models.IntegerField()
    changed_at = models.DateTimeField(auto_now=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        indexes = [models.Index(fields=['task','changed_at'])]
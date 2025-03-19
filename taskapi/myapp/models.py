from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Task(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    priority = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)

    def __str__(self):
        return f"{self.title} (Priority: {self.priority})"

    class Meta:
        indexes = [models.Index(fields=['priority'])]

class UrgentTask(Task):
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependencies_list')
    subtasks = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='parent_tasks')
    depth = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.parent:
            self.depth = self.parent.depth + 1
            if self.depth > 5:
                raise ValueError("Max subtask depth exceeded")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (Priority: {self.priority})"

class RegularTask(Task):
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} (Priority: {self.priority}, Notes: {self.notes})"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class TaskStatus(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='status')  # Changed to OneToOne
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Status for {self.task}: {'Completed' if self.completed else 'Pending'}"

class Deadline(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='deadline')  # OneToOne for clarity
    date = models.DateTimeField()

    def __str__(self):
        return f"Due: {self.date}"

class Project(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Project: {self.name}"

    def get_progress(self):
        tasks = UrgentTask.objects.filter(project=self)
        if not tasks:
            return 0
        completed = sum(1 for t in tasks if t.status.completed)  # Updated related_name
        return (completed / len(tasks)) * 100

class TaskAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('owner', 'Owner'), ('reviewer', 'Reviewer')], default='owner')

    class Meta:
        unique_together = ('task', 'user')
        indexes = [models.Index(fields=['task', 'user'])]

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class TaskPriorityHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='priority_history')
    old_priority = models.IntegerField()
    new_priority = models.IntegerField()
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now=True)
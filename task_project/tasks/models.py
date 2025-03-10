from django.db import models

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=100)
    priority = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.title} (Priority: {self.priority})"

    class Meta:
        abstract = True


class UrgentTask(Task):
    deadline = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.title} (Priority: {self.priority}, Deadline: {self.deadline})"

class RegularTask(Task):
    notes = models.TextField()

    def __str__(self):
        return f"{self.title} (Priority: {self.priority}, Notes: {self.notes})"

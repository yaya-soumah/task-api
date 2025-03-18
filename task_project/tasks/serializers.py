from django.utils import timezone
from rest_framework import serializers
from .models import UrgentTask, RegularTask, Tag, TaskStatus, Project, TaskComment, TaskAssignment, Deadline, TaskPriorityHistory

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ['id', 'completed', 'updated_at']

class DeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deadline
        fields = ['date']

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ['id', 'name', 'user']

    def create(self, validated_data):
        return Project.objects.create(**validated_data)

class TaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields = ['user', 'role']

class TaskPriorityHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskPriorityHistory
        fields = ['old_priority', 'new_priority', 'changed_at', 'changed_by']

class TaskCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = ['id', 'text', 'created_at']

class UrgentTaskSerializer(serializers.ModelSerializer):
    status = TaskStatusSerializer(read_only=True)  # Updated related_name
    comments = TaskCommentSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    dependencies = serializers.PrimaryKeyRelatedField(many=True, queryset=UrgentTask.objects.all(), required=False)
    parent = serializers.PrimaryKeyRelatedField(queryset=UrgentTask.objects.all(), allow_null=True, required=False)
    subtasks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    deadline = DeadlineSerializer(read_only=True)
    serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), allow_null=True, required=False)
    assignments = TaskAssignmentSerializer(many=True, read_only=True)
    priority_history = TaskPriorityHistorySerializer(many=True, read_only=True)

    class Meta:
        model = UrgentTask
        fields = ['id', 'title', 'priority', 'user', 'deadline', 'tags', 'dependencies', 'parent', 'subtasks', 'depth', 'project', 'assignments', 'comments', 'priority_history', 'status']

    def create(self, validated_data):
        # Pop ManyToMany and ForeignKey fields to handle separately
        tags = validated_data.pop('tags', [])
        dependencies = validated_data.pop('dependencies', [])
        parent = validated_data.pop('parent', None)
        project = validated_data.pop('project', None)

        task = UrgentTask.objects.create(**validated_data)

        if tags:
            task.tags.set(tags)
        if dependencies:
            task.dependencies.set(dependencies)
        if parent:
            task.parent = parent
        if project:
            task.project = project

        TaskStatus.objects.create(task=task)
        Deadline.objects.create(task=task, date=validated_data.get('deadline', timezone.now()))
        TaskAssignment.objects.get_or_create(task=task, user=task.user, defaults={'role': 'owner'})

        task.save()
        return task

class RegularTaskSerializer(serializers.ModelSerializer):
    status = TaskStatusSerializer(read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = RegularTask
        fields = ['id', 'title', 'priority', 'user', 'notes', 'tags', 'status', 'comments', 'created_at']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        task = RegularTask.objects.create(**validated_data)
        if tags:
            task.tags.set(tags)
        TaskStatus.objects.create(task=task)
        return task
from rest_framework import serializers
from tasks.models import UrgentTask, RegularTask, Tag, TaskStatus, Deadline, Project, TaskAssignment, TaskComment, \
    TaskPriorityHistory


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id','name']

class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStatus
        fields = ['completed','updated_at']

class DeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deadline
        fields=['date']

class ProjectSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id','name', 'created_at', 'progress']

    def get_progress(self,obj):
        return obj.get_progress()

class TaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields =['user','role']

class TaskCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields=['user','text','created_at']

class TaskPriorityHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskPriorityHistory
        fields=['old_priority','new_priority','changed_at','changed_by']

class UrgentTaskSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    status = TaskStatusSerializer(read_only=True, source='taskstatus')
    dependencies = serializers.PrimaryKeyRelatedField(many=True, queryset=UrgentTask.objects.all(), required=False)
    parent=serializers.PrimaryKeyRelatedField(queryset=UrgentTask.objects.all(), allow_null=True,required=False)
    subtasks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    deadline = DeadlineSerializer(read_only=True)
    project=ProjectSerializer(read_only=True)
    assignments = TaskAssignmentSerializer(many=True, read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    priority_history = TaskPriorityHistorySerializer(read_only=True, many=True)

    class Meta:
        model = UrgentTask
        fields = ['id','title','priority','user','deadline','tags','status','dependencies', 'parent', 'subtasks','depth','project','assignments', 'comments', 'priority_history']


class RegularTaskSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    class Meta:
        model = RegularTask
        fields=['id','title','priority','user', 'notes','tags']



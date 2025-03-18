from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UrgentTask, RegularTask, Tag, TaskStatus, Project, TaskComment, TaskPriorityHistory
from .serializers import UrgentTaskSerializer, RegularTaskSerializer, ProjectSerializer


@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def urgent_task_api(request):
    if request.method == 'GET':
        urgent_tasks = UrgentTask.objects.filter(user=request.user).select_related('user', 'project', 'status', 'deadline').prefetch_related('tags', 'comments', 'subtasks', 'dependencies', 'priority_history', 'assignments')
        priority = request.query_params.get('priority')
        tag = request.query_params.get('tag')
        if priority:
            urgent_tasks = urgent_tasks.filter(priority=priority)
        if tag:
            urgent_tasks = urgent_tasks.filter(tags__name=tag)
        serializer = UrgentTaskSerializer(urgent_tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = UrgentTaskSerializer(data=data)
        if serializer.is_valid():
            task = serializer.save()
            if 'tags' in request.data:
                task.tags.set([Tag.objects.get_or_create(name=name)[0] for name in request.data['tags']])
            if 'comments' in request.data:
                TaskComment.objects.bulk_create(
                    [TaskComment(task=task, user=request.user, text=text) for text in request.data['comments']]
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        task_id = request.data.get('id')
        if not task_id:
            return Response({"error": "Missing id"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            task = UrgentTask.objects.get(id=task_id, user=request.user)
            serializer = UrgentTaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                old_priority = task.priority
                serializer.save()

                if 'tags' in request.data:
                    task.tags.set([Tag.objects.get_or_create(name=name)[0] for name in request.data['tags']])
                if 'dependencies' in request.data:
                    task.dependencies.set(request.data['dependencies'])
                if 'parent' in request.data:
                    task.parent = UrgentTask.objects.get(id=request.data['parent']) if request.data['parent'] else None
                    task.save()
                if 'subtasks' in request.data:
                    task.subtasks.set(request.data['subtasks'])
                if 'project' in request.data:
                    task.project = Project.objects.get(id=request.data['project']) if request.data['project'] else None
                if 'comments' in request.data:
                    task.comments.all().delete()
                    TaskComment.objects.bulk_create(
                        [TaskComment(task=task, user=request.user, text=text) for text in request.data['comments']]
                    )
                if 'priority' in request.data and request.data['priority'] != old_priority:
                    TaskPriorityHistory.objects.create(
                        task=task,
                        old_priority=old_priority,
                        new_priority=request.data['priority'],
                        changed_by=request.user
                    )
                if 'completed' in request.data:
                    if task.status:
                        task.status.completed = request.data['completed']
                        task.status.save()
                    else:
                        TaskStatus.objects.create(task=task, completed=request.data['completed'])
                task.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UrgentTask.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def regular_task_api(request):
    if request.method == 'GET':
        regular_tasks = RegularTask.objects.filter(user=request.user).select_related('user', 'project', 'status').prefetch_related('tags', 'comments')
        priority = request.query_params.get('priority')
        tag = request.query_params.get('tag')
        if priority:
            regular_tasks = regular_tasks.filter(priority=priority)
        if tag:
            regular_tasks = regular_tasks.filter(tags__name=tag)
        serializer = RegularTaskSerializer(regular_tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = RegularTaskSerializer(data=data)
        if serializer.is_valid():
            task = serializer.save()
            if 'tags' in request.data:
                task.tags.set([Tag.objects.get_or_create(name=name)[0] for name in request.data['tags']])
            if 'comments' in request.data:
                TaskComment.objects.bulk_create(
                    [TaskComment(task=task, user=request.user, text=text) for text in request.data['comments']]
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        task_id = request.data.get('id')
        if not task_id:
            return Response({"error": "Missing id"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            task = RegularTask.objects.get(id=task_id, user=request.user)
            serializer = RegularTaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                if 'tags' in request.data:
                    task.tags.set([Tag.objects.get_or_create(name=name)[0] for name in request.data['tags']])
                if 'completed' in request.data:
                    task.status.completed = request.data['completed']
                    task.status.save()
                if 'comments' in request.data:
                    task.comments.all().delete()
                    TaskComment.objects.bulk_create(
                        [TaskComment(task=task, user=request.user, text=text) for text in request.data['comments']]
                    )
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except RegularTask.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_task_api(request, task_type, task_id):
    try:
        if task_type == 'urgent':
            task = UrgentTask.objects.select_related('user').get(id=task_id, user=request.user)
        elif task_type == 'regular':
            task = RegularTask.objects.select_related('user').get(id=task_id, user=request.user)
        else:
            return Response({"error": "Invalid task type"}, status=status.HTTP_400_BAD_REQUEST)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except (UrgentTask.DoesNotExist, RegularTask.DoesNotExist):
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_progress(request, task_id):
    try:
        task = UrgentTask.objects.select_related('user', 'parent', 'status').prefetch_related('subtasks', 'subtasks__status').get(id=task_id, user=request.user)
        subtasks = task.subtasks.all()
        if not subtasks:
            progress = 100 if task.status.completed else 0
        else:
            completed = sum(1 for st in subtasks if st.status.completed)
            progress = (completed / len(subtasks)) * 100
        return Response({"task": task_id, "progress": progress}, status=status.HTTP_200_OK)
    except UrgentTask.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def project_api(request):
    if request.method == 'POST':
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
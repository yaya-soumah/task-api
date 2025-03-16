from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import Http404
from django.utils import timezone


from tasks.models import UrgentTask, RegularTask, Tag, TaskStatus, Deadline, Project, TaskAssignment, TaskComment, \
    TaskPriorityHistory
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UrgentTaskSerializer, RegularTaskSerializer

def task_list(request):
    if request.method == 'POST':
        task_type = request.POST.get('task_type')
        title = request.POST.get('title')
        priority = int(request.POST.get('priority', 1))
        if task_type == 'urgent':
            deadline = request.POST.get('deadline')
            UrgentTask.objects.create(title=title, deadline=deadline, priority=priority, user=request.user)
        else:
            notes = request.POST.get('notes')
            RegularTask.objects.create(title=title, notes=notes, priority=priority, user=request.user)
        return redirect('task_list')

    urgent_tasks = UrgentTask.objects.filter(user=request.user)
    regular_tasks = RegularTask.objects.filter(user=request.user)
    context = {
        'urgent_tasks': urgent_tasks,
        'regular_tasks': regular_tasks
    }
    return render(request, 'tasks/task_list.html', context)

def delete_task(request, type, task_id):
    try:
        if type == 'urgent':
            task = UrgentTask.objects.get(id=task_id, user=request.user)
        elif type == 'regular':
            task = RegularTask.objects.get(id=task_id, user=request.user)
        else:
            raise Http404("Invalid task type")
        task.delete()
    except (UrgentTask.DoesNotExist, RegularTask.DoesNotExist):
        raise Http404("Task not found or not yours")
    return redirect('task_list')

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def urgent_task_api(request):
    if request.method == 'GET':
        urgent_tasks = UrgentTask.objects.filter(user=request.user).select_related('user', 'parent',
                                                                                   'project').prefetch_related('tags',
                                                                                                               'taskstatus',
                                                                                                               'dependencies',
                                                                                                               'subtasks',
                                                                                                               'assignments',
                                                                                                               'comments')
        priority = request.query_params.get('priority')
        title = request.query_params.get('title')
        tag = request.query_params.get('tag')
        project = request.query_params.get('project')
        if priority:
            urgent_tasks = urgent_tasks.filter(priority=priority)
        if title:
            urgent_tasks = urgent_tasks.filter(title=title)
        if tag:
            urgent_tasks = urgent_tasks.filter(tags__name=tag)
        if project:
            urgent_tasks = urgent_tasks.filter(project__id=project)
        serializer = UrgentTaskSerializer(urgent_tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = UrgentTaskSerializer(data=data)
        if serializer.is_valid():
            task = serializer.save()
            if 'tags' in request.data:
                tags = request.data.get('tags')
                for tag_name in tags:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    task.tags.add(tag)
            if 'dependencies' in request.data:
                for dep_id in request.data['dependencies']:
                    dep = UrgentTask.objects.get(id=dep_id)
                    if dep_id == task.id or dep in task.dependencies.all():
                        return Response({"error": "Circular dependency"}, status=status.HTTP_400_BAD_REQUEST)
                    task.dependencies.add(dep)
            if 'parent' in request.data and request.data['parent']:
                parent = UrgentTask.objects.get(id=request.data['parent'])
                if parent.id == task.id:
                    return Response({"error": "Task cannot be its own parent"}, status=status.HTTP_400_BAD_REQUEST)
                task.parent = parent
                # task.save()
            if 'project' in request.data or 'project_name' in request.data:
                project_id = request.data.get('project', None )

                if project_id:
                    project = Project.objects.get(id=project_id, user=request.user)
                else:
                    project_name = request.data.get('project_name','Unnamed Project')
                    project, _ = Project.objects.get_or_create(name=project_name, user=request.user)
                task.project = project

            task.save()
            if 'deadline' in request.data:
                Deadline.objects.create(task=task, date=request.data['deadline'])
            else:
                Deadline.objects.create(task=task,date=timezone.now())
            TaskStatus.objects.create(task=task)

            TaskAssignment.objects.get_or_create(task=task, user=request.user, defaults={'role': 'owner'})
            if 'reviewers' in request.data:
                for user_id in request.data['reviewers']:
                    user = User.objects.get(id=user_id)
                    TaskAssignment.objects.get_or_create(task=task, user=user, role='reviewer')

            if 'comments' in request.data:
                for comment in request.data['comments']:
                    TaskComment.objects.create(task=task, user=request.user, text=comment)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        task_id = request.data.get('id')
        if not task_id:
            return Response({"error": "Missing id"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            task = UrgentTask.objects.select_related('user','parent', 'project').prefetch_related('tags','taskstatus','dependencies','subtasks', 'assignments', 'comments').get(id=task_id, user=request.user)
            serializer = UrgentTaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                old_priority = task.priority
                serializer.save()

                if 'tags' in request.data:
                    task.tags.clear()
                    for tag_name in request.data['tags']:
                        tag,_= Tag.objects.get_or_create(name=tag_name)
                        task.tags.add(tag)
                if 'dependencies' in request.data:
                    task.dependencies.clear()
                    for dep_id in request.data['dependencies']:
                        dep = UrgentTask.objects.get(id=dep_id)
                        task.dependencies.add(dep)
                if 'parent' in request.data:
                    if request.data['parent'] is None:
                        task.parent = None
                    else:
                        task.parent = UrgentTask.objects.get(id=request.data['parent'])
                if 'completed' in request.data:
                    task.taskstatus.completed = request.data['completed']
                    task.taskstatus.save()
                if 'comments' in request.data:
                    task.comments.all().delete()
                    for comment_text in request.data['comments']:
                        TaskComment.objects.create(task=task, user=request.user, text=comment_text)

                if 'priority' in request.data and request.data['priority'] != old_priority:
                    TaskPriorityHistory.objects.create(task=task, old_priority=old_priority,
                                                       new_priority=request.data['priority'],
                                                       changed_by=request.user)


                task.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UrgentTask.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def regular_task_api(request):
    if request.method == 'GET':
        regular_tasks = RegularTask.objects.filter(user=request.user).select_related('tags', 'taskstatus')
        priority = request.query_params.get('priority')
        title = request.query_params.get('title')
        tag = request.query_params.get('tag')
        project = request.query_params.get('project')

        if priority:
            regular_tasks = regular_tasks.filter(priority=priority)
        if title:
            regular_tasks = regular_tasks.filter(title=title)
        if tag:
            regular_tasks = regular_tasks.filter(tags__name=tag)
        if project:
            regular_tasks = regular_tasks.filter(project__id=project)

        serializer = RegularTaskSerializer(regular_tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    elif request.method == 'POST':
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = RegularTaskSerializer(data=data)

        if serializer.is_valid():

            task = serializer.save()

            if 'tags' in request.data:  # Fixed

                for tag_name in request.data['tags']:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)

                    task.tags.add(tag)

            if 'project' in request.data:
                project = Project.objects.get(id=request.data['project'], user=request.user)

                task.project = project

            TaskStatus.objects.create(task=task)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        task_id = request.data.get('id')
        if not task_id:
            return Response({"error": "Missing id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = RegularTask.objects.select_related('user').get(id=task_id, user=request.user)
            serializer = RegularTaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()

                if 'tags' in request.data['tags']:
                    for tag_name in request.data['tags']:
                        tag,_ = Tag.objects.get_or_create(name=tag_name)
                        task.tags.add(tag)

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
        task = UrgentTask.objects.select_related('user','parent').prefetch_related('subtasks','taskstatus').get(id=task_id, user=request.user)
        subtasks = task.subtasks.all()
        if not subtasks:
            progress = 100 if task.taskstatus.completed else 0
        else:
            completed = sum(1 for st in subtasks if st.taskstatus.completed)
            progress = (completed / len(subtasks)) * 100
        return Response({"task": task_id, "progress": progress}, status=status.HTTP_200_OK)
    except UrgentTask.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
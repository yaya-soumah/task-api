from django.shortcuts import render, redirect
from django.http import Http404
from tasks.models import UrgentTask, RegularTask
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import UrgentTaskSerializer, RegularTaskSerializer

def task_list(request):
    if request.method == 'POST':
        task_type = request.POST.get('task_type')
        title = request.POST.get('title')
        priority = int(request.POST.get('priority', 1))  # Ensure int
        if task_type == 'urgent':
            deadline = request.POST.get('deadline')
            UrgentTask.objects.create(title=title, deadline=deadline, priority=priority)
        else:
            notes = request.POST.get('notes')
            RegularTask.objects.create(title=title, notes=notes, priority=priority)  # Fixed!
        return redirect('task_list')

    urgent_tasks = UrgentTask.objects.all()
    regular_tasks = RegularTask.objects.all()
    context = {
        'urgent_tasks': urgent_tasks,
        'regular_tasks': regular_tasks
    }
    return render(request, 'tasks/task_list.html', context)

def delete_task(request, task_type, task_id):
    try:
        if task_type == 'urgent':
            task = UrgentTask.objects.get(id=task_id)
        elif task_type == 'regular':
            task = RegularTask.objects.get(id=task_id)
        else:
            raise Http404("Invalid task type")
        task.delete()
    except (UrgentTask.DoesNotExist, RegularTask.DoesNotExist):
        raise Http404("Task not found")
    return redirect('task_list')

@api_view(['GET','POST'])
def task_api(request):
    if request.method == 'GET':
        urgent_tasks = UrgentTask.objects.all()
        regular_tasks = RegularTask.objects.all()
        urgent_serializer = UrgentTaskSerializer(urgent_tasks, many=True)
        regular_serializer = RegularTaskSerializer(regular_tasks, many=True)
        return Response({'urgent_tasks': urgent_serializer.data, 'regular_tasks': regular_serializer.data})
    elif request.method == 'POST':
        task_type = request.data.get('task_type')
        if task_type == 'urgent':
            serializer = UrgentTaskSerializer(data=request.data)
        else:
            serializer = RegularTaskSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['DELETE'])
def delete_task_api(request, task_type, task_id):
    try:
        if type == 'urgent':
            task = UrgentTask.objects.get(id=task_id)
            serializer = UrgentTaskSerializer(task)
        elif type == 'regular':
            task = RegularTask.objects.get(id=task_id)
            serializer = RegularTaskSerializer(task)
        else:
            return Response({"error" : "Invalid task type"}, status=400)
        task.delete()
        return Response(status=204)
    except (UrgentTask.DoesNotExist, RegularTask.DoesNotExist):
        return Response({"error" : "Task not found"}, status=404)

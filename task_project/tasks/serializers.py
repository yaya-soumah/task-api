from rest_framework import serializers
from tasks.models import UrgentTask, RegularTask

class UrgentTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = UrgentTask
        fields = ['id','title','priority','deadline']


class RegularTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularTask
        fields=['id','title','priority','notes']


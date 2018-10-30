# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class UserNode(models.Model):
    host = models.CharField(max_length=50)
    port = models.CharField(max_length=50)
    ipd = models.CharField(max_length=50)


class File(models.Model):
    name = models.CharField(max_length=50)
    users = models.ManyToManyField(UserNode, related_name='files', blank=True)



from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNode
        fields = '__all__'


class FileSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True)
    class Meta:
        model = File
        fields = '__all__'



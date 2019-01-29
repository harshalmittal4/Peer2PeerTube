# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import Http404
from .models import *




class UserAdd(APIView):
    """
    List all snippets, or create a new snippet.
    """
    serializer_class = UserSerializer

    def get(self, request, format=None):
        snippets = UserNode.objects.all()
        serializer = UserSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDelete(APIView):

    def get_object(self, ipd):
        try:
            return UserNode.objects.get(ipd=ipd)
        except Snippet.DoesNotExist:
            raise Http404

    def get(self, request,ipd, format=None):
        snippet = self.get_object(ipd)
        files = snippet.files.all()
        snippet.delete()
        for file in files:
            if file.users.count()==0:
                file.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class FileAdd(APIView):
    """
    List all snippets, or create a new snippet.
    """
    serializer_class = FileSerializer
    def get_object(self, name):
        try:
            return File.objects.get(name=name)
        except Snippet.DoesNotExist:
            raise Http404

    def get(self, request, name, format=None):
        file = self.get_object(name)
        serializer = FileSerializer(file)
        return Response(serializer.data)

    def post(self, request,name, format=None):
        filename  = request.data['name']
        ipd  = request.data['users']
        print(ipd)
        user = UserNode.objects.get(ipd=ipd)
        files  = File.objects.values_list('name', flat=True).distinct()
        if filename in files:
            file = File.objects.get(name=filename)
            file.users.add(user)
            file.save()
        else:
            file = File.objects.create(name = filename)
            file.save()
            file.users.add(user)
        serializer = FileSerializer(file)
        return Response(serializer.data, status=status.HTTP_201_CREATED)




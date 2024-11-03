from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Family

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class FamilySerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True)

    class Meta:
        model = Family
        fields = ['id', 'name', 'members']

    def create(self, validated_data):
        members_data = validated_data.pop('members')
        family = Family.objects.create(**validated_data)
        family.members.set(members_data)
        return family

    def update(self, instance, validated_data):
        members_data = validated_data.pop('members', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        if members_data is not None:
            instance.members.set(members_data)

        return instance
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class CreateCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    board_id = serializers.IntegerField()


class CreateTicketSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()


class UpdateTicketSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100, allow_null=True, required=False)
    body = serializers.CharField(allow_null=True, required=False)
    due_date = serializers.DateField(allow_null=True, required=False)
    priority = serializers.IntegerField(allow_null=True, required=False)
    category_id = serializers.IntegerField(allow_null=True, required=False)

    def validate(self, attrs):
        if (attrs.get('priority') is not None and attrs.get('category_id') is None) \
                or (attrs.get('priority') is None and attrs.get('category_id') is not None):
            raise ValidationError('Both priority and category_id should be provided (or not)')

        return attrs


class CreateTicketAssignmentSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField()
    board_membership_id = serializers.IntegerField()

"""Serializers documenting the AED API payloads (OpenAPI via drf-spectacular)."""

from rest_framework import serializers


class AllowedValueSerializer(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()


class FieldGroupSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()


class FieldSpecSerializer(serializers.Serializer):
    """One column of the standard AED schema."""

    name = serializers.CharField()
    group = serializers.CharField()
    group_label = serializers.CharField()
    type = serializers.ChoiceField(choices=["string", "number", "integer", "boolean", "date"])
    obligation = serializers.ChoiceField(choices=["wymagane", "zalecane", "opcjonalne"])
    required = serializers.BooleanField()
    label = serializers.CharField()
    description = serializers.CharField()
    description_en = serializers.CharField()
    example = serializers.CharField(allow_blank=True)
    allowed_values = AllowedValueSerializer(many=True)
    pattern = serializers.CharField(allow_null=True)
    minimum = serializers.FloatField(allow_null=True)
    maximum = serializers.FloatField(allow_null=True)
    max_length = serializers.IntegerField(allow_null=True)
    osm_tag = serializers.CharField(allow_null=True)


class SchemaDocumentSerializer(serializers.Serializer):
    """The standard AED schema ("wzorcowy zakres danych")."""

    name = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    title_en = serializers.CharField()
    description = serializers.CharField()
    license = serializers.CharField()
    obligations = serializers.ListField(child=serializers.CharField())
    groups = FieldGroupSerializer(many=True)
    fields = FieldSpecSerializer(many=True)

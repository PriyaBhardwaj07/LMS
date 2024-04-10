from rest_framework import serializers
from exam.models.allmodels import (
    Choice, 
    Course, 
    CourseStructure,
    Notification,
    Question, 
    UploadReadingMaterial,
    UploadVideo, 
    Quiz
)
class EditCourseInstanceSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100, required=True)
    summary = serializers.CharField(required=True)

    def validate(self, data):
        if not data['title'] or not data['summary']:
            raise serializers.ValidationError("Title and summary cannot be empty")
        return data
    
class NotificationSerializer(serializers.ModelSerializer):
    
    created_at = serializers.SerializerMethodField()
    
    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")
    
    def validate(self, data):
        # Field Existence and Null Field Handling
        required_fields = ['id', 'course', 'message', 'created_at']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise serializers.ValidationError(f"{field} is required")
        return data
    
    class Meta:
        model = Notification
        fields = ['id', 'message', 'created_at']
        
class UploadReadingMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadReadingMaterial
        fields = ['title', 'reading_content']

    def validate(self, data):
        """
        Validate the input data.
        """
        # Check if at least one of title or reading_content is provided
        if 'title' not in data and 'reading_content' not in data:
            raise serializers.ValidationError("At least one of title or reading_content is required.")
        return data
    
class EditVideoMaterialSerializer(serializers.ModelSerializer):
    """
    Serializer for editing video material instances.
    """

    class Meta:
        model = UploadVideo
        fields = ['title', 'video', 'summary']
        read_only_fields = ['uploaded_at']

    def validate(self, data):
        # Ensure either title or video is provided
        if 'title' not in data and 'video' not in data:
            raise serializers.ValidationError("Either 'title' or 'video' must be provided.")
        return data

class EditQuizInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'answers_at_end', 'exam_paper', 'pass_mark']

    def validate(self, data):
        # Check if title is provided
        if 'title' in data and not data['title']:
            raise serializers.ValidationError("Title cannot be empty.")

        # Check if description is provided
        if 'description' in data and not data['description']:
            raise serializers.ValidationError("Description cannot be empty.")

        # Check if pass_mark is a valid percentage
        if 'pass_mark' in data:
            pass_mark = data['pass_mark']
            if pass_mark < 0 or pass_mark > 100:
                raise serializers.ValidationError("Pass mark should be between 0 and 100.")

        # Your custom validations here
        return data

class EditingQuizInstanceOnConfirmationSerializer(serializers.Serializer):
    confirmation = serializers.BooleanField(required=True)
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False)
    answers_at_end = serializers.BooleanField(required=False)
    exam_paper = serializers.BooleanField(required=False)
    pass_mark = serializers.IntegerField(required=False)

    def validate(self, data):
        confirmation = data.get('confirmation')
        if confirmation is None:
            raise serializers.ValidationError("Confirmation field is required.")

        if confirmation and not all([data.get('title'), data.get('description'), data.get('answers_at_end'),
                                     data.get('exam_paper'), data.get('pass_mark')]):
            raise serializers.ValidationError("All fields are required when confirmation is true.")

        return data
    
class EditQuestionInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['figure', 'content', 'explanation', 'choice_order']

    def validate(self, data):
        # Check if content is provided when not null
        if 'content' in data and not data['content']:
            raise serializers.ValidationError("Content cannot be empty when provided.")

        return data

class EditingQuestionInstanceOnConfirmationSerializer(serializers.Serializer):
    confirmation = serializers.BooleanField(required=True)
    figure = serializers.ImageField(required=False)
    content = serializers.CharField(max_length=1000, required=False)
    explanation = serializers.CharField(max_length=2000, required=False)
    choice_order = serializers.CharField(max_length=30, required=False)

    def validate(self, data):
        confirmation = data.get('confirmation')
        if confirmation is None:
            raise serializers.ValidationError("Confirmation field is required.")

        # Check if content is provided when confirmation is true
        if confirmation and 'content' not in data:
            raise serializers.ValidationError("Content field is required when confirmation is true.")

        return data
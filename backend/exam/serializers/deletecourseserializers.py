from rest_framework import serializers
from exam.models.allmodels import Course, Question, Quiz, UploadReadingMaterial, UploadVideo

class DeleteSelectedCourseSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value)
            if course.active:
                raise serializers.ValidationError("Course must be inactive before deletion.")
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found.")
        return value

class DeleteReadingMaterialSerializer(serializers.Serializer):
    reading_material_id = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            "required": "Reading material ID is required.",
            "min_value": "Reading material ID must be a positive integer."
        }
    )

    def validate_reading_material_id(self, value):
        # Perform additional validation if needed
        if not UploadReadingMaterial.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Reading material with the provided ID does not exist.")
        return value

class DeleteVideoMaterialSerializer(serializers.Serializer):
    pass

class DeleteSelectedQuizSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            "required": "Quiz ID is required.",
            "min_value": "Quiz ID must be a positive integer."
        }
    )

    def validate_quiz_id(self, value):
        # Check if the quiz with the provided ID exists
        if not Quiz.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Quiz with the provided ID does not exist.")
        return value
    
class DeleteQuestionSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            "required": "Question ID is required.",
            "min_value": "Question ID must be a positive integer."
        }
    )

    def validate_question_id(self, value):
        # Check if the question with the provided ID exists
        if not Question.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Question with the provided ID does not exist.")
        return value
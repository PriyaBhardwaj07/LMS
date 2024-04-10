from datetime import timezone
from rest_framework import serializers
from exam.models.allmodels import Course, CourseEnrollment
from exam.models.coremodels import User
from django.core.exceptions import ObjectDoesNotExist

class RegisteredCourseSerializer(serializers.ModelSerializer):
    
    updated_at = serializers.SerializerMethodField()

    def get_updated_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d")

    def validate(self, data):
        # Field Existence and Null Field Handling
        required_fields = ['id', 'title', 'updated_at','version_number']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise serializers.ValidationError(f"{field} is required")
        return data 
    class Meta:
        model = Course
        fields = ['id', 'title', 'updated_at','version_number']
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name']

    def validate(self, data):
        # Field Existence and Null Field Handling
        required_fields = ['id', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise serializers.ValidationError(f"{field} is required")
        return data 


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying records in CourseRegisterRecord model.
    """
    customer = serializers.CharField(source='customer.name', read_only=True)
    course = serializers.CharField(source='course.title', read_only=True)
    created_at = serializers.SerializerMethodField()  # Custom method to format created_at

    def get_created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d") 

    def validate(self, data):
        # Field Existence and Null Field Handling
        required_fields = ['customer', 'course', 'active']  
        for field in required_fields:
            if field not in data or data[field] is None:
                raise serializers.ValidationError(f"{field} is required")
        return data

    class Meta:
        model = CourseEnrollment
        fields = ['customer', 'course', 'created_at', 'active']  
         
class DisplayCourseEnrollmentSerializer(serializers.ModelSerializer):
    user_first_name = serializers.SerializerMethodField()
    user_last_name = serializers.SerializerMethodField()
    course_title = serializers.SerializerMethodField()  # Add this field

    class Meta:
        model = CourseEnrollment
        fields = ['user', 'user_first_name', 'user_last_name', 'course_title', 'active']  # Replace 'course' with 'course_title'

    def get_user_first_name(self, obj):
        return obj.user.first_name
    
    def get_user_last_name(self, obj):
        return obj.user.last_name

    def get_course_title(self, obj):  # Define method to get course title
        return obj.course.title  # Fetch the title of the course from the related object

    def validate(self, attrs):
        """
        Custom validation to ensure that the user and course fields exist.
        """
        user_id = attrs.get('user')
        course_id = attrs.get('course')
        
        # Check if the user exists
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")

        # Check if the course exists
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course does not exist.")

        return attrs

    def create(self, validated_data):
        return CourseEnrollment.objects.create(**validated_data)


class UnAssignCourseEnrollmentSerializer(serializers.Serializer):
    enrollment_ids = serializers.ListField(
        child=serializers.IntegerField(),  # Validates that each item in the list is an integer
        min_length=1,  # Ensures the list is not empty
        error_messages={
            'min_length': 'At least one enrollment ID must be provided.',  # Custom error message for empty list
        }
    )

    def validate_enrollment_ids(self, value):
        """
        Additional validation to check if enrollment IDs are valid and exist in the database.
        """
        # Check if all provided enrollment IDs exist in the database
        invalid_ids = []
        for enrollment_id in value:
            if not CourseEnrollment.objects.filter(id=enrollment_id).exists():
                invalid_ids.append(enrollment_id)

        if invalid_ids:
            raise serializers.ValidationError(f"The following enrollment IDs do not exist: {', '.join(map(str, invalid_ids))}")

        return value

    def validate(self, data):
        """
        Additional validation to ensure uniqueness of enrollment IDs.
        """
        enrollment_ids = data.get('enrollment_ids', [])

        # Check for duplicate enrollment IDs
        if len(enrollment_ids) != len(set(enrollment_ids)):
            raise serializers.ValidationError("Duplicate enrollment IDs are not allowed.")

        return data
    
class AssignCourseEnrollmentSerializer(serializers.Serializer):
    enrollment_ids = serializers.ListField(
        child=serializers.IntegerField(),  # Validates that each item in the list is an integer
        min_length=1,  # Ensures the list is not empty
        error_messages={
            'min_length': 'At least one enrollment ID must be provided.',  # Custom error message for empty list
        }
    )

    def validate_enrollment_ids(self, value):
        """
        Validate that all the provided enrollment IDs exist in the database.
        """
        for enrollment_id in value:
            try:
                CourseEnrollment.objects.get(id=enrollment_id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(f"Enrollment with ID {enrollment_id} does not exist.")
        return value
    
class EnrolledCoursesSerializer(serializers.ModelSerializer):
    """Serializer for displaying enrolled courses."""
    
    class Meta:
        model = CourseEnrollment
        fields = ['id', 'course', 'enrolled_at', 'updated_at']
        
    def validate(self, data):
        # Ensure that the enrolled_at date is not in the future
        enrolled_at = data.get('enrolled_at')
        if enrolled_at and enrolled_at > timezone.now():
            raise serializers.ValidationError("Enrollment date cannot be in the future.")
        
        # Ensure that updated_at is not before enrolled_at
        updated_at = data.get('updated_at')
        if updated_at and enrolled_at and updated_at < enrolled_at:
            raise serializers.ValidationError("Updated date cannot be before enrollment date.")
        
        return data

class EnrollmentDeleteSerializer(serializers.Serializer):
    """
    Serializer for deleting a course enrollment.
    """
    enrollment_id = serializers.IntegerField()

    def validate(self, data):
        # Validate enrollment_id
        if 'enrollment_id' not in data:
            raise serializers.ValidationError("Enrollment ID is required.")
        return data



from django.utils import timezone
from django.http import QueryDict
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from rest_framework import status
from django.contrib import messages
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from exam import serializers
from exam.serializers.maincourseserializers import DeleteQuestionSerializer, DeleteReadingMaterialSerializer, DeleteSelectedCourseSerializer, DeleteSelectedQuizSerializer
from exam.serializers.editcourseserializers import EditCourseInstanceSerializer, EditQuestionInstanceSerializer, EditQuizInstanceSerializer, EditVideoMaterialSerializer, EditingQuestionInstanceOnConfirmationSerializer, EditingQuizInstanceOnConfirmationSerializer, NotificationSerializer
from exam.models.allmodels import (
    ActivityLog,
    Course,
    Notification,
    UploadVideo,
    UploadReadingMaterial,
    CourseStructure,
    CourseRegisterRecord,
    CourseEnrollment,
    Progress,
    Quiz,
    Question,
    QuizAttemptHistory
)
from rest_framework.exceptions import NotFound, ValidationError

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator
# from exam.models.coremodels import *
from exam.serializers.createcourseserializers import (
    ActivateCourseSerializer,
    CourseSerializer, 
    CourseStructureSerializer,
    CreateChoiceSerializer,
    InActivateCourseSerializer, 
    UploadReadingMaterialSerializer, 
    UploadVideoSerializer, 
    QuizSerializer, 
    CreateCourseSerializer,
    CreateUploadReadingMaterialSerializer,
    CreateUploadVideoSerializer,
    CreateQuizSerializer,
    CreateQuestionSerializer,
)
import pandas as pd # type: ignore

class CourseInstanceDetailsView(APIView):
    """ 
    PUT :method updates the details of a course instance based on the provided course_id in the request body
    If the course instance is active, it creates a notification in the notification table.
    Returns appropriate responses based on success or failure.
    """
    """  in this we can edit the course instance """
    def put(self, request, format=None):
        try:
            course_id = request.data.get('course_id')
            course = Course.objects.get(pk=course_id)
            
            if not course:
                raise Course.DoesNotExist("No course found with the provided course ID.")
            if course.deleted_at:
                raise ValidationError("Course instance has been deleted")
            
            serializer = EditCourseInstanceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            course.title = serializer.validated_data.get('title')
            course.summary = serializer.validated_data.get('summary')
            course.updated_at = timezone.now()
            course.save()

            if course.active:
                latest_activity_log = ActivityLog.objects.latest('created_at')
                notification = Notification.objects.create(
                    message=latest_activity_log.message,
                    course=course
                )
                notification_data = {
                    "message": notification.message,
                    "created_at": notification.created_at
                }
                return Response({"message": "Course instance updated successfully", "notification": notification_data}, status=status.HTTP_200_OK)
            return Response({"message": "Course instance updated successfully"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            error_message = str(e)
            if isinstance(e, (ValidationError, Course.DoesNotExist)):
                error_message = "Invalid data: " + error_message
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST) 
    """  
    PATCH : This method soft-deletes a course instance based on the course_id provided in the request body.
    """

    def patch(self, request, format=None):
        serializer = DeleteSelectedCourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course_id = serializer.validated_data['course_id']

        try:
            # Fetch the course instance
            course = Course.objects.get(id=course_id)

            # Check if the course is active
            if course.active:
                raise ValidationError("Course must be inactive before deletion.")

            # Soft delete the course
            course.active = False
            course.deleted_at = timezone.now()
            course.save()

            # Delete related instances if they are associated only with this course
            self.delete_related_instances(course)

            return Response({"message": "Course soft deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_related_instances(self, course):
        # Delete mapped instances of course_id with reading material
        reading_materials = UploadReadingMaterial.objects.filter(courses=course)
        if reading_materials.exists():
            reading_materials.delete()

        # Delete mapped instances of course_id with video material
        video_materials = UploadVideo.objects.filter(courses=course)
        if video_materials.exists():
            video_materials.delete()

        # Delete mapped instances of course_id with quiz and associated questions
        quizzes = Quiz.objects.filter(courses=course)
        for quiz in quizzes:
            if quiz.questions.count() > 0:
                quiz.questions.all().delete()
            quiz.delete()
        """ 
        AFTER API TESTING :
        EDIT :  
        REQUEST BODY :
        {
        "course_id": 7,
        "title": "React",
        "summary": "This is React"
    }
        RESPONSE BODY :
        {
        "message": "Course instance updated successfully"
        }
        
                DELETE
            REQUEST BODY :{
        "course_id": 9
    }
        RESPONSE BODY :
        {
        "message": "Course soft deleted successfully."
    }
            """

class ReadingMaterialView(APIView):
    def put(self, request, course_id, format=None):
        try:
            reading_material_id = request.data.get('reading_material_id')
            
            if reading_material_id is None:
                return Response({"error": "reading_material_id is required in the request body."},
                                status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Get the reading material instance
                reading_material = get_object_or_404(UploadReadingMaterial, pk=reading_material_id)
                
                # Check if the associated course is active
                if reading_material.courses.filter(pk=course_id, active=True).exists():
                    return Response({"error": "Cannot edit reading material. Course is active."},
                                    status=status.HTTP_403_FORBIDDEN)

                # Validate request data
                serializer = UploadReadingMaterialSerializer(instance=reading_material, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save(updated_at=timezone.now())

                return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            if isinstance(e, (UploadReadingMaterial.DoesNotExist, ValidationError)):
                error_message = "Reading material not found." if isinstance(e, UploadReadingMaterial.DoesNotExist) else str(e)
                status_code = status.HTTP_404_NOT_FOUND
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            return Response({"error": error_message}, status=status_code)
    
    def patch(self, request, course_id, format=None):
        try:
            reading_material_id = request.data.get('reading_material_id')
            
            if reading_material_id is None:
                return Response({"error": "reading_material_id is required in the request body."},
                                status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch the reading material instance
            reading_material = get_object_or_404(UploadReadingMaterial, pk=reading_material_id)
            
            # Validate request data
            serializer = DeleteReadingMaterialSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            with transaction.atomic():
                # Check if the reading material is associated with other courses
                other_courses_count = reading_material.courses.exclude(id=course_id).count()
                if other_courses_count > 0:
                    # Only remove the relation with the current course
                    reading_material.courses.remove(course_id)
                else:
                    # No other courses are associated, soft delete the reading material
                    reading_material.deleted_at = timezone.now()
                    reading_material.active = False
                    reading_material.save()
                
                return Response({"message": "Reading material deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            error_message = str(e)
            if isinstance(e, (UploadReadingMaterial.DoesNotExist, ValidationError)):
                error_message = "Reading material not found." if isinstance(e, UploadReadingMaterial.DoesNotExist) else str(e)
                status_code = status.HTTP_404_NOT_FOUND
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            return Response({"error": error_message}, status=status_code)

    """ 
    AFTER TESTING API:
    PATCH :  REQUEST BODY
    {
    "course_id": 3,
    "reading_material_id": 3
    }
    RESPONSE BODY:
    {
    "message": "Reading material deleted successfully."
    }
    """
    
class QuizModifyView(APIView):
    
    def put(self, request, course_id, format=None):
        try:
            # Check if course exists
            course = Course.objects.get(pk=course_id)
            if course.active:
                return Response({"error": "Editing is not allowed for active courses."},
                                status=status.HTTP_403_FORBIDDEN)

            # Check if quiz exists
            quiz_id = request.data.get('quiz_id', None)
            if not quiz_id:
                return Response({"error": "Quiz ID is required in the request body."}, status=status.HTTP_400_BAD_REQUEST)
            quiz = Quiz.objects.get(pk=quiz_id)
            if course not in quiz.courses.all():
                return Response({"error": "Quiz not found for the specified course."},
                                status=status.HTTP_404_NOT_FOUND)

            # Update quiz instance
            serializer = EditQuizInstanceSerializer(quiz, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist as e:
            error_message = "Resource not found" if isinstance(e, ObjectDoesNotExist) else str(e)
            status_code = status.HTTP_404_NOT_FOUND if isinstance(e, ObjectDoesNotExist) else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({"error": error_message}, status=status_code)
    
    def patch(self, request, course_id, format=None):
        try:
            quiz_id = request.data.get('quiz_id', None)
            if not quiz_id:
                return Response({"error": "Quiz ID is required in the request body."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate request data
            serializer = DeleteSelectedQuizSerializer(data={'quiz_id': quiz_id})
            serializer.is_valid(raise_exception=True)
            
            # Fetch the quiz instance
            quiz = Quiz.objects.get(id=quiz_id)
            
            # Check if the quiz is associated with other courses
            other_courses_count = quiz.courses.exclude(id=course_id).count()
            if other_courses_count > 0:
                # Only remove the relation with the current course
                quiz.courses.remove(course_id)
            else:
                # No other courses are associated, soft delete the quiz
                quiz.deleted_at = timezone.now()
                quiz.active = False
                quiz.save()
                
            return Response({"message": "Quiz deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except ObjectDoesNotExist as e:
            error_message = "Quiz not found" if isinstance(e, ObjectDoesNotExist) else "Internal Server Error"
            status_code = status.HTTP_404_NOT_FOUND if isinstance(e, ObjectDoesNotExist) else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({"error": error_message}, status=status_code)

        
class QuestionModifyView(APIView):
    def put(self, request, quiz_id, format=None):  
        error_response = None
        try:
            # Extract question_id from request body
            question_id = request.data.get('question_id')
            if not question_id:
                raise ValidationError("Question ID is required in the request body.")

            # Extract course_id from request body
            course_id = request.data.get('course_id')
            if not course_id:
                raise ValidationError("Course ID is required in the request body.")

            # Check if quiz exists
            quiz = Quiz.objects.get(pk=quiz_id)

            # Check if question exists
            question = Question.objects.get(pk=question_id)
            if quiz not in question.quizzes.all():
                raise ValidationError("Question not found for the specified quiz.")

            # Check if course exists
            course = Course.objects.get(pk=course_id)
            if course.active:
                error_response = {"error": "Editing is not allowed for active courses."}
            elif course not in quiz.courses.all():
                error_response = {"error": "Quiz not found for the specified course."}
            else:
                # Update question instance
                serializer = EditQuestionInstanceSerializer(question, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

        except ValidationError as e:
            error_response = {"error": str(e)}
        
        if error_response:
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        # Handle other unexpected errors
        return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def patch(self, request, quiz_id, format=None):
        error_response = None
        try:
            # Extract question_id from request body
            question_id = request.data.get('question_id')
            if not question_id:
                return Response({"error": "Question ID is required in the request body."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Fetch the question instance
            question = Question.objects.get(id=question_id)

            # Check if the question is associated with the specified quiz
            if quiz_id not in question.quizzes.values_list('id', flat=True):
                error_response = {"error": "Question not found for the specified quiz."}
            else:
                # Check if the question is associated with other quizzes
                other_quizzes_count = question.quizzes.exclude(id=quiz_id).count()
                if other_quizzes_count > 0:
                    # Only remove the relation with the current quiz
                    question.quizzes.remove(quiz_id)
                else:
                    # No other quizzes are associated, soft delete the question
                    question.deleted_at = timezone.now()
                    question.active = False
                    question.save()

                return Response({"message": "Question deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except Question.DoesNotExist:
            error_response = {"error": "Question not found."}

        if error_response:
            return Response(error_response, status=status.HTTP_404_NOT_FOUND)

        # Handle other unexpected errors
        return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

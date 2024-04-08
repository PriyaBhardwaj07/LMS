from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from rest_framework import status
from django.contrib import messages
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics

from exam.models.allmodels import (
    Course,
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
from exam.serializers.deletecourseserializers import DeleteQuestionSerializer, DeleteReadingMaterialSerializer, DeleteSelectedCourseSerializer, DeleteSelectedQuizSerializer, DeleteVideoMaterialSerializer
import pandas as pd # type: ignore

class DeleteSelectedCourseView(APIView):
    """
        view to used for deleting a course instance
        triggers with POST/delete request.
        should be allowed for only [super admin].

        table : Course
        
        url : course_id

        for course.active == True -> not allowed (first convert it into inactive course)
        for course.active == False -> 
                delete instance of course whose id in url from course table
                delete instances related to it from courseregistrationrecords, coursestructure, courseenrollment, quizattempthistory - via foreign key relation (CASCADE delete)
                delete mapped instances of course_id in url with reading material , video material, quiz with whom it is in manytomany relation.
                        reading material , video material, quiz are in relation with this course only , then delete them from their tables too, similarly for questions in aspect of the quiz delete, and choicees will be deleted by cascade delete.
                
    """
    def post(self, request, course_id, format=None):
        try:
            # Fetch the course instance
            course = get_object_or_404(Course, id=course_id)

            # Check if the course is active
            if course.active:
                return Response({"error": "Course must be inactive before deletion."}, status=status.HTTP_400_BAD_REQUEST)

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
    REQUEST BODY:
    In url : http://127.0.0.1:8000/lms/delete-course/1/
    RESPONSE:
    {
    "message": "Course soft deleted successfully."
     }
    """
                              
class DeleteSelectedReadingMaterialView(APIView):
    """
        view to used for deleting a course instance
        triggers with POST/delete request.
        should be allowed for only [super admin].

        table : UploadReadingMaterial
        
        url : course_id, reading_material_id

        for course.active == True -> not allowed (first convert it into inactive course)
        for course.active == False -> 
                check if readingmaterial whose id is in url is in relation with courses other than this :
                        if yes -> then only delete the relation between the course and that material.
                        if no -> then delete the instance of reading material whose id is in url
    """
    def post(self, request, course_id, reading_material_id, format=None):
        try:
            # Fetch the reading material instance
            reading_material = UploadReadingMaterial.objects.get(id=reading_material_id)

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

        except UploadReadingMaterial.DoesNotExist:
            return Response({"error": "Reading material not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """ 
    REQUEST BODY:
    http://127.0.0.1:8000/lms/course/1/reading-material/2/delete/
    RESPONSE BODY:
    {
    "message": "Reading material deleted successfully."
}  
    
    """

# SARTHAK WILL DO 
class DeleteSelectedVideoMaterialView(APIView):
    """
        view to used for deleting a course instance
        triggers with POST/delete request.
        should be allowed for only [super admin].

        table : UploadVideo
        
        url : course_id, video_material_id

        for course.active == True -> not allowed (first convert it into inactive course)
        for course.active == False -> 
                check if video_material whose id is in url is in relation with courses other than this :
                        if yes -> then only delete the relation between the course and that material.
                        if no -> then delete the instance of video_material whose id is in url
    """
    def post(self, request, course_id, video_material_id, format=None):
        try:
            # Validate request data
            serializer = DeleteVideoMaterialSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Fetch the video material instance
            video_material = UploadVideo.objects.get(id=video_material_id)
            
            # Check if the video material is associated with other courses
            other_courses_count = video_material.courses.exclude(id=course_id).count()
            if other_courses_count > 0:
                # Only remove the relation with the current course
                video_material.courses.remove(course_id)
            else:
                # No other courses are associated, soft delete the video material
                video_material.deleted_at = timezone.now()
                video_material.active = False
                video_material.save()
                
            return Response({"message": "Video material deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        
        except UploadVideo.DoesNotExist:
            return Response({"error": "Video material not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteSelectedQuizView(APIView):
    """
        view to used for deleting a course instance
        triggers with POST/delete request.
        should be allowed for only [super admin].

        table : Quiz
        
        url : course_id, quiz_id

        for course.active == True -> not allowed (first convert it into inactive course)
        for course.active == False -> 
                check if Quiz whose id is in url is in relation with courses other than this :
                        if yes -> then only delete the relation between the course and that Quiz.
                        if no -> then delete the instance of Quiz whose id is in url
    """
    def post(self, request, course_id, quiz_id, format=None):
        try:
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
                quiz.save()  # Save the changes
                
            return Response({"message": "Quiz deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    """
    URL  
    
    RESPONSE BODY:
    {
    "message": "Quiz deleted successfully."
}
    
    """

class DeleteSelectedQuestionView(APIView):
    """
        view to used for deleting a course instance
        triggers with POST/delete request.
        should be allowed for only [super admin].

        table : Question
        
        url : course_id, quiz_id , question_id

        for course.active == True -> not allowed (first convert it into inactive course)
        for course.active == False -> 
                check if Question whose id is in url is in relation with quizzes other than this :
                        if yes -> then only delete the relation between that question and  Quiz.
                        if no -> then delete the instance of Question whose id is in url
    """
    def post(self, request, course_id, quiz_id, question_id, format=None):
        try:
            # Fetch the question instance
            question = Question.objects.get(id=question_id)
            
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
            return Response({"error": "Question not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """
    REQUEST BODY :
    URL
    
    RESPONSE BODY:
    {
    "message": "Question deleted successfully."
}
    """

# ============================================================
class DeleteSelectedChoiceView(APIView):
    """
        view to used for deleting a course instance
        triggers with POST/delete request.
        should be allowed for only [super admin].

        table : Choice
        
        url : course_id, question_id , choice_id

        for course.active == True -> not allowed (first convert it into inactive course)
        for course.active == False -> 
                delete the selected choice instance from choice table
    """
    pass

# should allow multiple coursestructure instances to be deleted
class DeleteCourseStructureInstanceView(APIView):
    pass

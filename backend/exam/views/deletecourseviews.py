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

from exam import serializers
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
from exam.serializers.deletecourseserializers import DeleteQuestionSerializer, DeleteReadingMaterialSerializer, DeleteSelectedCourseSerializer, DeleteSelectedQuizSerializer, DeleteVideoMaterialSerializer
import pandas as pd # type: ignore

class DeleteSelectedCourseView(APIView):
    """
    View used for deleting a course instance.
    Triggers with POST/delete request.
    Should be allowed for only [super admin].

    Table: Course
        
    Request Body: {"course_id": id}

    For course.active == True -> not allowed (first convert it into inactive course)
    For course.active == False -> 
        delete instance of course whose id in request body from course table
        delete instances related to it from courseregistrationrecords, coursestructure, courseenrollment, quizattempthistory - via foreign key relation (CASCADE delete)
        delete mapped instances of course_id in request body with reading material, video material, quiz with whom it is in manytomany relation.
        Reading material, video material, quiz are in relation with this course only, then delete them from their tables too, similarly for questions in aspect of the quiz delete, and choices will be deleted by cascade delete.
    """
    def post(self, request, format=None):
        serializer = DeleteSelectedCourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course_id = serializer.validated_data['course_id']

        try:
            # Fetch the course instance
            course = Course.objects.get(id=course_id)

            # Check if the course is active
            if course.active:
                raise serializers.ValidationError("Course must be inactive before deletion.")

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
    {
    "course_id": 3
}
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
            # Validate request data
            serializer = DeleteReadingMaterialSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
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
    {
    "reading_material_id": 1
    }
    RESPONSE BODY:
    {
    "message": "Reading material deleted successfully."
}  
    
    """


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
            # Validate request data
            serializer = DeleteSelectedQuizSerializer(data=request.data)
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
        
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    """
    REQUEST BODY:{
    "quiz_id": 1
}
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
            # Validate request data
            serializer = DeleteQuestionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
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
    {
    "question_id": 1
}
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
    pass

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

class EditCourseInstanceDetailsView(APIView):
    """
        view to used for editing a course instance.
        POST request
        should be allowed for only [super admin].

        table : Course
        
        url : course_id
        
        in request body:
                    title , summary 
        first check if course.deleted_at != null: if it is null, not allowed to go further
            request.title and request.summary != null [means they should not be empty]
            if they are empty -> not allowed
            else :
                    course.title = request.title
                    course.summary = request.summary
                    course.updated_at = timezone.now()
        if course.active == False :
                don't do anything extra
        if course.active == True :
                make a instance in notification table, with latest message from activitylog table and course  in url
    """
    def post(self, request, course_id, format=None):
        try:
            course = Course.objects.get(pk=course_id)
            if not course :
                return Response({"error": "No course found on provided course ID."}, status=status.HTTP_404_NOT_FOUND)
            if course.deleted_at:
                return Response({"error": "Course instance has been deleted"}, status=status.HTTP_400_BAD_REQUEST)
            serializer = EditCourseInstanceSerializer(data=request.data)
            if serializer.is_valid():
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
                        "message" : notification.message,
                        "created_at" : notification.created_at
                    }
                    return Response({"message": "Course instance updated successfully", "notification":notification_data}, status=status.HTTP_200_OK)
                return Response({"message": "Course instance updated successfully"}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as ve:
            return Response({"error": "Validation Error: " + str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Course.DoesNotExist:
            return Response({"error": "Course instance not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    """
    TESTING RESULT:
    REQUEST BODY:{
    "title": "Java",
    "summary":"it's a fun subject"
}
    RESPONSE BODY:
    {
    "message": "Course instance updated successfully"
}
    
    """    
        
# TODO this one        
class NotificationBasedOnCourseDisplayView(APIView):
    """
        view to get and display the notification instances filtered for each course
        triggered by GET request
        
        table : Notification
        
        url : course_id
        
        if courseenrollment.created_at for user in request for course in url is older than notification instance created_at for that course is true:
        display all of the instances of notification filtered for course
        instance data to display :
                message
                created_at
        else : 
            return no instance , just message - no notification yet.
    """
# TODO : THE FUNCTIONALITY TO ENABLE THE VIEW OF NOTIFICATIONS, IF NOTIFICATION FOR THAT COURSES ARE NEWER THE ENROLLMENT DATE OF COURSE ENROLLMENT, THEN REFLECT IN NOTIFICATION FOLDER OF USER
    def get(self, request, course_id, format=None):
        try:
            # Get the course enrollment date for the current user
            course_enrollment = CourseEnrollment.objects.get(user=request.user, course_id=course_id)
            enrollment_date = course_enrollment.created_at

            # Get notifications for the specified course
            notifications = Notification.objects.filter(course_id=course_id)

            # Check if there are any notifications for the given course
            if notifications.exists():
                # Filter notifications based on creation date
                new_notifications = notifications.filter(created_at__gt=enrollment_date)
                if new_notifications.exists():
                    serializer = NotificationSerializer(new_notifications, many=True)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "No new notifications for this course yet."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No notifications for this course yet."}, status=status.HTTP_200_OK)
        except CourseEnrollment.DoesNotExist:
            return Response({"error": "User is not enrolled in this course."}, status=status.HTTP_404_NOT_FOUND)
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EditReadingMaterialInstanceView(APIView):
    """
        view to used for editing a reading_material instance.
        POST request
        should be allowed for only [super admin].

        table : Course
        
        url : course_id, reading_material_id
        
        table : Course, UploadReadingMaterial, CourseStructure
        
        if course.active == True -> not allowed
        if course.active == False :
                        if course.original_course is null :
                            while editing instance of reading_material:
                                title = request.title (only if request.title != null)
                                reading_content = request.reading_content (only if request.reading_content != null)
                                updated_at = timezone.now()
            and instance is saved again and editing
                    if course.original_course is not null :
                        while editing instance :
                                if reading_material in url is related with courses other than that in url :
                                    create new instance of reading_material using data of instance of reading_material in url for course for in url
                                        while creating instance :
                                                    title = request body
                                                    courses = id in url
                                                    reading_content = request body
                                                    uploaded_at = updated_at = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)                                            
                                            and instance is saved 
                                            and in CourseStructure table, do editing , for content id as reading_material id , and content_type as reading for course in url change the reading_material id to id of new reading_material's instance's id.
                                if reading_material in url is only in relation with course in url :
                                    while editing instance of reading_material:
                                        title = request.title (only if request.title != null)
                                        reading_content = request.reading_content (only if request.reading_content != null)
                                        updated_at = timezone.now()
                    and instance is saved again and editing
    """
    def post(self, request, course_id, reading_material_id, format=None):
        try:
            # Get the reading material instance
            reading_material = UploadReadingMaterial.objects.get(pk=reading_material_id)

            # Check if the associated course is active
            if reading_material.courses.filter(pk=course_id, active=True).exists():
                return Response({"error": "Cannot edit reading material. Course is active."},
                                status=status.HTTP_403_FORBIDDEN)

            # Check if title and reading_content are provided in the request
            title = request.data.get('title')
            reading_content = request.data.get('reading_content')
            if title is None and reading_content is None:
                return Response({"error": "At least one of title or reading_content is required."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Update the reading material instance
            if title is not None:
                reading_material.title = title
            if reading_content is not None:
                reading_material.reading_content = reading_content
            reading_material.updated_at = timezone.now()
            reading_material.save()

            serializer = UploadReadingMaterialSerializer(reading_material)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UploadReadingMaterial.DoesNotExist:
            return Response({"error": "Reading material not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        """
        RESULT:
        REQUEST BODY:
        {
    "title": "introduction",
    "reading_content": "Reading material is updated"
    }
        RESPONSE BODY:
        {
    "id": 1,
    "title": "introduction",
    "reading_content": "Reading material is updated",
    "uploaded_at": "2024-04-06T08:31:56.360377Z",
    "updated_at": "2024-04-06T08:48:36.770432Z",
    "deleted_at": null,
    "active": true,
    "courses": [
        1
    ]
}
        """

# error in this check             
class EditVideoMaterialInstanceView(APIView):
    """
        view to used for editing a reading_material instance.
        POST request
        should be allowed for only [super admin].

        table : Course
        
        url : course_id, video_id
        
        table : Course, UploadVideo, CourseStructure
        
        if course.active == True -> not allowed
        if course.active == False :
                        if course.original_course is null :
                            while editing instance of video:
                                title = request.title (only if request.title != null)
                                video = request.video (only if request.video != null)
                                summary = request.summary
                                updated_at = timezone.now()
            and instance is saved again and editing
                    if course.original_course is not null :
                        while editing instance :
                                if video in url is related with courses other than that in url :
                                    create new instance of video using data of instance of video in url for course for in url
                                        while creating instance :
                                            title = request body
                                            slug = auto generated by pre_save
                                            courses = id in url
                                            video = request body
                                            summary = request body
                                            uploaded_at = auto now                                            
                                        and instance is saved 
                                            and in CourseStructure table, do editing , for content id as video id , and content_type as video for course in url change the video id to id of new video's instance's id.
                                if video in url is only in relation with course in url :
                                    while editing instance of video:
                                        title = request.title (only if request.title != null)
                                        video = request.video (only if request.video != null)
                                        summary = request.summary
                                        updated_at = timezone.now()
                    and instance is saved again and editing
    """
    def post(self, request, course_id, video_id, format=None):
        try:
            # Check if course exists and is not active
            course = Course.objects.get(pk=course_id)
            if course.active:
                return Response({"error": "Editing is not allowed for active courses."},
                                status=status.HTTP_403_FORBIDDEN)
        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Check if video exists
            video = UploadVideo.objects.get(pk=video_id)
        except UploadVideo.DoesNotExist:
            return Response({"error": "Video not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the video is related to the course in the URL
        if video.course_id != course_id:
            # Create a new instance of video
            serializer = EditVideoMaterialSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(courses=[course_id])
                # Update CourseStructure entry with the new video id
                CourseStructure.objects.filter(course=course_id, content_type='video', content_id=video_id)\
                    .update(content_id=serializer.data['id'])
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Edit the existing video instance
            serializer = EditVideoMaterialSerializer(video, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    

class EditQuizInstanceView(APIView):
    """
        view to used for editing a quiz instance.
        POST request
        should be allowed for only [super admin].

        table : Course
        
        url : course_id, quiz_id
        
        table : Course, Quiz, CourseStructure
        
        if course.active == True -> not allowed
        if course.active == False :
                        if course.original_course is null :
                            while editing instance of quiz:
                                title = request.title (only if request.title != null)
                                description = request body
                                answers_at_end = request body
                                exam_paper = t/f from request body
                                pass_mark = request body
                                updated_at = timezone.now()
            and instance is saved again and editing
                    if course.original_course is not null :
                        while editing instance :
                                if quiz in url is related with courses other than that in url :
                                        return response message -- editing not allowed without manual confirmation[handle with dialogue box and ask for confirmation]
                                if quiz in url is only in relation with course in url :
                                    while editing instance of quiz:
                                        title = request.title (only if request.title != null)
                                        description = request body
                                        answers_at_end = request body
                                        exam_paper = t/f from request body
                                        pass_mark = request body
                                        updated_at = timezone.now()
                    and instance is saved again and editing
    """
    def post(self, request, course_id, quiz_id, format=None):
        try:
            # Check if course exists
            course = Course.objects.get(pk=course_id)
            if course.active:
                return Response({"error": "Editing is not allowed for active courses."},
                                status=status.HTTP_403_FORBIDDEN)

            # Check if quiz exists
            quiz = Quiz.objects.get(pk=quiz_id)
            if quiz not in course.quizzes.all():
                return Response({"error": "Quiz not found for the specified course."},
                                status=status.HTTP_404_NOT_FOUND)

            # Update quiz instance
            serializer = EditQuizInstanceSerializer(quiz, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    """
    RESULT:
    REQUEST BODY:{
    "title": "updated Title",
    "description": "Your Quiz Description",
    "answers_at_end": true,
    "exam_paper": false,
    "pass_mark": 50
}
    RESPONSE BODY:{
    "title": "updated Title",
    "description": "Your Quiz Description",
    "answers_at_end": true,
    "exam_paper": false,
    "pass_mark": 50
}
    
    """    

# error 
class EditingQuizInstanceOnConfirmation(APIView):
    """
        view for post
        url : quiz_id, course_id
            ask if the changes should be allowed in quiz to be reflected in all other courses to which are related ?
        if in request confirmation = true :
                                while editing instance of quiz:
                                title = request.title (only if request.title != null)
                                description = request body
                                answers_at_end = request body
                                exam_paper = t/f from request body
                                pass_mark = request body
                                updated_at = timezone.now()
            and instance is saved again and editing
        if in request confirmation = false :
                    while creating instance :
                    courses = id in url
                    title = request body
                    slug = auto generated by pre_save
                    description = request body
                    answers_at_end = request body
                    exam_paper = t/f from request body
                    pass_mark = request body
                    created_at = updated_at = models.DateField(auto_now=True)
                    active = False by default
            and instance is saved
            and in CourseStructure table, 
                    do editing , for content id as quiz id , and content_type as quiz for course in url change the quiz id to id of new quiz's instance's id.
    """
    def post(self, request, course_id, quiz_id, format=None):
        try:
            serializer = EditingQuizInstanceOnConfirmationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            confirmation = serializer.validated_data['confirmation']
            quiz = Quiz.objects.get(pk=quiz_id)
            course = quiz.courses.first()  # Assuming each quiz is related to only one course
            
            if confirmation:
                # Editing existing quiz instance
                if course.active:
                    return Response({"error": "Editing is not allowed for active courses."},
                                    status=status.HTTP_403_FORBIDDEN)

                quiz.title = serializer.validated_data.get('title', quiz.title)
                quiz.description = serializer.validated_data.get('description', quiz.description)
                quiz.answers_at_end = serializer.validated_data.get('answers_at_end', quiz.answers_at_end)
                quiz.exam_paper = serializer.validated_data.get('exam_paper', quiz.exam_paper)
                quiz.pass_mark = serializer.validated_data.get('pass_mark', quiz.pass_mark)
                quiz.updated_at = timezone.now()
                quiz.save()

                return Response({"message": "Quiz instance updated successfully."}, status=status.HTTP_200_OK)
            else:
                # Creating new quiz instance
                new_quiz = Quiz.objects.create(
                    title=serializer.validated_data.get('title'),
                    description=serializer.validated_data.get('description'),
                    answers_at_end=serializer.validated_data.get('answers_at_end'),
                    exam_paper=serializer.validated_data.get('exam_paper'),
                    pass_mark=serializer.validated_data.get('pass_mark'),
                )

                # Update CourseStructure entry with the new quiz id
                CourseStructure.objects.filter(course=course_id, content_type='quiz', content_id=quiz_id) \
                    .update(content_id=new_quiz.id)

                return Response({"message": "New quiz instance created successfully."}, status=status.HTTP_201_CREATED)
        
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EditQuestionInstanceView(APIView):
    """
        view to used for editing a question instance.
        POST request
        should be allowed for only [super admin].

        table : Course
        
        url : course_id, quiz_id, question_id
        
        table : Course, Quiz, CourseStructure, Question
        
        if course.active == True -> not allowed
        if course.active == False :
                        if course.original_course is null :
                            while editing instance of question:
                                figure = request body
                                content = request body (only if request.content != null)
                                explanation = request body
                                choice_order = request body
                                updated_at = timezone.now()
            and instance is saved again and editing
                    if course.original_course is not null :
                        while editing instance :
                                if question in url is related with quiz other than that in url :
                                        return response message -- editing not allowed without manual confirmation[handle with dialogue box and ask for confirmation]
                                if question in url is only in relation with quiz in url :
                                    while editing instance of question:
                                        figure = request body
                                        content = request body (only if request.content != null)
                                        explanation = request body
                                        choice_order = request body
                                        updated_at = timezone.now()
                    and instance is saved again and editing
    """
    def post(self, request, course_id, quiz_id, question_id, format=None):
        try:
            # Check if course exists
            course = Course.objects.get(pk=course_id)
            if course.active:
                return Response({"error": "Editing is not allowed for active courses."},
                                status=status.HTTP_403_FORBIDDEN)

            # Check if quiz exists
            quiz = Quiz.objects.get(pk=quiz_id)
            if course not in quiz.courses.all():
                return Response({"error": "Quiz not found for the specified course."},
                                status=status.HTTP_404_NOT_FOUND)

            # Check if question exists
            question = Question.objects.get(pk=question_id)
            if quiz not in question.quizzes.all():
                return Response({"error": "Question not found for the specified quiz."},
                                status=status.HTTP_404_NOT_FOUND)

            # Update question instance
            serializer = EditQuestionInstanceSerializer(question, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Course.DoesNotExist:
            return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
        except Question.DoesNotExist:
            return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    """
    REQUEST BODY:
    {
    "content": "what is dfa",
    "explanation": "true or false"
}
   RESPONSE BODY:
   {
    "figure": null,
    "content": "what is dfa",
    "explanation": "true or false",
    "choice_order": "random"
}     
    """
        
class EditingQuestionInstanceOnConfirmation(APIView):
    """
        view for post
        url : quiz_id, course_id
            ask if the changes should be allowed in quiz to be reflected in all other quizzes to which are related ?
        if in request confirmation = true :
                while editing instance of question:
                                        figure = request body
                                        content = request body (only if request.content != null)
                                        explanation = request body
                                        choice_order = request body
                                        updated_at = timezone.now()
            and instance is saved again and editing
        if in request confirmation = false :
                while creating instance of question -> do not allow to update the question then , 
                                                        and suggest to make new one, after deleting this from this quiz.
    """
    def post(self, request, course_id, quiz_id, format=None):
        try:
            serializer = EditingQuestionInstanceOnConfirmationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            confirmation = serializer.validated_data['confirmation']
            quiz = Quiz.objects.get(pk=quiz_id)
            questions = quiz.questions.all()
            
            if confirmation:
                # Editing existing question instances
                for question in questions:
                    question.figure = serializer.validated_data.get('figure', question.figure)
                    if 'content' in serializer.validated_data and serializer.validated_data['content'] is not None:
                        question.content = serializer.validated_data['content']
                    question.explanation = serializer.validated_data.get('explanation', question.explanation)
                    question.choice_order = serializer.validated_data.get('choice_order', question.choice_order)
                    question.updated_at = timezone.now()
                    question.save()
                
                return Response({"message": "Question instances updated successfully."}, status=status.HTTP_200_OK)
            else:
                # Do not allow updating, suggest creating a new question
                return Response({"message": "You chose not to update existing questions. Please create new ones instead."},
                                status=status.HTTP_400_BAD_REQUEST)
        
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    """
        REQUEST BODY:
        {
    "confirmation": true,
    "content": "Your updated question content",
    "explanation": "Your updated explanation",
    "choice_order": "random"
}
RESPONSE:
{
    "message": "Question instances updated successfully."
}
        
    """

# need to decide whether to keep it or not
class EditCourseStructureView(APIView):
    pass



#MULTIPLE EXCEPT REMOVE 
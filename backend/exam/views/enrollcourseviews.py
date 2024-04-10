from datetime import timezone
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from django.contrib import messages
from django.db import transaction
from django.db import DatabaseError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from exam.models.allmodels import (
    Course,
    CourseRegisterRecord,
    CourseEnrollment,
    Progress,
    Quiz,
    Question,
    QuizAttemptHistory
)
from django.views.generic import (
    DetailView,
    ListView,
    TemplateView,
    FormView,
    CreateView,
    FormView,
    UpdateView,
)
from exam.forms import (
    QuestionForm,
)
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.decorators import method_decorator

from exam.serializers.enrollcourseserializers import (
    AssignCourseEnrollmentSerializer, 
    CourseEnrollmentSerializer,
    DisplayCourseEnrollmentSerializer,
    EnrolledCoursesSerializer,
    EnrollmentDeleteSerializer, 
    RegisteredCourseSerializer, 
    UnAssignCourseEnrollmentSerializer, 
    UserSerializer
)
from exam.models.coremodels import *

# for enrollment feature
# will be displayed to employer/client-admin only

class RegisteredCourseListView(APIView):
    """
        view to display courses that are registered for that customer, whose's id is owned by user in request.
        trigger with GET request
        should be allowed for only [client-admin / Employer].
       
        table : CourseRegisterRecord, Courses
       
        what will be displayed:
                    id
                    title
                    updated_at # to see how old is this course
                    original_course [title to be extracted on frontend]
                    version_number
    """
    '''
    how will we do it ?
            first extract user from request and then extract it's customer id
            filter CourseRegisterRecord with that customer id     TODO :[and active to be True]
            make list of courses that are filtered
            get the instances of Courses whose id is in list.
    '''
    def get(self, request, format=None):
        try:
            # ===========================================
            # Extract customer ID from request headers
            user_header = request.headers.get("user")
            if user_header:
                user_data = json.loads(user_header)
                customer_id = user_data.get("customer")
            else:
                return Response({"error": "Customer ID not found in headers."}, status=status.HTTP_400_BAD_REQUEST)
            # ===========================================


            # Filter CourseRegisterRecord with customer ID and active status
            course_register_records = CourseRegisterRecord.objects.filter(customer=customer_id, active=True)

            # Check if courses exist
            if not course_register_records:
                return Response({"message": "No customer-course register record found.", "data": []}, status=status.HTTP_404_NOT_FOUND)

            # Get the list of course IDs
            course_ids = [record.course.id for record in course_register_records]
            if not course_ids:
                return Response({"error": "No courses found for the given customer ID."}, status=status.HTTP_404_NOT_FOUND)

            # Get instances of Course whose IDs are in the list
            courses = Course.objects.filter(id__in=course_ids)

            # Serialize the courses data
            serializer = RegisteredCourseSerializer(courses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (ValidationError, ObjectDoesNotExist) as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        """
        RESULT AFTER TESTING API
        IN HEADER: 
        Key: user
        Value: {"id ":1 ,"first_name":"Hanks","last_name":"Doe","customer":1}
        
        RESPONSE:
        [
    {
        "id": 1,
        "title": "Java",
        "updated_at": "2024-03-24",
        "version_number": 1
    }
]
        """
          
class UserListForEnrollmentView(APIView):
    """
    
    view to display data about list of user which have customer id same as that of user in request.
    trigger with GET request
    should be allowed for only [Employer].
    
    table : User
    what will be displayed:
                    id, first_name, last_name, status
                    
    """
    '''
        what will happen:
                    user will be extracted from request
                    user's customer_id will be retrieved then
                    CourseRegisterRecord will be filtered on the basis of this customer_id
                    and list of course_ids will be made
                    list of course_ids will be used to retrieve the list of course titles associated with it from course table.
    '''
    def get(self, request, format=None):
        # ===========================================

        # Extract customer ID from the request headers
        user_header = request.headers.get("user")
        if user_header:
            user_data = json.loads(user_header)
            customer_id = user_data.get("customer")
        else:
            return Response({"error": "Customer ID not found in headers."}, status=status.HTTP_400_BAD_REQUEST)
        # ===========================================

        if not customer_id:
            return Response({"error": "Customer ID header is missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Filter users based on the provided customer ID
            users = User.objects.filter(customer__id=customer_id)
            if not users:  # If no users found, return error
                return Response({"error": "No users found for the given customer ID."}, status=status.HTTP_404_NOT_FOUND)
        except ObjectDoesNotExist:
            return Response({"error": "No users found for the given customer ID."}, status=status.HTTP_404_NOT_FOUND)
        # Serialize the user data
        try:
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as ve:
            return Response({"error": "Validation Error: " + str(ve)}, status=status.HTTP_400_BAD_REQUEST)     
    
    """
        RESULT AFTER TESTING API
        IN HEADER: 
        Key: user
        Value: {"customer":1}
        
        RESPONSE:
    [
        {
            "id": 1,
            "first_name": "Hanks",
            "last_name": "Doe",
            "status": "active"
        }
    ]
        """


class CreateCourseEnrollmentView(APIView):
    
    """
        view to create instances in CourseEnrollment.
        trigger with POST request
        should be allowed for only [Employer].
       

        table : CourseEnrollment
       
        in request body :
                        list of course_id =[..., ..., ..., ...]
                        list of user_id =[..., ..., ..., ...]
        in response body :
                        each course in list will be mapped for all users in list inside CourseEnrollment table
                        by default active will be true
    """
    
    def post(self, request, *args, **kwargs):
        course_ids = request.data.get("course_ids", [])
        user_ids = request.data.get("user_ids", [])

        if not course_ids:
            return Response({"error": "Course IDs are missing."}, status=status.HTTP_400_BAD_REQUEST)
        if not user_ids:
            return Response({"error": "User IDs are missing."}, status=status.HTTP_400_BAD_REQUEST)

        # Lists to hold created enrollments, existing records, and all records
        enrollments = []
        existing_records = []

        try:
            # Retrieve all existing records from the database
            all_existing_records = CourseEnrollment.objects.all()

            for course_id in course_ids:
                for user_id in user_ids:
                    # Check if enrollment already exists
                    if CourseEnrollment.objects.filter(course_id=course_id, user_id=user_id).exists():
                        # Return a response indicating that the enrollment already exists
                        existing_record = {
                            "course_id": course_id,
                            "user_id": user_id
                        }
                        existing_records.append(existing_record)
                        continue  # Move to the next iteration

                    # Create a new enrollment
                    enrollment = CourseEnrollment.objects.create(course_id=course_id, user_id=user_id, active=True)
                    enrollments.append(enrollment)

            # Combine new enrollments and existing records into a single list
            all_records = list(all_existing_records.values()) + enrollments + existing_records

            # Response body including all three lists
            response_data = {
                "message": "Course enrollments have been created successfully.",
                "enrollments": enrollments,
                "existing_records": existing_records,
                "all_records": all_records
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
    """
        RESULT AFTER TESTING API
        REQUEST BODY:
 {
    "course_ids": [2],
    "user_ids": [1]
}

        
    RESPONSE:
        {
    "message": "Course enrollments have been created successfully.",
    "enrollments": [],
    "existing_records": [
        {
            "course_id": 2,
            "user_id": 1
        }
    ],
    "all_records": [
        {
            "id": 1,
            "user_id": 1,
            "course_id": 2,
            "enrolled_at": "2024-04-08T06:50:13.204005Z",
            "updated_at": "2024-04-08T06:50:13.204005Z",
            "active": true,
            "deleted_at": null
        },
        {
            "course_id": 2,
            "user_id": 1
        }
    ]
}
     """    
     
class DisplayCourseEnrollmentView(APIView):
    """
        view to display all instances of CourseEnrollment Table.
        trigger with GET request
        
        table : CourseEnrollment, User , Course
        
        what will be displayed:
                    id
                    course.title,
                    user.first_name,
                    user.last_name,
                    enrolled_at,
                    active
    """
    
    def get(self, request, format=None):
        try:
            # Get all instances of CourseEnrollment
            enrollments = CourseEnrollment.objects.all()

            # Check if there are any enrollments
            if not enrollments.exists():
                return Response({"message": "No course enrollments found."}, status=status.HTTP_404_NOT_FOUND)

            # Serialize the course enrollment data
            serializer = DisplayCourseEnrollmentSerializer(enrollments, many=True)
            
            return Response(serializer.data)
        except (CourseEnrollment.DoesNotExist, DatabaseError, ValidationError) as error:
            error_message = "An error occurred: " + str(error)
            return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    """
    RESULT AFTER TESTING API
        
    RESPONSE:
[
    {
        "user": 1,
        "user_first_name": "Mary",
        "user_last_name": "James",
        "course_title": "Python",
        "active": true
    }
]
]
    """    
        
class UnAssignCourseEnrollmentView(APIView):
    """
    this API is used to unassign course to specified user(s) by turning the active false , and hide visibility of course to user(s).
    required inputs : list of ids of instance of course enrollment table
    
    Method: POST
    Parameters:
        - enrollment_ids (list of integers): IDs of course enrollment instances to unassign.
    
    It is triggered with POST request.
    
    """
    def post(self, request, *args, **kwargs):
        try:
            # Deserialize and validate the input data
            serializer = UnAssignCourseEnrollmentSerializer(data=request.data)
            if serializer.is_valid():
                enrollment_ids = serializer.validated_data.get('enrollment_ids')
                # Check if any enrollment IDs were provided
                if not enrollment_ids:
                    return Response({'error': 'No enrollment IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

                # Check if any provided enrollment IDs are not found in the database
                enrollments = CourseEnrollment.objects.filter(id__in=enrollment_ids)
                if len(enrollments) != len(enrollment_ids):
                    return Response({'error': 'One or more enrollment IDs do not exist'}, status=status.HTTP_404_NOT_FOUND)

                # Iterate through each enrollment and update its active status
                updated_enrollments = []
                for enrollment in enrollments:
                    if enrollment.active:
                        enrollment.active = False
                        enrollment.save()
                        updated_enrollments.append(enrollment.id)
                    else:
                        updated_enrollments.append({'id': enrollment.id, 'message': 'Enrollment is already inactive'})

                return Response({'message': f'Courses unassigned successfully.', 'updated_enrollments': updated_enrollments}, status=status.HTTP_200_OK)

            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    """
        RESULT AFTER TESTING API
        REQUEST BODY:
{
    "enrollment_ids": [
        "3"
                       ]
}       
        RESPONSE:
        {
    "message": "Courses unassigned successfully.",
    "updated_enrollments": [
        3
    ]
}
  
"""    

class AssignCourseEnrollmentView(APIView):
    """
    this API is used to assign course to specified user(s) for all users in courseenrollment table who have active false
    in request body : list of ids of instance of course enrollment table
    
    Method: POST
    Parameters:
        - enrollment_ids (list of integers): IDs of course enrollment instances to assign, who have active status false for now
    
    It is triggered with POST request.
    
    """
    def post(self, request, *args, **kwargs):
        serializer = AssignCourseEnrollmentSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            enrollment_ids = serializer.validated_data.get('enrollment_ids', [])

            if not enrollment_ids:
                return Response({'error': 'No enrollment IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate that all provided IDs are integers
            if not all(isinstance(enrollment_id, int) for enrollment_id in enrollment_ids):
                return Response({'error': 'All enrollment IDs must be integers'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if enrollments exist and are inactive
            enrollments_to_update = CourseEnrollment.objects.filter(id__in=enrollment_ids, active=False)

            if not enrollments_to_update.exists():
                # Check if any provided enrollment IDs are already active
                active_enrollments = CourseEnrollment.objects.filter(id__in=enrollment_ids, active=True)
                if active_enrollments.exists():
                    active_ids = [enrollment.id for enrollment in active_enrollments]
                    return Response({'warning': 'One or more enrollments are already active',
                                     'active_enrollment_ids': active_ids}, status=status.HTTP_409_CONFLICT)

                return Response({'error': 'No valid enrollments found to update'}, status=status.HTTP_404_NOT_FOUND)

            # Perform the update operation inside a transaction
            with transaction.atomic():
                updated_count = enrollments_to_update.update(active=True)

            return Response({'message': 'Course(s) assigned successfully', 'updated_count': updated_count},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """
        RESULT AFTER TESTING API
        
        REQUEST BODY:
       {
    "enrollment_ids": [
        "3"
    ]
    }
        
        RESPONSE:
{
    "message": "Course(s) assigned successfully",
    "updated_count": 1
}
    
    """  
        
class EnrolledCoursesListDisplayView(APIView):
    """  
    trigger with GET request
    table : CourseEnrollment
    should be allowed for only [Client].
    GET Request 
    this view is so that the client can see their enrolled courses
    """
    def get(self, request, format=None):
        try:
            # Retrieve user ID from request headers
            user_id = request.headers.get("user")
            if user_id is None:
                return Response({"error": "User ID not found in headers."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Retrieve enrolled courses for the user that are active
            enrolled_courses = CourseEnrollment.objects.filter(user_id=user_id, course__active=True)
            
            # Serialize the enrolled courses data
            serializer = EnrolledCoursesSerializer(enrolled_courses, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """ 
    IN HEADER: KEY:User, Value:1
    RESPONSE:
    [
    {
        "id": 3,
        "course": 4,
        "enrolled_at": "2024-04-08T06:54:45.492018Z",
        "updated_at": "2024-04-08T06:54:45.492018Z",
    }
]
    
    """

class DeleteEnrollmentView(APIView):
    """ 
    Trigger with POST request to delete a course enrollment.
    Table: CourseEnrollment
    Should be allowed for only [Client Admin].
    This view allows the client admin to delete a client from a certain course.
    url : course_id
    """

    def post(self, request, enrollment_id, format=None):
        try:
            # Check if the enrollment exists
            enrollment = CourseEnrollment.objects.get(pk=enrollment_id)
        except CourseEnrollment.DoesNotExist:
            return Response({"error": "Course enrollment not found."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Check if the enrollment is already soft-deleted
            if enrollment.deleted_at:
                return Response({"error": "Course enrollment is already deleted."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Soft delete the enrollment
            enrollment.deleted_at = timezone.now()
            enrollment.active = False
            enrollment.save()

            return Response({"message": "Course enrollment deleted successfully."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    """ 
    
    RESPONSE:
    {
    "message": "Course enrollment deleted successfully."
 }
    """
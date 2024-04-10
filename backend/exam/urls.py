from django.contrib import admin
from django.urls import path

from .views.maincourseviews import (
    CourseInstanceDetailsView,
    QuestionModifyView,
    QuizModifyView,
    ReadingMaterialView)

from .views.deletecourseviews import( 
    DeleteSelectedCourseView,
    DeleteSelectedQuestionView,
    DeleteSelectedQuizView,
    DeleteSelectedReadingMaterialView,
    DeleteSelectedVideoMaterialView
    
    
     )
from .views.editcourseviews import(
    EditCourseInstanceDetailsView,
    EditQuestionInstanceView,
    EditQuizInstanceView, 
    EditReadingMaterialInstanceView,
    EditVideoMaterialInstanceView,
    EditingQuestionInstanceOnConfirmation,
    EditingQuizInstanceOnConfirmation,
    NotificationBasedOnCourseDisplayView)
from .views.courseviews import (
    ActiveCourseListDisplayView,
    AllCourseListDisplayView,
    InActiveCourseListDisplayView,
    # RegisterCoursesOnCostumerListDisplayView,
    CourseInstanceDetailDisplayView,
    SingleCourseStructureListDisplayView,
    ReadingMaterialInstanceDisplayView,
    VideoInstanceDisplayView,
    QuizInstanceDisplayView,
    QuizTake,
    dummy_quiz_index,
    ReadingMaterialListPerCourseView,
    VideoMaterialListPerCourseView,
    QuizListPerCourseView,
    QuestionListPerQuizView
)
from .views.registercourseviews import (
    FirstVersionActiveCourseListView,
    DerivedVersionActiveCourseListView,
    LMSCustomerListView,
    CreateCourseRegisterRecordView,
    DisplayCourseRegisterRecordView,
    # DeleteCourseRegisterRecordView,
    DeleteSingleCourseRegisterRecordInstanceView,
    DeactivateCourseRegistrationRecordView,
    ActivateCourseRegistrationRecordView,
    DisplayActiveCourseRegisterRecordView,
    DisplayInActiveCourseRegisterRecordView
)
from .views.enrollcourseviews import (
    DeleteEnrollmentView,
    EnrolledCoursesListDisplayView,
    RegisteredCourseListView,
    UserListForEnrollmentView,
    CreateCourseEnrollmentView,
    DisplayCourseEnrollmentView,
    UnAssignCourseEnrollmentView,
    AssignCourseEnrollmentView
)
from .views.createcourseviews import (
    CreateCourseView,
    CreateReadingMaterialView,
    CreateVideoView,
    CreateQuizView,
    CreateCourseStructureForCourseView,
    CreateQuestionView,
    CreateChoiceView,
    ActivateCourseView,
    InActivateCourseView,
    CreateNewVersionCourseView
)
# from .views.editcourseviews import (
#     EditCourseInstanceDetailsView,
#     EditReadingMaterialView,
#     EditVideoMaterialView,
#     EditQuizDetailView,
#     EditExistingQuestionDetailsView,
#     EditQuestionChoicesView
# )

urlpatterns = [
    # path('courses/', CourseListView.as_view(), name='courses-list'),
    # path('customers/', CostumerListView.as_view(), name='customers-list'),
    # path('client-admin-courses/', ClientAdminCourseListView.as_view(), name='client-admin-courses-list'),
    # path('client-admin-employees/', ClientAdminEmployeeListView.as_view(), name='client-admin-employees-list'),
    # path('enrollments/', CourseEnrollmentDisplayView.as_view(), name='enrollments-list'),
    
    #courseview.py  views url
    path('courses/', AllCourseListDisplayView.as_view(), name='courses-list'),
    path('courses/active/', ActiveCourseListDisplayView.as_view(), name='active-courses-list'),
    path('courses/inactive/', InActiveCourseListDisplayView.as_view(), name='inactive-courses-list'),

    # path('courses/registered/', RegisterCoursesOnCostumerListDisplayView.as_view(), name='registered-courses-list'),
    # path('courses/unregistered/', UnRegisteredCoursesOnCostumerListDisplayView.as_view(), name='un-registered-courses-list'),
    # path('courses/enrolled/', EnrolledCoursesListDisplayView.as_view(), name='enrolled-courses-list'),
    path('course/<int:course_id>/', CourseInstanceDetailDisplayView.as_view(), name='course'),
    path('course-structure/<int:course_id>/', SingleCourseStructureListDisplayView.as_view(), name='course-structure'),
    path('course/<int:course_id>/reading/<int:content_id>/', ReadingMaterialInstanceDisplayView.as_view(), name='course-reading-material-instance'),
    path('course/<int:course_id>/video/<int:content_id>/', VideoInstanceDisplayView.as_view(), name='course-video-instance'),
    path('course/<int:course_id>/quiz/<int:content_id>/', QuizInstanceDisplayView.as_view(), name='course-quiz-instance'),
    path('course/<int:course_id>/readings/', ReadingMaterialListPerCourseView.as_view(), name='course-reading-material-list'),
    path('course/<int:course_id>/videos/', VideoMaterialListPerCourseView.as_view(), name='course-video-list'),
    path('course/<int:course_id>/quizzes/', QuizListPerCourseView.as_view(), name='course-quiz-list'),
    path('course/<int:course_id>/quiz/<int:quiz_id>/questions/', QuestionListPerQuizView.as_view(), name='quiz-question-list'),
    path('course/<int:course_id>/notifications/', NotificationBasedOnCourseDisplayView.as_view(), name='course_notifications'),
    path("<int:pk>/<slug:quiz_slug>/take/", QuizTake.as_view(), name="quiz_take"), #href="{% url 'quiz_take' pk=course.pk slug=quiz.slug %}
    #extra
    path('quiz/redirect/<int:course_id>/', view=dummy_quiz_index, name='quiz_index'),
    
    
    #registercourseviews.py views url
    path('courses/active/v1/', FirstVersionActiveCourseListView.as_view(), name='active-first-version-courses-list'),
    path('courses/derived-active/<int:course_id>/', DerivedVersionActiveCourseListView.as_view(), name='active-derived-version-course-list'),
    path('lms-customer/', LMSCustomerListView.as_view(), name='lms-customer-list'),
    path('create/course-register-record/', CreateCourseRegisterRecordView.as_view(), name='create-course-register-record'),
    path('display/course-register-record/', DisplayCourseRegisterRecordView.as_view(), name='course-register-record-list'),
    # path('delete/course-register-record/', DeleteCourseRegisterRecordView.as_view(), name='delete-course-register-record-list'),
    path('delete/course/<int:pk>/register-record/', DeleteSingleCourseRegisterRecordInstanceView.as_view(), name='delete-single-course-register-record'),
    path('deactivate/register-records/', DeactivateCourseRegistrationRecordView.as_view(), name='deactivate-register-records'),
    path('activate/register-records/', ActivateCourseRegistrationRecordView.as_view(), name='activate-register-records'),
    path('display/active/course-register-record/', DisplayActiveCourseRegisterRecordView.as_view(), name='active-course-register-record-list'),
    path('display/inactive/course-register-record/', DisplayInActiveCourseRegisterRecordView.as_view(), name='inactive-course-register-record-list'),

    #enrollcourseviews.py views url
    path('display/registered-course/', RegisteredCourseListView.as_view(), name='register-course-list'),
    path('display/users/', UserListForEnrollmentView.as_view(), name='users-list'),
    path('create/course-enrollments/', CreateCourseEnrollmentView.as_view(), name='create-course-enrollments-record'),
    path('display/course-enrollments/', DisplayCourseEnrollmentView.as_view(), name='course-enrollments-list'),
    path('enrollments/unassign/', UnAssignCourseEnrollmentView.as_view(), name='unassign-course-enrollment'),
    path('enrollments/assign/', AssignCourseEnrollmentView.as_view(), name='assign-course-enrollment'),
    path('display/enrolled-courses/', EnrolledCoursesListDisplayView.as_view(), name='enrolled-courses-list'),
    path('delete-enrollment/<int:enrollment_id>/', DeleteEnrollmentView.as_view(), name='delete-enrollment'),
 
    #createcourseview.py views url
    path('create/course/v1/', CreateCourseView.as_view(), name='create-course-v1'),
    path('create/course/<int:course_id>/reading-material/', CreateReadingMaterialView.as_view(), name='create-course-reading-material'),
    path('create/course/<int:course_id>/video/', CreateVideoView.as_view(), name='create-course-video'),
    path('create/course/<int:course_id>/quiz/', CreateQuizView.as_view(), name='create-course-quiz'),
    path('create/course/<int:course_id>/course-structure/', CreateCourseStructureForCourseView.as_view(), name='create-course-structure'),
    path('create/<int:course_id>/quiz/<int:quiz_id>/question/', CreateQuestionView.as_view(), name='create-quiz-question'),
    path('create/question/<int:question_id>/choices/', CreateChoiceView.as_view(), name='create-question-choice'),
    path('active/course/<int:course_id>/', ActivateCourseView.as_view(), name='activate-course'),
    path('inactive/course/<int:course_id>/', InActivateCourseView.as_view(), name='inactivate-course'),
    path('create/course/<int:course_id>/versions/', CreateNewVersionCourseView.as_view(), name='create-course-v1'),
  
    #editcourseviews.py views url
    path('course/edit/', EditCourseInstanceDetailsView.as_view(), name='edit_course_instance'),
    path('course/<int:course_id>/notifications/', NotificationBasedOnCourseDisplayView.as_view(), name='course_notifications'),
    path('course/<int:course_id>/reading-material/<int:reading_material_id>/', EditReadingMaterialInstanceView.as_view(), name='edit_reading_material_instance'),
    path('course/<int:course_id>/video/<int:video_id>/', EditVideoMaterialInstanceView.as_view(), name='edit_video_material_instance'),
    path('course/<int:course_id>/quiz/<int:quiz_id>/change/', EditQuizInstanceView.as_view(), name='edit_quiz_instance'),
    path('course/<int:course_id>/quiz/<int:quiz_id>/confirmation/', EditingQuizInstanceOnConfirmation.as_view(), name='edit_quiz_instance_with_confirmation'),  
    path('course/<int:course_id>/quiz/<int:quiz_id>/question/<int:question_id>/',EditQuestionInstanceView.as_view(),name='edit_question_instance'),
    path('quiz/<int:quiz_id>/course/<int:course_id>/confirm/', EditingQuestionInstanceOnConfirmation.as_view(), name='edit_question_instance_with_confirmation'),

    #deletecourseviews.py url
    path('delete-course/', DeleteSelectedCourseView.as_view(), name='delete_course'),
    path('course/<int:course_id>/reading-material/<int:reading_material_id>/delete/', DeleteSelectedReadingMaterialView.as_view(), name='delete_reading_material'),
    path('course/<int:course_id>/video/<int:video_material_id>/deleted/', DeleteSelectedVideoMaterialView.as_view(), name='delete_selected_video_material'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/delete/', DeleteSelectedQuizView.as_view(), name='delete_selected_quiz'),
    path('course/<int:course_id>/quiz/<int:quiz_id>/question/<int:question_id>/delete/', DeleteSelectedQuestionView.as_view(), name='delete_selected_question'),


    #urls after merge for enroll,edit,delete
    path('course/modify/', CourseInstanceDetailsView.as_view(), name='update_course_instance'),
    path('course/reading/', ReadingMaterialView.as_view(), name='reading_material'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/', QuizModifyView.as_view(), name='quiz_modify'),
    path('courses/<int:course_id>/quizzes/<int:quiz_id>/questions/<int:question_id>/', QuestionModifyView.as_view(), name='question_modify'),


    
   
]

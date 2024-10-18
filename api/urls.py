from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CenterViewSet, SectionViewSet, SubscriptionViewSet, ScheduleViewSet, RecordViewSet, SectionCategoryViewSet, FeedbackViewSet, dashboard_metrics, dashboard_notifications, recent_activities, create_syllabus_and_generate_tests, get_syllabuses_and_tests, submit_test, get_user_results 
from .views import get_syllabuses_and_tests  # Импорт представления

router = DefaultRouter()
router.register(r'centers', CenterViewSet)
router.register(r'sections', SectionViewSet)
router.register(r'categories', SectionCategoryViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'schedules', ScheduleViewSet)
router.register(r'records', RecordViewSet)
router.register(r'feedbacks', FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('attendance/', RecordViewSet.as_view({'post': 'confirm_attendance'})),
    path('attendance/cancel/', RecordViewSet.as_view({'post': 'cancel_reservation'})), 
    path('dashboard/metrics/', dashboard_metrics, name='dashboard-metrics'),
    path('dashboard/recent-activities/', recent_activities, name='recent-activities'),
    path('dashboard/notifications/', dashboard_notifications, name='dashboard-notifications'),
    path('subscriptions/unactivated/', SubscriptionViewSet.as_view({'get': 'unactivated_subscriptions'})),
    path('subscriptions/<int:pk>/activate/', SubscriptionViewSet.as_view({'post': 'activate_subscription'})),
    path('generate/', create_syllabus_and_generate_tests, name='generate_tests'),
    path('get_tests/', get_syllabuses_and_tests, name='get_tests'), 
    path('get_tests/<int:section_id>/', get_syllabuses_and_tests, name='get_tests_by_section'),  
    path('submit_test/', submit_test, name='submit_test'),
    path('get_user_results/', get_user_results, name='get_user_results'),
    path('schedules/<int:pk>/start/', ScheduleViewSet.as_view({'post': 'start'}), name='schedule-start'),
]



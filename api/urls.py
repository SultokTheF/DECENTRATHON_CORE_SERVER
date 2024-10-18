from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CenterViewSet, SectionViewSet, SubscriptionViewSet, ScheduleViewSet, RecordViewSet, SectionCategoryViewSet, FeedbackViewSet, dashboard_metrics, dashboard_notifications, recent_activities

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
]
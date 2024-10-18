from rest_framework import viewsets, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Center, Section, Subscription, Schedule, Record, SectionCategory, Feedback
from .serializers import CenterSerializer, SectionSerializer, SubscriptionSerializer, ScheduleSerializer, RecordSerializer, SectionCategorySerializer, FeedbackSerializer, UserResultsSerializer
from .pagination import StandardResultsSetPagination
from django.utils import timezone
from datetime import timedelta, datetime
from rest_framework.exceptions import ValidationError
from .tasks import notify_user_after_recording

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from .models import Syllabus, TestQuestion
from .utils import parse_pdf, generate_test_from_syllabus

from rest_framework.decorators import api_view
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from .models import Syllabus
from .utils import parse_pdf

from rest_framework.decorators import api_view
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from .models import Syllabus, TestQuestion
from .utils import parse_pdf

@api_view(['POST'])
def create_syllabus_and_generate_tests(request):
    if 'pdf' not in request.FILES or 'section_id' not in request.POST:
        return JsonResponse({"error": "No PDF file or section_id provided"}, status=400)

    try:
        pdf_file = request.FILES['pdf']
        section_id = request.POST['section_id']

        # Проверка, существует ли секция
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return JsonResponse({"error": "Section not found"}, status=404)

        # Сохраняем PDF и парсим его
        syllabus_content = parse_pdf(pdf_file)

        # Создание силлабуса
        syllabus = Syllabus.objects.create(
            title=pdf_file.name,
            content=syllabus_content,
            section=section  # Связь с секцией по её id
        )

        # Генерация тестов для силлабуса
        syllabus.generate_and_save_tests()

        return JsonResponse({"status": "success", "syllabus_id": syllabus.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['GET'])
def get_syllabuses_and_tests(request, section_id=None):
    try:
        if section_id:
            syllabuses = Syllabus.objects.filter(section__id=section_id)  # Фильтрация по секции
        else:
            syllabuses = Syllabus.objects.all()  # Все силлабусы

        syllabus_data = []

        for syllabus in syllabuses:
            questions = TestQuestion.objects.filter(syllabus=syllabus)
            question_data = [
                {
                    "question": question.question,
                    "options": question.options,
                    "correct_answer": question.correct_answer
                }
                for question in questions
            ]
            syllabus_data.append({
                "id": syllabus.id,
                "title": syllabus.title,
                "content": syllabus.content,
                "section": syllabus.section.name,  # Название секции
                "questions": question_data
            })

        return JsonResponse({"syllabuses": syllabus_data}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)




class CenterViewSet(viewsets.ModelViewSet):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    search_fields = ['name', 'location', 'description']
    filterset_fields = ['description', 'latitude', 'longitude', 'sections__id', 'users']
    ordering_fields = ['name', 'location', 'latitude', 'longitude']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        new_param = self.request.query_params.get('new', None)

        if self.request.user.is_authenticated and self.request.user.role == 'STAFF':
            queryset = queryset.filter(users=self.request.user)

        if new_param is not None:
            try:
                new_param = int(new_param)
                if new_param <= 0:
                    raise ValidationError('Параметр "new" должен быть положительным целым числом.')
                queryset = queryset.order_by('-id')[:new_param]
            except ValueError:
                raise ValidationError('Параметр "new" должен быть целым числом.')
        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response({'error': 'У вас нет прав для создания центров.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        if self.request.user.role == 'STAFF':
            center = self.get_object()
            if not center.users.filter(id=self.request.user.id).exists():
                raise ValidationError("У вас нет прав для редактирования этого центра.")
        serializer.save()

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    search_fields = ['name', 'description']
    filterset_fields = ['category', 'center']
    ordering_fields = ['name', 'category', 'description']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated and self.request.user.role == 'STAFF':
            queryset = queryset.filter(center__users=self.request.user)

        new_param = self.request.query_params.get('new', None)
        if new_param is not None:
            try:
                new_param = int(new_param)
                if new_param <= 0:
                    raise ValidationError('Параметр "new" должен быть положительным целым числом.')
                queryset = queryset.order_by('-id')[:new_param]
            except ValueError:
                raise ValidationError('Параметр "new" должен быть целым числом.')
        return queryset

    def perform_update(self, serializer):
        if self.request.user.role == 'STAFF':
            section = self.get_object()
            if not section.center.users.filter(id=self.request.user.id).exists():
                raise ValidationError("У вас нет прав для редактирования этого раздела.")
        serializer.save()


class SectionCategoryViewSet(viewsets.ModelViewSet):
    queryset = SectionCategory.objects.all()
    serializer_class = SectionCategorySerializer
    pagination_class = StandardResultsSetPagination


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type', 'is_active']
    ordering_fields = ['start_date', 'end_date']

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if self.request.user.role != 'ADMIN' and instance.user != self.request.user:
            return Response({'error': 'У вас нет прав для обновления этого абонемента.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.end_date < timezone.now():
            instance.is_active = False
            instance.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unactivated_subscriptions(self, request):
        if self.request.user.role != 'ADMIN':
            return Response({'error': 'У вас нет прав для просмотра неактивированных абонементов.'}, status=status.HTTP_403_FORBIDDEN)
        unactivated_subs = Subscription.objects.filter(is_activated_by_admin=False)
        serializer = self.get_serializer(unactivated_subs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def activate_subscription(self, request, pk=None):
        if self.request.user.role != 'ADMIN':
            return Response({'error': 'У вас нет прав для активации абонементов.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            subscription = Subscription.objects.get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({'error': 'Абонемент не существует.'}, status=status.HTTP_404_NOT_FOUND)

        subscription.is_activated_by_admin = True
        subscription.save()

        return Response({'message': 'Абонемент успешно активирован.'}, status=status.HTTP_200_OK)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['section', 'status', 'date', 'start_time', 'end_time', 'records__user__id', 'section__center']
    search_fields = ['section__name', 'section__center__name']
    ordering_fields = ['start_time', 'end_time', 'capacity', 'reserved']

    def get_queryset(self):
        if self.request.user.role == 'STAFF':
            return Schedule.objects.filter(section__center__users=self.request.user)
        elif self.request.user.role == 'ADMIN':
            return Schedule.objects.all()
        return super().get_queryset()


class RecordViewSet(viewsets.ModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'schedule', 'attended', 'subscription', 'schedule__section', 'schedule__date']
    search_fields = ['schedule__section__name', 'user__email']
    ordering_fields = ['schedule__start_time', 'attended', 'schedule__date']

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return Record.objects.all()
        return Record.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='user-records/(?P<user_id>\d+)', permission_classes=[IsAuthenticated])
    def user_records(self, request, user_id=None):
        if request.user.role not in ['ADMIN', 'STAFF']:
            return Response({'error': 'У вас нет прав для просмотра записей этого пользователя.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'ADMIN':
            records = Record.objects.filter(user=user)
        
        elif request.user.role == 'STAFF':
            records = Record.objects.filter(user=user, schedule__section__center__users=request.user)
        
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        user = request.user
        schedule_id = request.data.get('schedule')
        subscription_id = request.data.get('subscription')

        try:
            schedule = Schedule.objects.get(id=schedule_id)
        except Schedule.DoesNotExist:
            return Response({'error': 'Расписание не существует.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription = Subscription.objects.get(id=subscription_id, user=user, is_active=True)
        except Subscription.DoesNotExist:
            return Response({'error': 'У вас нет действующего абонемента.'}, status=status.HTTP_400_BAD_REQUEST)

        if not subscription.is_activated_by_admin:
            return Response({'error': 'Ваш абонемент не был активирован администратором.'}, status=status.HTTP_400_BAD_REQUEST)

        current_datetime = timezone.now()
        schedule_datetime = timezone.make_aware(datetime.combine(schedule.date, schedule.start_time))

        # Проверка: если до занятия больше 24 часов, запись не разрешена
        time_difference = schedule_datetime - current_datetime
        if time_difference > timedelta(hours=24):
            return Response({'error': 'Вы не можете записаться на это занятие, так как до его начала больше 24 часов.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на пересекающиеся записи
        overlapping_records = Record.objects.filter(
            user=user,
            subscription=subscription,
            schedule__date=schedule.date,
            schedule__start_time__range=(
                (schedule_datetime - timedelta(hours=1)).time(),
                (schedule_datetime + timedelta(hours=1)).time()
            )
        )

        if Record.objects.filter(user=user, schedule=schedule, subscription=subscription).exists():
            return Response({'error': 'Вы уже записаны на это занятие с этим абонементом.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if overlapping_records.exists():
            return Response({'error': 'Вы не можете записаться на пересекающиеся занятия с использованием одного абонемента.'}, status=status.HTTP_400_BAD_REQUEST)

        # Создание записи
        record = Record.objects.create(
            user=user,
            schedule=schedule,
            subscription=subscription
        )
        schedule.reserved += 1
        schedule.save()

        serializer = self.get_serializer(record)
        notify_user_after_recording.delay(record.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unconfirmed_records(self, request):
        section_id = request.query_params.get('section_id')
        if not section_id:
            return Response({'error': 'Требуется идентификатор раздела.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response({'error': 'Раздел не найден.'}, status=status.HTTP_404_NOT_FOUND)
        records = Record.objects.filter(user=request.user, schedule__section=section, attended=False)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm_attendance(self, request):
        record_id = request.data.get('record_id')
        if not record_id:
            return Response({'error': 'Требуется идентификатор записи.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            record = Record.objects.get(id=record_id, user=request.user)
        except Record.DoesNotExist:
            return Response({'error': 'Запись не найдена или у вас нет доступа к этой записи.'}, status=status.HTTP_404_NOT_FOUND)
        if record.attended:
            return Response({'error': 'Вы уже посетили это занятие.'}, status=status.HTTP_400_BAD_REQUEST)
        record.attended = True
        record.save()
        return Response({'message': 'Посещение успешно подтверждено.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_records(self, request):
        record_type = request.query_params.get('type', 'all')
        current_datetime = timezone.now()
        records = self.get_queryset()

        if record_type == 'past':
            records = records.filter(schedule__date__lt=current_datetime.date())
        elif record_type == 'current':
            records = records.filter(schedule__date=current_datetime.date())
        elif record_type == 'future':
            records = records.filter(schedule__date__gt=current_datetime.date())

        records = records.order_by('schedule__date', 'schedule__start_time')

        page = self.paginate_queryset(records)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel_reservation(self, request):
        record_id = request.data.get('record_id')
        
        if not record_id:
            return Response({'error': 'Требуется идентификатор записи.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            record = Record.objects.get(id=record_id, user=request.user)
        except Record.DoesNotExist:
            return Response({'error': 'Запись не найдена или у вас нет доступа к этой записи.'}, status=status.HTTP_404_NOT_FOUND)
        
        if record.is_canceled:
            return Response({'error': 'Вы уже отменили это резервирование.'}, status=status.HTTP_400_BAD_REQUEST)
        
        record.cancel_reservation()
        
        return Response({'message': 'Резервирование успешно отменено.'}, status=status.HTTP_200_OK)


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user_feedback_only = self.request.query_params.get('user_feedback_only', None)
        if user_feedback_only:
            return Feedback.objects.filter(user=self.request.user)
        return super().get_queryset()


from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from user.models import CustomUser
from api.models import Subscription
from api.models import Center
from api.models import Schedule

@api_view(['GET'])
def dashboard_metrics(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    total_users = CustomUser.objects.count()
    active_subscriptions = Subscription.objects.filter(is_active=True).count()
    total_centers = Center.objects.count()
    lessons_today = Schedule.objects.filter(date=today).count()
    lessons_this_week = Schedule.objects.filter(date__gte=start_of_week, date__lte=today + timedelta(days=6)).count()
    feedback_count = Feedback.objects.count()

    return Response({
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'total_centers': total_centers,
        'lessons_today': lessons_today,
        'lessons_this_week': lessons_this_week,
        'feedback_count': feedback_count,
    })


@api_view(['GET'])
def recent_activities(request):
    recent_signups = CustomUser.objects.order_by('-date_joined')[:5]
    recent_feedback = Feedback.objects.order_by('-created_at')[:5]
    recent_enrollments = Record.objects.order_by('-id')[:5]

    return Response({
        'recent_signups': [{
            'email': signup.email,
            'date_joined': signup.date_joined
        } for signup in recent_signups],
        'recent_feedback': [{
            'user': feedback.user.email,
            'center': feedback.center.name,
            'stars': feedback.stars,
            'text': feedback.text,
            'created_at': feedback.created_at,
        } for feedback in recent_feedback],
        'recent_enrollments': [{
            'user': enrollment.user.email,
            'section': enrollment.schedule.section.name,
            'center': enrollment.schedule.section.center.name,
            'date': enrollment.schedule.date,
            'attended': enrollment.attended,
        } for enrollment in recent_enrollments],
    })


@api_view(['GET'])
def dashboard_notifications(request):
    today = timezone.now().date()

    upcoming_lessons = Schedule.objects.filter(date__gte=today, date__lte=today + timedelta(days=7))
    expired_subscriptions = Subscription.objects.filter(end_date__lt=today, is_active=False)

    return Response({
        'upcoming_lessons': [{
            'center': lesson.center.name,
            'section': lesson.section.name,
            'date': lesson.date,
            'start_time': lesson.start_time,
            'end_time': lesson.end_time,
            'capacity': lesson.capacity,
            'reserved': lesson.reserved,
        } for lesson in upcoming_lessons],
        'expired_subscriptions': [{
            'user': subscription.user.email,
            'section': subscription.section.name,
            'end_date': subscription.end_date,
        } for subscription in expired_subscriptions]
    })

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import TestQuestion, UserResults

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from django.http import JsonResponse
from .models import TestQuestion, UserResults
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import TestQuestion, UserResults
from user.models import CustomUser

@api_view(['POST'])
def submit_test(request):
    user = request.user
    if user.is_anonymous:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data
    test_id = data.get('test_id')
    
    # Проверка на наличие test_id
    if not test_id:
        return Response({"error": "Test ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Получаем тестовые вопросы для конкретного силлабуса
        syllabus = Syllabus.objects.get(id=test_id)
        test_questions = TestQuestion.objects.filter(syllabus=syllabus)

        total_points_earned = 0  # Переменная для подсчета общего количества очков
        points_per_correct_answer = 10  # Количество очков за правильный ответ
        results = []

        # Обработка всех ответов, которые пользователь прислал
        for answer in data['answers']:
            question_id = answer['question_id']
            chosen_answer = answer['chosen_answer']

            # Получение вопроса по его ID и проверка, принадлежит ли он данному силлабусу
            try:
                question = test_questions.get(id=question_id)
            except TestQuestion.DoesNotExist:
                return Response({"error": f"Question with ID {question_id} not found in this test"}, status=status.HTTP_404_NOT_FOUND)

            # Проверка правильного ответа
            is_correct = question.correct_answer == chosen_answer

            # Начисление очков за правильный ответ
            points_earned = points_per_correct_answer if is_correct else 0
            total_points_earned += points_earned

            # Сохранение результата
            result = UserResults.objects.create(
                test_question=question,
                user=user,
                chosen_answer=chosen_answer,
                is_correct=is_correct,
                points=points_earned
            )

            # Добавление результата в итоговый список
            results.append({
                "question": question.question,
                "chosen_answer": chosen_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "points": points_earned,
                "options": question.options
            })

        # Обновление общего количества очков пользователя
        user.add_points(total_points_earned)

        return Response({"results": results, "total_points_earned": total_points_earned, "user_total_points": user.total_points}, status=status.HTTP_200_OK)

    except Syllabus.DoesNotExist:
        return Response({"error": "Test not found"}, status=status.HTTP_404_NOT_FOUND)
    except KeyError as e:
        return Response({"error": f"Missing key: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_user_results(request):
    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)

    user = request.user
    user_results = UserResults.objects.filter(user=user)

    results = []
    for result in user_results:
        results.append({
            "question": result.test_question.question,
            "chosen_answer": result.chosen_answer,
            "correct_answer": result.test_question.correct_answer,
            "is_correct": result.is_correct,
            "points": result.points
        })

    return Response({"results": results})
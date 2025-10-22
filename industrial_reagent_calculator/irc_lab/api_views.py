from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import ChemicalProcess, ReagentCalculation, ChemicalProcessInReagentCalculation
from django.contrib.auth.models import User
from django.db.models import Sum
from .views import get_reagent_calculaion_in_draft_ctatus
from django.contrib.auth import login, logout, authenticate
from .serializers import (
    ChemicalProcessInCalculationDeleteSerializer,
    ChemicalProcessInCalculationUpdateSerializer,
    ChemicalProcessSerializer, 
    ChemicalProcessCreateSerializer,
    ChemicalProcessImageSerializer,
    ReagentCalculationSerializer, 
    ReagentCalculationCreateSerializer,
    CartIconSerializer,
    ChemicalProcessInCalculationSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer, 
    UserLoginSerializer
)

# Swagger imports
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Permissions imports
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from .permissions import IsManager, IsAdmin, IsOwner, IsOwnerOrManager

class ChemicalProcessList(APIView):
    """
    GET: Список услуг с фильтрацией
    POST: Добавление новой услуги (без изображения)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Получить список химических процессов с фильтрацией",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Поиск по названию", type=openapi.TYPE_STRING),
        ],
        responses={200: ChemicalProcessSerializer(many=True)}
    )
    def get(self, request):
        # Фильтрация - только активные услуги
        processes = ChemicalProcess.objects.filter(is_active=True)
        
        # Фильтрация по названию (если передан параметр search)
        search_query = request.GET.get('search', '')
        if search_query:
            processes = processes.filter(
                Q(name__istartswith=search_query)
            )
        
        serializer = ChemicalProcessSerializer(processes, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Создать новый химический процесс",
        request_body=ChemicalProcessCreateSerializer,
        responses={
            201: ChemicalProcessCreateSerializer,
            400: 'Validation Error'
        }
    )
    def post(self, request):
        # Проверка прав - только менеджеры и админы могут создавать процессы
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Недостаточно прав для создания химического процесса'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = ChemicalProcessCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChemicalProcessDetail(APIView):
    """
    GET: Получение одной услуги
    PUT: Изменение услуги
    DELETE: Удаление услуги (с удалением изображения)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Получить детали химического процесса по ID",
        responses={200: ChemicalProcessSerializer}
    )
    def get(self, request, pk):
        process = get_object_or_404(ChemicalProcess, pk=pk, is_active=True)
        serializer = ChemicalProcessSerializer(process)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Обновить химический процесс",
        request_body=ChemicalProcessCreateSerializer,
        responses={
            200: ChemicalProcessCreateSerializer,
            400: 'Validation Error'
        }
    )
    def put(self, request, pk):
        # Проверка прав - только менеджеры и админы могут изменять процессы
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Недостаточно прав для изменения химического процесса'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        process = get_object_or_404(ChemicalProcess, pk=pk, is_active=True)
        serializer = ChemicalProcessCreateSerializer(process, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Удалить химический процесс (деактивация)",
        responses={204: 'No Content'}
    )
    def delete(self, request, pk):
        # Проверка прав - только менеджеры и админы могут удалять процессы
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Недостаточно прав для удаления химического процесса'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        process = get_object_or_404(ChemicalProcess, pk=pk, is_active=True)
        process.is_active = False
        process.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='post',
    operation_description="Добавить/изменить изображение для химического процесса",
    request_body=ChemicalProcessImageSerializer,
    responses={
        200: ChemicalProcessImageSerializer,
        400: 'Validation Error'
    }
)
@api_view(['POST'])
def chemical_process_upload_image(request, pk):
    """
    POST: Добавление/изменение изображения для услуги
    """
    # Проверка прав - только менеджеры и админы
    if not (request.user.is_staff or request.user.is_superuser):
        return Response(
            {'error': 'Недостаточно прав для загрузки изображений'}, 
            status=status.HTTP_403_FORBIDDEN
        )
        
    process = get_object_or_404(ChemicalProcess, pk=pk, is_active=True)
    
    # TODO: Здесь будет логика загрузки в Minio
    # Пока просто сохраняем URL или файл
    
    serializer = ChemicalProcessImageSerializer(process, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CartIconView(APIView):
    """
    GET: Иконка корзины - возвращает id заявки-черновика и количество услуг
    """
    permission_classes = [IsAuthenticated]  # Только авторизованные
    
    @swagger_auto_schema(
        operation_description="Получить информацию о корзине (количество процессов в черновике)",
        responses={200: CartIconSerializer}
    )
    def get(self, request):
        user = request.user
        
        # Ищем заявку в статусе DRAFT для этого пользователя
        draft_calculation = get_reagent_calculaion_in_draft_ctatus(user)
        
        processes_count = 0
        calculation_id = None
        
        if draft_calculation:
            calculation_id = draft_calculation.id
            processes_count = ChemicalProcessInReagentCalculation.objects.filter(
                calculation=draft_calculation
            ).count()
        
        serializer = CartIconSerializer({
            'calculation_id': calculation_id,
            'processes_count': processes_count
        })
        
        return Response(serializer.data)

class ReagentCalculationList(APIView):
    """
    GET: Список заявок (кроме удаленных и черновика) с фильтрацией
    """
    permission_classes = [IsAuthenticated]  # Только авторизованные
    
    @swagger_auto_schema(
        operation_description="Получить список заявок на расчет реагентов",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Фильтр по статусу", type=openapi.TYPE_STRING),
            openapi.Parameter('date_from', openapi.IN_QUERY, description="Дата от (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('date_to', openapi.IN_QUERY, description="Дата до (YYYY-MM-DD)", type=openapi.TYPE_STRING),
        ],
        responses={200: ReagentCalculationSerializer(many=True)}
    )
    def get(self, request):
        # Базовый queryset - исключаем удаленные и черновики
        base_queryset = ReagentCalculation.objects.exclude(
            status__in=[
                ReagentCalculation.ReagentCalculationStatus.DELETED,
                ReagentCalculation.ReagentCalculationStatus.DRAFT
            ]
        )
        
        # Разные права доступа для разных ролей
        if request.user.is_staff or request.user.is_superuser:
            # Менеджеры и админы видят все заявки
            calculations = base_queryset
        else:
            # Обычные пользователи видят только свои заявки
            calculations = base_queryset.filter(client=request.user)
        
        # Фильтрация по статусу
        status_filter = request.GET.get('status', '')
        if status_filter:
            calculations = calculations.filter(status=status_filter)
        
        # Фильтрация по диапазону даты формирования
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        if date_from:
            calculations = calculations.filter(formation_datetime__date__gte=date_from)
        if date_to:
            calculations = calculations.filter(formation_datetime__date__lte=date_to)
        
        serializer = ReagentCalculationSerializer(calculations, many=True)
        return Response(serializer.data)

class ReagentCalculationDetail(APIView):
    """
    GET: Детали заявки с услугами
    PUT: Изменение полей заявки
    DELETE: Удаление заявки
    """
    permission_classes = [IsOwnerOrManager]  # Владелец ИЛИ менеджер
    
    @swagger_auto_schema(
        operation_description="Получить детали заявки на расчет реагентов",
        responses={200: ReagentCalculationSerializer}
    )
    def get(self, request, pk):
        calculation = get_object_or_404(ReagentCalculation, pk=pk)
        # Permission IsOwnerOrManager автоматически проверит доступ

        self.check_object_permissions(request, calculation)

        serializer = ReagentCalculationSerializer(calculation)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Обновить заявку на расчет реагентов",
        request_body=ReagentCalculationCreateSerializer,
        responses={
            200: ReagentCalculationSerializer,
            400: 'Validation Error'
        }
    )
    def put(self, request, pk):
        calculation = get_object_or_404(ReagentCalculation, pk=pk)
        # Permission IsOwnerOrManager автоматически проверит доступ
        
        self.check_object_permissions(request, calculation)


        if calculation.client.id != request.user.id and not request.user.is_staff:
            return Response(
                {"error": f"Access denied. Calculation owned by user {calculation.client.id}"},
                status=403
            )

        serializer = ReagentCalculationCreateSerializer(calculation, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # Возвращаем полные данные заявки
            full_serializer = ReagentCalculationSerializer(calculation)
            return Response(full_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Удалить заявку на расчет реагентов",
        responses={
            204: 'No Content',
            400: 'Validation Error'
        }
    )
    def delete(self, request, pk):
        calculation = get_object_or_404(ReagentCalculation, pk=pk)
        # Permission IsOwnerOrManager автоматически проверит доступ
        self.check_object_permissions(request, calculation)

        # Можно удалять только черновики (по заданию)
        if calculation.status != ReagentCalculation.ReagentCalculationStatus.DRAFT:
            return Response(
                {'error': 'Можно удалять только заявки в статусе черновика'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calculation.status = ReagentCalculation.ReagentCalculationStatus.DELETED
        calculation.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='put',
    operation_description="Сформировать заявку (изменить статус DRAFT → FORMED)",
    responses={
        200: ReagentCalculationSerializer,
        400: 'Validation Error'
    }
)
@api_view(['PUT'])
@permission_classes([IsOwner])  # Только владелец может формировать свою заявку
def calculation_form(request, pk):
    """
    PUT: Сформировать заявку создателем
    Проверка обязательных полей и смена статуса DRAFT → FORMED
    """
    calculation = get_object_or_404(ReagentCalculation, pk=pk)
    # Permission IsOwner автоматически проверит что request.user == calculation.client
    
    # Проверяем, что заявка в статусе черновика
    if calculation.status != ReagentCalculation.ReagentCalculationStatus.DRAFT:
        return Response(
            {'error': 'Можно формировать только заявки в статусе черновика'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверка обязательных полей
    required_fields = ['target_mass', 'safety_factor', 'calculation_date']
    missing_fields = []
    
    for field in required_fields:
        if not getattr(calculation, field):
            missing_fields.append(field)
    
    if missing_fields:
        return Response(
            {'error': f'Обязательные поля не заполнены: {", ".join(missing_fields)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Проверяем, что в заявке есть хотя бы одна услуга
    processes_count = ChemicalProcessInReagentCalculation.objects.filter(
        calculation=calculation
    ).count()
    
    if processes_count == 0:
        return Response(
            {'error': 'Нельзя сформировать пустую заявку. Добавьте хотя бы одну услугу.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Меняем статус и проставляем дату формирования
    calculation.status = ReagentCalculation.ReagentCalculationStatus.FORMED
    calculation.formation_datetime = timezone.now()
    calculation.save()
    
    serializer = ReagentCalculationSerializer(calculation)
    return Response(serializer.data)

@swagger_auto_schema(
    method='put',
    operation_description="Завершить/отклонить заявку модератором",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'action': openapi.Schema(type=openapi.TYPE_STRING, description='complete или reject')
        }
    ),
    responses={
        200: ReagentCalculationSerializer,
        400: 'Validation Error'
    }
)
@api_view(['PUT'])
@permission_classes([IsManager])  # Только менеджеры могут завершать заявки
def calculation_complete(request, pk):
    """
    PUT: Завершить/отклонить заявку модератором
    Статус FORMED → COMPLETED/REJECTED
    Расчет total_input_mass при завершении
    """
    calculation = get_object_or_404(ReagentCalculation, pk=pk)
    
    # Проверяем, что заявка в статусе "Сформирована"
    if calculation.status != ReagentCalculation.ReagentCalculationStatus.FORMED:
        return Response(
            {'error': 'Можно завершать только заявки в статусе "Сформирована"'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Получаем действие из запроса (complete/reject)
    action = request.data.get('action')
    if action not in ['complete', 'reject']:
        return Response(
            {'error': 'Неверное действие. Допустимые значения: complete, reject'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Используем текущего пользователя как модератора
    moderator = request.user
    
    # Меняем статус в зависимости от действия
    if action == 'complete':
        calculation.status = ReagentCalculation.ReagentCalculationStatus.COMPLETED
        
        ## 🔧 РАСЧЕТ БИЗНЕС-ЛОГИКИ ПРИ ЗАВЕРШЕНИИ
        # Расчет общей массы реагентов (формула из лабораторной 2)
        total_input_mass = calculate_total_input_mass(calculation)
        calculation.total_input_mass = total_input_mass
        
    else:  # reject
        calculation.status = ReagentCalculation.ReagentCalculationStatus.REJECTED
    
    # Проставляем модератора и дату завершения
    calculation.manager = moderator
    calculation.completion_datetime = timezone.now()
    calculation.save()
    
    serializer = ReagentCalculationSerializer(calculation)
    return Response(serializer.data)

def calculate_total_input_mass(calculation):
    """
    Расчет общей массы реагентов для завершенной заявки
    Формула: сумма(process.input_mass * quantity) * (target_mass / 1000) * (1 + safety_factor/100)
    """
    processes_in_calculation = ChemicalProcessInReagentCalculation.objects.filter(
        calculation=calculation
    ).select_related('process')
    
    total_mass = 0
    
    for item in processes_in_calculation:
        # Базовая масса для target_mass = 1000 кг
        base_mass_for_1000 = item.process.input_mass * item.quantity
        
        # Масштабируем под целевую массу
        scaled_mass = base_mass_for_1000 * (calculation.target_mass / 1000)
        
        # Учитываем выход реакции
        mass_with_yield = scaled_mass * (100 / item.process.yield_percent)
        
        # Учитываем коэффициент запаса
        mass_with_safety = mass_with_yield * (1 + calculation.safety_factor / 100)
        
        total_mass += mass_with_safety
    
    return round(total_mass, 2)

@swagger_auto_schema(
    method='post',
    operation_description="Добавить химический процесс в корзину (заявку-черновик)",
    responses={
        201: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'calculation_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'processes_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'created_new_calculation': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Только авторизованные
def add_process_to_cart(request, pk):
    """
    POST: Добавление услуги в заявку-черновик
    Создает заявку если ее нет, добавляет услугу
    """
    # Получаем услугу
    process = get_object_or_404(ChemicalProcess, pk=pk, is_active=True)
    
    # Используем текущего пользователя
    user = request.user
    
    # Ищем или создаем заявку-черновик для пользователя
    calculation = get_reagent_calculaion_in_draft_ctatus(user)

    created = False

    if not calculation:
        # Создаем новую заявку
        calculation = ReagentCalculation.objects.create(
            client=user,
            status=ReagentCalculation.ReagentCalculationStatus.DRAFT,
            target_mass=1000,
            safety_factor=10, 
            calculation_date=timezone.now().date()
        )
        created = True
    
    # Проверяем, не добавлена ли уже эта услуга в заявку
    existing_relation = ChemicalProcessInReagentCalculation.objects.filter(
        calculation=calculation,
        process=process
    ).first()
    
    if existing_relation:
        # Если уже есть - увеличиваем quantity
        existing_relation.quantity += 1
        existing_relation.save()
    else:
        # Если нет - создаем новую связь
        ChemicalProcessInReagentCalculation.objects.create(
            calculation=calculation,
            process=process,
            quantity=1,
            comment='Добавлено через API',
            calculation_result=0
        )
    
    # Возвращаем информацию о корзине
    processes_count = ChemicalProcessInReagentCalculation.objects.filter(
        calculation=calculation
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    return Response({
        'message': f'Услуга "{process.name}" добавлена в заявку',
        'calculation_id': calculation.id,
        'processes_count': processes_count,
        'created_new_calculation': created
    }, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='put',
    operation_description="Обновить связь химического процесса в заявке",
    request_body=ChemicalProcessInCalculationUpdateSerializer,
    responses={
        200: ChemicalProcessInCalculationUpdateSerializer,
        400: 'Validation Error'
    }
)
@api_view(['PUT'])
@permission_classes([IsOwner])  # Только владелец заявки
def update_calculation_process(request):
    """
    PUT: Изменение M2M связи (количество, порядок, комментарий)
    Без PK - используем calculation_id и process_id
    """
    serializer = ChemicalProcessInCalculationDeleteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    calculation_id = serializer.validated_data['calculation_id']
    process_id = serializer.validated_data['process_id']
    
    # Ищем заявку и проверяем права
    calculation = get_object_or_404(ReagentCalculation, pk=calculation_id)
    if calculation.client != request.user:
        return Response(
            {'error': 'Нет прав для изменения этой заявки'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Ищем M2M связь
    m2m_relation = get_object_or_404(
        ChemicalProcessInReagentCalculation,
        calculation_id=calculation_id,
        process_id=process_id
    )
    
    # Обновляем данные
    update_serializer = ChemicalProcessInCalculationUpdateSerializer(
        m2m_relation, 
        data=request.data, 
        partial=True
    )
    
    if update_serializer.is_valid():
        update_serializer.save()
        return Response(update_serializer.data)
    
    return Response(update_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='delete',
    operation_description="Удалить химический процесс из заявки",
    request_body=ChemicalProcessInCalculationDeleteSerializer,
    responses={
        204: 'No Content',
        400: 'Validation Error'
    }
)
@api_view(['DELETE'])
@permission_classes([IsOwner])  # Только владелец заявки
def delete_calculation_process(request):
    """
    DELETE: Удаление M2M связи (удаление услуги из заявки)
    Без PK - используем calculation_id и process_id
    """
    serializer = ChemicalProcessInCalculationDeleteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    calculation_id = serializer.validated_data['calculation_id']
    process_id = serializer.validated_data['process_id']
    
    # Ищем заявку и проверяем права
    calculation = get_object_or_404(ReagentCalculation, pk=calculation_id)
    if calculation.client != request.user:
        return Response(
            {'error': 'Нет прав для изменения этой заявки'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Ищем и удаляем M2M связь
    m2m_relation = get_object_or_404(
        ChemicalProcessInReagentCalculation,
        calculation_id=calculation_id,
        process_id=process_id
    )
    
    m2m_relation.delete()
    
    return Response(
        {'message': 'Услуга удалена из заявки'}, 
        status=status.HTTP_204_NO_CONTENT
    )

@swagger_auto_schema(
    method='post',
    operation_description="Регистрация нового пользователя",
    request_body=UserRegistrationSerializer,
    responses={
        201: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        400: 'Validation Error'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])  # Отключаем аутентификацию для регистрации
def user_register(request):
    """
    POST: Регистрация - создаем пользователя, но не логиним
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {'message': 'Пользователь успешно зарегистрирован', 'user_id': user.id},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    operation_description="Получить профиль пользователя",
    responses={200: UserProfileSerializer}
)
@swagger_auto_schema(
    method='put',
    operation_description="Обновить профиль пользователя",
    request_body=UserProfileSerializer,
    responses={
        200: UserProfileSerializer,
        400: 'Validation Error'
    }
)
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])  # Только авторизованные
def user_profile(request):
    """
    GET/PUT: Профиль - работаем с текущим пользователем
    """
    user = request.user  # Используем текущего пользователя
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_description="Аутентификация пользователя с созданием сессии",
    request_body=UserLoginSerializer,
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'is_superuser': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        ),
        400: 'Validation Error'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])  # Отключаем аутентификацию для логина
def user_login(request):
    """
    POST: Аутентификация - проверяем учетные данные и создаем сессию
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)  # Создаем сессию
        return Response({
            'message': 'Успешная аутентификация', 
            'user_id': user.id,
            'username': user.username,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_description="Выход пользователя из системы",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    """
    POST: Деавторизация - удаляем сессию
    """
    logout(request)
    return Response({'message': 'Выход выполнен'})

@swagger_auto_schema(
    method='get',
    operation_description="Просмотр активных сессий в Redis (только для админов)",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'active_sessions_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'sessions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAdmin])
def view_redis_sessions(request):
    """
    GET: Просмотр активных сессий в Redis - для демонстрации в лабораторной
    """
    from django.core.cache import cache
    from django.contrib.sessions.models import Session
    import re
    
    try:
        # Получаем все ключи сессий из Redis
        # Используем низкоуровневый доступ к Redis
        import django_redis
        redis_client = django_redis.get_redis_connection("default")
        
        # Ищем ключи сессий (они имеют префикс)
        session_keys = []
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=':1:django.contrib.sessions.cache*', count=100)
            session_keys.extend(keys)
            if cursor == 0:
                break
        
        sessions_data = []
        for key in session_keys:
            try:
                # Получаем данные сессии
                session_data = redis_client.get(key)
                if session_data:
                    # Декодируем данные сессии
                    decoded_data = session_data.decode('utf-8')
                    sessions_data.append({
                        'session_key': key.decode('utf-8'),
                        'data_preview': decoded_data[:100] + '...' if len(decoded_data) > 100 else decoded_data
                    })
            except Exception as e:
                sessions_data.append({
                    'session_key': key.decode('utf-8') if isinstance(key, bytes) else str(key),
                    'error': str(e)
                })
        
        return Response({
            'active_sessions_count': len(sessions_data),
            'sessions': sessions_data
        })
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при получении сессий из Redis: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import ChemicalProcess, ReagentCalculation, ChemicalProcessInReagentCalculation
from django.contrib.auth.models import User
from django.db.models import Sum
from .views import get_reagent_calculaion_in_draft_ctatus
from django.contrib.auth import login, logout
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

def get_fixed_user():
    try:
        user = User.objects.get(id=1)
    except User.DoesNotExist:
        user = User.objects.create_user(
            id=1,
            username='student',
            password='root'
        )
    return user

class ChemicalProcessList(APIView):
    """
    GET: Список услуг с фильтрацией
    POST: Добавление новой услуги (без изображения)
    """
    
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
    
    def post(self, request):
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
    
    def get(self, request, pk):
        process = get_object_or_404(ChemicalProcess, pk=pk, is_active=True)
        serializer = ChemicalProcessSerializer(process)
        return Response(serializer.data)
    
    def put(self, request, pk):
        process = get_object_or_404(ChemicalProcess, pk=pk, is_active=True)
        serializer = ChemicalProcessCreateSerializer(process, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        process = get_object_or_404(ChemicalProcess, pk=pk, is_active=True)
        # Вместо реального удаления помечаем как неактивный
        process.is_active = False
        process.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def chemical_process_upload_image(request, pk):
    """
    POST: Добавление/изменение изображения для услуги
    """
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
    
    def get(self, request):
        user = get_fixed_user()
        
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
    
    def get(self, request):
        # Исключаем удаленные и черновики
        calculations = ReagentCalculation.objects.exclude(
            status__in=[
                ReagentCalculation.ReagentCalculationStatus.DELETED,
                ReagentCalculation.ReagentCalculationStatus.DRAFT
            ]
        )
        
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
    
    def get(self, request, pk):
        calculation = get_object_or_404(ReagentCalculation, pk=pk)
        serializer = ReagentCalculationSerializer(calculation)
        return Response(serializer.data)
    
    def put(self, request, pk):
        calculation = get_object_or_404(ReagentCalculation, pk=pk)
        serializer = ReagentCalculationCreateSerializer(calculation, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # Возвращаем полные данные заявки
            full_serializer = ReagentCalculationSerializer(calculation)
            return Response(full_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        calculation = get_object_or_404(ReagentCalculation, pk=pk)
        
        # Можно удалять только черновики (по заданию)
        if calculation.status != ReagentCalculation.ReagentCalculationStatus.DRAFT:
            return Response(
                {'error': 'Можно удалять только заявки в статусе черновика'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calculation.status = ReagentCalculation.ReagentCalculationStatus.DELETED
        calculation.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['PUT'])
def calculation_form(request, pk):
    """
    PUT: Сформировать заявку создателем
    Проверка обязательных полей и смена статуса DRAFT → FORMED
    """
    calculation = get_object_or_404(ReagentCalculation, pk=pk)
    
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

@api_view(['PUT'])
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
    
    # Получаем фиксированного модератора (пока используем того же пользователя)
    moderator = get_fixed_user()
    
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

@api_view(['POST'])
def add_process_to_cart(request, pk):
    """
    POST: Добавление услуги в заявку-черновик
    Создает заявку если ее нет, добавляет услугу
    """
    # Получаем услугу
    process = get_object_or_404(ChemicalProcess, pk=pk, is_active=True)
    
    # Получаем фиксированного пользователя
    user = get_fixed_user()
    
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

@api_view(['PUT'])
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

@api_view(['DELETE'])
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

@api_view(['POST'])
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

@api_view(['GET', 'PUT'])
def user_profile(request):
    """
    GET/PUT: Профиль - работаем с фиксированным пользователем
    """
    # Для демонстрации используем пользователя с ID=1
    user = User.objects.get(id=1)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def user_login(request):
    """
    POST: Аутентификация - проверяем учетные данные, но не используем сессии
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        return Response({
            'message': 'Учетные данные верны', 
            'user_id': user.id,
            'username': user.username
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def user_logout(request):
    """
    POST: Деавторизация - фиктивный метод для демонстрации
    """
    return Response({'message': 'Выход выполнен'})
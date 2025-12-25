from rest_framework import serializers
from .models import ChemicalProcess, ReagentCalculation, ChemicalProcessInReagentCalculation
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class ChemicalProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChemicalProcess
        fields = [
            'id', 'name', 'description', 'input_reagent', 'output_product',
            'input_mass', 'output_mass', 'yield_percent', 'image',
            'reaction_equation', 'parameter_name', 'parameter_unit',
            'parameter_min', 'parameter_max', 'parameter_default', 'is_active'
        ]
        read_only_fields = ['id']

class ChemicalProcessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChemicalProcess
        fields = [
            'name', 'description', 'input_reagent', 'output_product',
            'input_mass', 'output_mass', 'yield_percent',
            'reaction_equation', 'parameter_name', 'parameter_unit',
            'parameter_min', 'parameter_max', 'parameter_default'
        ]

class ChemicalProcessImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChemicalProcess
        fields = ['image']

class ChemicalProcessInCalculationSerializer(serializers.ModelSerializer):
    """Сериализатор для связи услуга-в-заявке"""
    process_name = serializers.CharField(source='process.name', read_only=True)
    process_image = serializers.CharField(source='process.image', read_only=True)
    
    class Meta:
        model = ChemicalProcessInReagentCalculation
        fields = [
            'id', 'calculation', 'process', 'process_name', 'process_image',
            'quantity', 'calculation_result'
        ]
        read_only_fields = ['id', 'calculation']

class ReagentCalculationDetailSerializer(serializers.ModelSerializer):
    """
    ДЕТАЛЬНЫЙ Сериализатор (с вложенными услугами).
    Используется для просмотра одной заявки.
    """
    processes = ChemicalProcessInCalculationSerializer(
        source='chemicalprocessinreagentcalculation_set', 
        many=True, 
        read_only=True
    )
    client_username = serializers.CharField(source='client.username', read_only=True)
    manager_username = serializers.CharField(source='manager.username', read_only=True)

    class Meta:
        model = ReagentCalculation
        fields = [
            "id",
            "status",
            "creation_datetime",
            "formation_datetime",
            "completion_datetime",
            "client",
            "client_username",
            "manager",
            "manager_username",
            "target_mass",
            "safety_factor",
            "calculation_date",
            "total_input_mass",
            "processes",
            "results_quantity",
        ]
        read_only_fields = [
            'id', 'status', 'creation_datetime', 'formation_datetime',
            'completion_datetime', 'client', 'manager', 'total_input_mass'
        ]

class ReagentCalculationListSerializer(serializers.ModelSerializer):
    """
    СПИСОЧНЫЙ Сериализатор (без тяжелых вложенных данных).
    Используется для вывода списка заявок.
    """
    client_username = serializers.CharField(source='client.username', read_only=True)
    manager_username = serializers.CharField(source='manager.username', read_only=True)

    class Meta:
        model = ReagentCalculation
        fields = [
            'id', 'status', 'creation_datetime', 'formation_datetime', 
            'completion_datetime', 'client', 'client_username', 'manager', 
            'manager_username', 'target_mass', 'safety_factor', 
            'calculation_date', 'total_input_mass', 'results_quantity'
        ]
        read_only_fields = [
            'id', 'status', 'creation_datetime', 'formation_datetime',
            'completion_datetime', 'client', 'manager', 'total_input_mass'
        ]

class ReagentCalculationCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/изменения заявки"""
    class Meta:
        model = ReagentCalculation
        fields = [
            'target_mass', 'safety_factor', 'calculation_date'
        ]

class CartIconSerializer(serializers.Serializer):
    """Сериализатор для иконки корзины"""
    calculation_id = serializers.IntegerField()
    processes_count = serializers.IntegerField()

class ChemicalProcessInCalculationUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения M2M связи"""
    class Meta:
        model = ChemicalProcessInReagentCalculation
        fields = ['quantity', 'calculation_result'] # УБРАНО поле 'comment'

class ChemicalProcessInCalculationDeleteSerializer(serializers.Serializer):
    """Сериализатор для удаления M2M связи"""
    calculation_id = serializers.IntegerField()
    process_id = serializers.IntegerField()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    # УБРАНО поле is_staff для безопасности
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают"})
        
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Пользователь с таким именем уже существует"})
            
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # Создаем обычного пользователя
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "password",
            "password_confirm"
        ]
        read_only_fields = ['id', 'username', 'date_joined']

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError(
                    {"password_confirm": "Пароли не совпадают"}
                )
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("password_confirm", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise serializers.ValidationError("Неверные учетные данные")
            if not user.is_active:
                raise serializers.ValidationError("Аккаунт отключен")
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError("Необходимо указать username и password")

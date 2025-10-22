from rest_framework import serializers
from .models import ChemicalProcess, ReagentCalculation, ChemicalProcessInReagentCalculation
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password

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
            'quantity', 'comment', 'calculation_result'
        ]
        read_only_fields = ['id', 'calculation']

class ReagentCalculationSerializer(serializers.ModelSerializer):
    """Сериализатор для заявки с вложенными услугами"""
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
            'id', 'status', 'creation_datetime', 'formation_datetime', 
            'completion_datetime', 'client', 'client_username', 'manager', 
            'manager_username', 'target_mass', 'safety_factor', 
            'calculation_date', 'total_input_mass', 'processes'
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
        fields = ['quantity', 'comment', 'calculation_result']

class ChemicalProcessInCalculationDeleteSerializer(serializers.Serializer):
    """Сериализатор для удаления M2M связи"""
    calculation_id = serializers.IntegerField()
    process_id = serializers.IntegerField()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
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
        # Убираем password_confirm и хэшируем пароль
        validated_data.pop('password_confirm')
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined']

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
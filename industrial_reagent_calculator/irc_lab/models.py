from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class ChemicalProcess(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    input_reagent = models.CharField(max_length=100)
    output_product = models.CharField(max_length=100)
    input_mass = models.DecimalField(max_digits=10, decimal_places=2)
    output_mass = models.DecimalField(max_digits=10, decimal_places=2)
    yield_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    image = models.URLField(blank=True, null=True)
    reaction_equation = models.TextField()
    parameter_name = models.CharField(max_length=100)
    parameter_unit = models.CharField(max_length=20)
    parameter_min = models.DecimalField(max_digits=8, decimal_places=2)
    parameter_max = models.DecimalField(max_digits=8, decimal_places=2)
    parameter_default = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
class ReagentCalculation(models.Model):
    class ReagentCalculationStatus(models.TextChoices):
        DRAFT = "DRAFT"
        DELETED = "DELETED"
        FORMED = "FORMED"
        COMPLETED = "COMPLETED"
        REJECTED = "REJECTED"

    status = models.CharField(
        max_length=10,
        choices=ReagentCalculationStatus.choices,
        default=ReagentCalculationStatus.DRAFT,
    )

    creation_datetime = models.DateTimeField(auto_now_add=True)
    formation_datetime = models.DateTimeField(blank=True, null=True)
    completion_datetime = models.DateTimeField(blank=True, null=True)
    
    client = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_calculations'
    )
    
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='managed_calculations', 
        blank=True, null=True
    )
    
    target_mass = models.DecimalField(
        max_digits=10, 
        decimal_places=2
    )
    safety_factor = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=10
    )
    calculation_date = models.DateField()
    
    total_input_mass = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, null=True
    )
    results_quantity = models.IntegerField(
        null=True
    )

    def __str__(self):
        return f"Расчет № {self.id}"
    
class ChemicalProcessInReagentCalculation(models.Model):
    calculation = models.ForeignKey(
        ReagentCalculation, 
        on_delete=models.CASCADE
        )
    process = models.ForeignKey(
        ChemicalProcess, 
        on_delete=models.CASCADE
        )
    
    quantity = models.IntegerField(default=1)
    
    calculation_result = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True
    )

    def __str__(self):
        return f"{self.calculation_id}-{self.process_id}"

    class Meta:
        unique_together = ('calculation', 'process')
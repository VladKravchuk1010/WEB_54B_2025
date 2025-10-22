from django.utils import timezone
from django.shortcuts import render, redirect
from .models import ChemicalProcess, ChemicalProcessInReagentCalculation, ReagentCalculation
from django.contrib.auth.models import User
from django.db import connection
from django.http import Http404
from django.db.models import Sum

def chemical_processes_list(request):
    calculation = get_reagent_calculaion_in_draft_ctatus()

    if not calculation: 
        calculation_id = 0
    else:
        calculation_id = calculation.id

    processes_in_request = count_processes_in_request(calculation_id)
    
    search_processes_query = request.GET.get('search_processes', '')
    
    return render(request, 'chemical_processes.html', {
        'processes': ChemicalProcess.objects.filter(name__istartswith=search_processes_query, is_active=True),
        'processes_in_request': processes_in_request,
        'search_processes_query': search_processes_query,
        'calculation_id': calculation_id,
    })

def chemical_process_detail(request, id):
    calculation = get_reagent_calculaion_in_draft_ctatus()

    if not calculation: 
        calculation_id = 0
    else:
        calculation_id = calculation.id

    processes_in_request = count_processes_in_request(calculation_id)

    return render(request, 'chemical_process_detail.html', {
        'process': ChemicalProcess.objects.get(id=id, is_active=True),
        'processes_in_request': processes_in_request,
        'calculation_id': calculation_id,
    })


def request_reagent_calculation(request, calculation_id):
    
    processes_in_request = count_processes_in_request(calculation_id)

    calculation = ReagentCalculation.objects.filter(
        id=calculation_id,
        status=ReagentCalculation.ReagentCalculationStatus.DRAFT,
    ).first()

    if not calculation:
        raise Http404("Заявка на расчет реагента не найдена")

    processes = ChemicalProcessInReagentCalculation.objects.filter(
        calculation=calculation,
        process__is_active=True,
    ).select_related('process')
    
    services_with_processes = []
    for item in processes:
        comment = item.comment
        if comment is None:
            comment = ''
        services_with_processes.append({
            'process': item.process,
            'm2m_data': {
                'quantity': item.quantity,
                'comment': comment,
                'calculation_result': item.calculation_result
            }
        })
    
    return render(request, 'request_reagent_calculation.html', {
        'processes_in_request': processes_in_request,
        'calculation': calculation,
        'services_with_processes': services_with_processes,
        'calculation_id': calculation.id,
    })

def remove_chemical_process(request, process_id):
    if request.method != "POST":
        return redirect('chemical_processes')
    try:
        process = ChemicalProcess.objects.get(id=process_id)
        process.is_active = False
        process.save()
        return redirect('chemical_processes')
    except ChemicalProcess.DoesNotExist:
        return redirect('chemical_processes')
    
def remove_reagent_calculation(request, calculation_id):
    if request.method != "POST":
        return redirect('request_reagent_calculation')
        
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE irc_lab_reagentcalculation SET status = 'deleted' WHERE id = %s",
            [calculation_id]
        )

    
    return redirect('chemical_processes')
    
def add_chemical_process(request, process_id):

    process = ChemicalProcess.objects.get(id=process_id)

    calculation = get_reagent_calculaion_in_draft_ctatus()
    
    if not calculation:
        calculation = ReagentCalculation.objects.create(
            client=User.objects.get(username="student"),
            status=ReagentCalculation.ReagentCalculationStatus.DRAFT,
            target_mass=1000,  # значение по умолчанию
            safety_factor=10,  # значение по умолчанию
            calculation_date=timezone.now().date()
        )
    
    existing_relation = ChemicalProcessInReagentCalculation.objects.filter(
            calculation=calculation,
            process=process
        ).first()
        
    if existing_relation:
        existing_relation.quantity += 1
        existing_relation.save()
    else:
        ChemicalProcessInReagentCalculation.objects.create(
            calculation=calculation,
            process=process,
            quantity=1,
            calculation_result=0
            
        )

    return redirect('chemical_processes')

def get_reagent_calculaion_in_draft_ctatus(user=None):

    if user is None:
        user = User.objects.get(username="student")

    calculation = ReagentCalculation.objects.filter(
            client=user,
            status=ReagentCalculation.ReagentCalculationStatus.DRAFT
        ).first()

    return calculation

def count_processes_in_request(calculation_id):
    if calculation_id == 0:
        return 0
    
    total_quantity = ChemicalProcessInReagentCalculation.objects.filter(
        calculation__id=calculation_id,
        process__is_active=True,
    ).aggregate(total=Sum('quantity'))['total']
    
    return total_quantity or 0
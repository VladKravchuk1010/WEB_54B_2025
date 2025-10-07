from django.shortcuts import render
from .data import processes, current_request

def chemical_processes_list(request):
    search_processes_query = request.GET.get('search_processes', '')
    if search_processes_query:
        filtered_processes = [p for p in processes if search_processes_query.lower() in p['name'].lower()]
    else:
        filtered_processes = processes
    
    return render(request, 'chemical_processes.html', {
        'processes': filtered_processes,
        'current_request': current_request,
        'search_processes_query': search_processes_query
    })

def process_calculation(request, id):
    process = next((p for p in processes if p['id'] == id), None)
    if not process:
        return render(request, '404.html')
    
    return render(request, 'process_calculation.html', {
        'process': process,
        'current_request': current_request
    })

def request_composition(request):
    services_with_m2m = []
    for service_m2m in current_request['services_m2m']:
        process = next((p for p in processes if p['id'] == service_m2m['service_id']), None)
        if process:
            services_with_m2m.append({
                'process': process,
                'm2m_data': service_m2m
            })
    
    return render(request, 'request_composition.html', {
        'current_request': current_request,
        'services_with_processes': services_with_m2m
    })
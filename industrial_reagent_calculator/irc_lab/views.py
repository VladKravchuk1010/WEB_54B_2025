from django.shortcuts import render
from .data import processes, current_request

def processes_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        filtered_processes = [p for p in processes if search_query.lower() in p['name'].lower()]
    else:
        filtered_processes = processes
    
    return render(request, 'processes.html', {
        'processes': filtered_processes,
        'current_request': current_request,
        'search_query': search_query
    })

def process_detail(request, id):
    process = next((p for p in processes if p['id'] == id), None)
    if not process:
        return render(request, '404.html')
    
    return render(request, 'process_detail.html', {
        'process': process,
        'current_request': current_request
    })

def request_detail(request):
    selected_processes = [p for p in processes if p['id'] in current_request['selected_processes']]
    
    return render(request, 'request_detail.html', {
        'current_request': current_request,
        'processes': selected_processes
    })
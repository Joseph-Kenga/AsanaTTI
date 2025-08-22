from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Table
from orders.models import Order
import json

@login_required
def table_dashboard(request):
    """Main dashboard showing all tables with their current status"""
    tables = Table.objects.filter(is_active=True).order_by('table_number')
    
    # Get active orders for each table
    for table in tables:
        table.active_orders = table.orders.filter(status__in=['pending', 'preparing', 'ready'])
        table.total_active_amount = sum(order.total_amount for order in table.active_orders)
    
    context = {
        'tables': tables,
        'title': 'Table Dashboard'
    }
    return render(request, 'tables/dashboard.html', context)

@login_required
def table_detail(request, table_id):
    """Detailed view of a specific table"""
    table = get_object_or_404(Table, id=table_id)
    active_orders = table.orders.filter(status__in=['pending', 'preparing', 'ready'])
    completed_orders = table.orders.filter(status='completed').order_by('-created_at')[:10]
    
    context = {
        'table': table,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'title': f'Table {table.table_number}'
    }
    return render(request, 'tables/detail.html', context)

@login_required
@require_POST
def update_table_status(request, table_id):
    """Update table status (available, occupied, cleaning, etc.)"""
    table = get_object_or_404(Table, id=table_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Table.TABLE_STATUS_CHOICES):
        old_status = table.status
        table.status = new_status
        table.save()
        
        messages.success(request, f'Table {table.table_number} status updated from {old_status} to {new_status}')
    else:
        messages.error(request, 'Invalid status provided')
    
    return redirect('table_detail', table_id=table_id)

@login_required
@require_POST
def update_table_occupancy(request, table_id):
    """Update current occupancy of a table"""
    table = get_object_or_404(Table, id=table_id)
    new_occupancy = request.POST.get('current_occupancy')
    
    try:
        occupancy = int(new_occupancy)
        if 0 <= occupancy <= table.capacity:
            table.current_occupancy = occupancy
            table.save()
            
            # Update status based on occupancy
            if occupancy == 0:
                table.status = 'available'
            else:
                table.status = 'occupied'
            table.save()
            
            messages.success(request, f'Table {table.table_number} occupancy updated to {occupancy}')
        else:
            messages.error(request, f'Occupancy must be between 0 and {table.capacity}')
    except ValueError:
        messages.error(request, 'Invalid occupancy value')
    
    return redirect('table_detail', table_id=table_id)

@login_required
@csrf_exempt
def table_status_api(request):
    """API endpoint for getting table status (for real-time updates)"""
    if request.method == 'GET':
        tables = Table.objects.filter(is_active=True).values(
            'id', 'table_number', 'name', 'capacity', 'current_occupancy', 
            'status', 'has_active_order'
        )
        
        # Add active order count for each table
        for table in tables:
            table_obj = Table.objects.get(id=table['id'])
            table['active_orders_count'] = table_obj.orders.filter(
                status__in=['pending', 'preparing', 'ready']
            ).count()
        
        return JsonResponse({'tables': list(tables)})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def clear_table(request, table_id):
    """Clear a table - mark all orders as completed and reset table status"""
    table = get_object_or_404(Table, id=table_id)
    
    # Complete all active orders
    active_orders = table.orders.filter(status__in=['pending', 'preparing', 'ready'])
    for order in active_orders:
        order.status = 'completed'
        order.save()
    
    # Reset table status
    table.status = 'available'
    table.current_occupancy = 0
    table.save()
    
    messages.success(request, f'Table {table.table_number} has been cleared')
    return redirect('table_dashboard')

@login_required
def table_list(request):
    """List all tables with filtering options"""
    status_filter = request.GET.get('status', '')
    capacity_filter = request.GET.get('capacity', '')
    
    tables = Table.objects.filter(is_active=True)
    
    if status_filter:
        tables = tables.filter(status=status_filter)
    
    if capacity_filter:
        tables = tables.filter(capacity=capacity_filter)
    
    tables = tables.order_by('table_number')
    
    context = {
        'tables': tables,
        'status_choices': Table.TABLE_STATUS_CHOICES,
        'title': 'Table List'
    }
    return render(request, 'tables/list.html', context)

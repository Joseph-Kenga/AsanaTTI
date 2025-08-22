from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Order, OrderItem, OrderItemTopping, OrderStatusHistory
from tables.models import Table
from menu.models import Item, Category, Size, Topping, CookingPreference
from billing.models import Bill
import json
from django.utils import timezone

@login_required
def order_dashboard(request):
    """Main dashboard for order management"""
    pending_orders = Order.objects.filter(status='pending').order_by('created_at')
    preparing_orders = Order.objects.filter(status='preparing').order_by('created_at')
    ready_orders = Order.objects.filter(status='ready').order_by('created_at')
    
    context = {
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'title': 'Order Dashboard'
    }
    return render(request, 'orders/dashboard.html', context)

@login_required
def create_order(request, table_id):
    """Create a new order for a table"""
    table = get_object_or_404(Table, id=table_id)
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create the order
                order = Order.objects.create(
                    table=table,
                    waiter=request.user,
                    special_instructions=request.POST.get('special_instructions', '')
                )
                
                # Process order items
                items_data = json.loads(request.POST.get('items', '[]'))
                for item_data in items_data:
                    item = get_object_or_404(Item, id=item_data['item_id'])
                    size = None
                    if item_data.get('size_id'):
                        size = get_object_or_404(Size, id=item_data['size_id'])
                    
                    cooking_preference = None
                    if item_data.get('cooking_preference_id'):
                        cooking_preference = get_object_or_404(CookingPreference, id=item_data['cooking_preference_id'])
                    
                    # Calculate unit price
                    unit_price = item.base_price
                    if size:
                        unit_price += size.price_modifier
                    
                    # Create order item
                    order_item = OrderItem.objects.create(
                        order=order,
                        item=item,
                        size=size,
                        quantity=item_data['quantity'],
                        unit_price=unit_price,
                        cooking_preference=cooking_preference,
                        special_instructions=item_data.get('special_instructions', '')
                    )
                    
                    # Add toppings
                    for topping_id in item_data.get('toppings', []):
                        topping = get_object_or_404(Topping, id=topping_id)
                        OrderItemTopping.objects.create(
                            order_item=order_item,
                            topping=topping
                        )
                
                # Update order type
                order.update_order_type()
                
                # Update table status
                table.status = 'occupied'
                table.save()
                
                # Create status history
                OrderStatusHistory.objects.create(
                    order=order,
                    status='pending',
                    changed_by=request.user,
                    notes='Order created'
                )
                
                messages.success(request, f'Order #{order.id} created successfully for Table {table.table_number}')
                return redirect('order_detail', order_id=order.id)
                
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
    
    context = {
        'table': table,
        'categories': categories,
        'title': f'Create Order - Table {table.table_number}'
    }
    return render(request, 'orders/create_order.html', context)

@login_required
def order_detail(request, order_id):
    """Detailed view of an order"""
    order = get_object_or_404(Order, id=order_id)
    status_history = order.status_history.all()
    
    context = {
        'order': order,
        'status_history': status_history,
        'title': f'Order #{order.id}'
    }
    return render(request, 'orders/detail.html', context)

@login_required
@require_POST
def update_order_status(request, order_id):
    """Update order status"""
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')
    
    if new_status in dict(Order.ORDER_STATUS_CHOICES):
        old_status = order.status
        order.status = new_status
        
        if new_status == 'completed':
            order.completed_at = timezone.now()
        
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            changed_by=request.user,
            notes=notes
        )
        
        messages.success(request, f'Order #{order.id} status updated from {old_status} to {new_status}')
    else:
        messages.error(request, 'Invalid status provided')
    
    return redirect('order_detail', order_id=order_id)

@login_required
def kitchen_orders(request):
    """View for kitchen staff - shows food orders"""
    pending_food_orders = Order.objects.filter(
        status='pending',
        order_items__item__item_type='food'
    ).distinct().order_by('created_at')
    
    preparing_food_orders = Order.objects.filter(
        status='preparing',
        order_items__item__item_type='food'
    ).distinct().order_by('created_at')
    
    context = {
        'pending_orders': pending_food_orders,
        'preparing_orders': preparing_food_orders,
        'title': 'Kitchen Orders'
    }
    return render(request, 'orders/kitchen.html', context)

@login_required
def bar_orders(request):
    """View for bar staff - shows drink orders"""
    pending_drink_orders = Order.objects.filter(
        status='pending',
        order_items__item__item_type='drink'
    ).distinct().order_by('created_at')
    
    preparing_drink_orders = Order.objects.filter(
        status='preparing',
        order_items__item__item_type='drink'
    ).distinct().order_by('created_at')
    
    context = {
        'pending_orders': pending_drink_orders,
        'preparing_orders': preparing_drink_orders,
        'title': 'Bar Orders'
    }
    return render(request, 'orders/bar.html', context)

@login_required
@csrf_exempt
def order_status_api(request):
    """API endpoint for getting order status updates"""
    if request.method == 'GET':
        order_type = request.GET.get('type', 'all')
        
        if order_type == 'kitchen':
            orders = Order.objects.filter(
                status__in=['pending', 'preparing'],
                order_items__item__item_type='food'
            ).distinct()
        elif order_type == 'bar':
            orders = Order.objects.filter(
                status__in=['pending', 'preparing'],
                order_items__item__item_type='drink'
            ).distinct()
        else:
            orders = Order.objects.filter(status__in=['pending', 'preparing'])
        
        orders_data = []
        for order in orders:
            order_data = {
                'id': order.id,
                'table_number': order.table.table_number,
                'status': order.status,
                'order_type': order.order_type,
                'created_at': order.created_at.isoformat(),
                'total_amount': float(order.total_amount),
                'items_count': order.order_items.count()
            }
            orders_data.append(order_data)
        
        return JsonResponse({'orders': orders_data})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def add_item_to_order(request, order_id):
    """Add additional items to an existing order"""
    order = get_object_or_404(Order, id=order_id)
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                items_data = json.loads(request.POST.get('items', '[]'))
                for item_data in items_data:
                    item = get_object_or_404(Item, id=item_data['item_id'])
                    size = None
                    if item_data.get('size_id'):
                        size = get_object_or_404(Size, id=item_data['size_id'])
                    
                    cooking_preference = None
                    if item_data.get('cooking_preference_id'):
                        cooking_preference = get_object_or_404(CookingPreference, id=item_data['cooking_preference_id'])
                    
                    # Calculate unit price
                    unit_price = item.base_price
                    if size:
                        unit_price += size.price_modifier
                    
                    # Create order item
                    order_item = OrderItem.objects.create(
                        order=order,
                        item=item,
                        size=size,
                        quantity=item_data['quantity'],
                        unit_price=unit_price,
                        cooking_preference=cooking_preference,
                        special_instructions=item_data.get('special_instructions', '')
                    )
                    
                    # Add toppings
                    for topping_id in item_data.get('toppings', []):
                        topping = get_object_or_404(Topping, id=topping_id)
                        OrderItemTopping.objects.create(
                            order_item=order_item,
                            topping=topping
                        )
                
                # Update order type
                order.update_order_type()
                
                messages.success(request, f'Items added to Order #{order.id}')
                return redirect('order_detail', order_id=order.id)
                
        except Exception as e:
            messages.error(request, f'Error adding items: {str(e)}')
    
    context = {
        'order': order,
        'categories': categories,
        'title': f'Add Items - Order #{order.id}'
    }
    return render(request, 'orders/add_items.html', context)

@login_required
def modify_order_item(request, order_item_id):
    """Modify an existing order item"""
    order_item = get_object_or_404(OrderItem, id=order_item_id)
    
    if request.method == 'POST':
        try:
            # Update quantity
            new_quantity = int(request.POST.get('quantity', 1))
            if new_quantity > 0:
                order_item.quantity = new_quantity
                order_item.save()
                
                messages.success(request, f'Order item quantity updated to {new_quantity}')
            else:
                # Delete the item if quantity is 0
                order_item.delete()
                messages.success(request, 'Order item removed')
            
            return redirect('order_detail', order_id=order_item.order.id)
            
        except ValueError:
            messages.error(request, 'Invalid quantity value')
    
    context = {
        'order_item': order_item,
        'title': f'Modify Order Item'
    }
    return render(request, 'orders/modify_item.html', context)

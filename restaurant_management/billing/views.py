from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from .models import Bill, Receipt, Payment, TableTransfer
from orders.models import Order
from tables.models import Table
import json
from django.views.decorators.csrf import csrf_exempt

@login_required
def billing_dashboard(request):
    """Main dashboard for billing operations"""
    pending_bills = Bill.objects.filter(payment_status='pending').order_by('-created_at')
    paid_bills = Bill.objects.filter(payment_status='paid').order_by('-created_at')[:10]
    
    context = {
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
        'title': 'Billing Dashboard'
    }
    return render(request, 'billing/dashboard.html', context)

@login_required
def create_bill(request, table_id):
    """Create a bill for a table with all its active orders"""
    table = get_object_or_404(Table, id=table_id)
    active_orders = table.orders.filter(status__in=['pending', 'preparing', 'ready', 'served'])
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create the bill
                bill = Bill.objects.create(
                    table=table,
                    cashier=request.user,
                    customer_name=request.POST.get('customer_name', ''),
                    customer_phone=request.POST.get('customer_phone', ''),
                    special_requests=request.POST.get('special_requests', '')
                )
                
                # Add orders to the bill
                order_ids = request.POST.getlist('orders')
                orders = Order.objects.filter(id__in=order_ids)
                bill.orders.set(orders)
                
                # Calculate totals
                bill.calculate_totals()
                
                messages.success(request, f'Bill #{bill.id} created for Table {table.table_number}')
                return redirect('bill_detail', bill_id=bill.id)
                
        except Exception as e:
            messages.error(request, f'Error creating bill: {str(e)}')
    
    context = {
        'table': table,
        'active_orders': active_orders,
        'title': f'Create Bill - Table {table.table_number}'
    }
    return render(request, 'billing/create_bill.html', context)

@login_required
def bill_detail(request, bill_id):
    """Detailed view of a bill"""
    bill = get_object_or_404(Bill, id=bill_id)
    payments = bill.payments.all()
    
    context = {
        'bill': bill,
        'payments': payments,
        'title': f'Bill #{bill.id}'
    }
    return render(request, 'billing/bill_detail.html', context)

@login_required
@require_POST
def process_payment(request, bill_id):
    """Process a payment for a bill"""
    bill = get_object_or_404(Bill, id=bill_id)
    amount = request.POST.get('amount')
    payment_method = request.POST.get('payment_method')
    reference_number = request.POST.get('reference_number', '')
    notes = request.POST.get('notes', '')
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        with transaction.atomic():
            # Create payment record
            payment = Payment.objects.create(
                bill=bill,
                amount=amount,
                payment_method=payment_method,
                reference_number=reference_number,
                processed_by=request.user,
                notes=notes
            )
            
            # Update bill status if fully paid
            total_paid = sum(p.amount for p in bill.payments.all())
            if total_paid >= bill.total_amount:
                bill.payment_status = 'paid'
                bill.paid_at = timezone.now()
                bill.save()
                
                messages.success(request, f'Payment processed. Bill #{bill.id} is now fully paid.')
            else:
                messages.success(request, f'Payment of ${amount} processed. Remaining balance: ${bill.total_amount - total_paid}')
            
            return redirect('bill_detail', bill_id=bill.id)
            
    except ValueError as e:
        messages.error(request, f'Invalid amount: {str(e)}')
    except Exception as e:
        messages.error(request, f'Error processing payment: {str(e)}')
    
    return redirect('bill_detail', bill_id=bill.id)

@login_required
def print_receipt(request, bill_id):
    """Print a receipt for a paid bill"""
    bill = get_object_or_404(Bill, id=bill_id)
    
    if not bill.is_paid:
        messages.error(request, 'Cannot print receipt for unpaid bill')
        return redirect('bill_detail', bill_id=bill.id)
    
    if bill.receipt_printed:
        messages.warning(request, 'Receipt has already been printed')
        return redirect('bill_detail', bill_id=bill.id)
    
    try:
        with transaction.atomic():
            # Create receipt
            receipt_data = {
                'bill_id': bill.id,
                'table_number': bill.table.table_number,
                'customer_name': bill.customer_name,
                'customer_phone': bill.customer_phone,
                'subtotal': float(bill.subtotal),
                'tax_amount': float(bill.tax_amount),
                'discount_amount': float(bill.discount_amount),
                'total_amount': float(bill.total_amount),
                'payment_method': bill.payment_method,
                'items': []
            }
            
            # Add order items to receipt data
            for order in bill.orders.all():
                for order_item in order.order_items.all():
                    item_data = {
                        'name': order_item.item.name,
                        'quantity': order_item.quantity,
                        'unit_price': float(order_item.unit_price),
                        'total_price': float(order_item.total_price),
                        'toppings': order_item.toppings_list,
                        'cooking_preference': order_item.cooking_preference.name if order_item.cooking_preference else None
                    }
                    receipt_data['items'].append(item_data)
            
            receipt = Receipt.objects.create(
                bill=bill,
                printed_by=request.user,
                receipt_data=receipt_data
            )
            
            # Mark bill as receipt printed
            bill.receipt_printed = True
            bill.save()
            
            messages.success(request, f'Receipt #{receipt.receipt_number} printed successfully')
            
            # Clear the table
            table = bill.table
            table.status = 'available'
            table.current_occupancy = 0
            table.save()
            
            # Complete all orders
            for order in bill.orders.all():
                order.status = 'completed'
                order.save()
            
            return redirect('bill_detail', bill_id=bill.id)
            
    except Exception as e:
        messages.error(request, f'Error printing receipt: {str(e)}')
        return redirect('bill_detail', bill_id=bill.id)

@login_required
def receipt_detail(request, receipt_id):
    """View a receipt"""
    receipt = get_object_or_404(Receipt, id=receipt_id)
    
    context = {
        'receipt': receipt,
        'title': f'Receipt #{receipt.receipt_number}'
    }
    return render(request, 'billing/receipt_detail.html', context)

@login_required
def transfer_table(request, table_id):
    """Transfer orders from one table to another"""
    from_table = get_object_or_404(Table, id=table_id)
    available_tables = Table.objects.filter(is_active=True, status='available').exclude(id=table_id)
    active_orders = from_table.orders.filter(status__in=['pending', 'preparing', 'ready'])
    
    if request.method == 'POST':
        to_table_id = request.POST.get('to_table')
        reason = request.POST.get('reason', '')
        
        if to_table_id:
            to_table = get_object_or_404(Table, id=to_table_id)
            
            try:
                with transaction.atomic():
                    # Create transfer record
                    transfer = TableTransfer.objects.create(
                        from_table=from_table,
                        to_table=to_table,
                        transferred_by=request.user,
                        reason=reason
                    )
                    
                    # Transfer orders
                    transfer.orders.set(active_orders)
                    
                    # Update table statuses
                    from_table.status = 'available'
                    from_table.current_occupancy = 0
                    from_table.save()
                    
                    to_table.status = 'occupied'
                    to_table.save()
                    
                    messages.success(request, f'Orders transferred from Table {from_table.table_number} to Table {to_table.table_number}')
                    return redirect('table_detail', table_id=to_table.id)
                    
            except Exception as e:
                messages.error(request, f'Error transferring table: {str(e)}')
        else:
            messages.error(request, 'Please select a destination table')
    
    context = {
        'from_table': from_table,
        'available_tables': available_tables,
        'active_orders': active_orders,
        'title': f'Transfer Table {from_table.table_number}'
    }
    return render(request, 'billing/transfer_table.html', context)

@login_required
def bill_list(request):
    """List all bills with filtering options"""
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    bills = Bill.objects.all()
    
    if status_filter:
        bills = bills.filter(payment_status=status_filter)
    
    if date_filter:
        bills = bills.filter(created_at__date=date_filter)
    
    bills = bills.order_by('-created_at')
    
    context = {
        'bills': bills,
        'status_choices': Bill.PAYMENT_STATUS_CHOICES,
        'title': 'Bill List'
    }
    return render(request, 'billing/bill_list.html', context)

@login_required
def payment_history(request, bill_id):
    """View payment history for a bill"""
    bill = get_object_or_404(Bill, id=bill_id)
    payments = bill.payments.all().order_by('-processed_at')
    
    context = {
        'bill': bill,
        'payments': payments,
        'title': f'Payment History - Bill #{bill.id}'
    }
    return render(request, 'billing/payment_history.html', context)

@login_required
@csrf_exempt
def billing_api(request):
    """API endpoint for billing operations"""
    if request.method == 'GET':
        table_id = request.GET.get('table_id')
        if table_id:
            table = get_object_or_404(Table, id=table_id)
            active_orders = table.orders.filter(status__in=['pending', 'preparing', 'ready', 'served'])
            
            orders_data = []
            for order in active_orders:
                order_data = {
                    'id': order.id,
                    'total_amount': float(order.total_amount),
                    'items_count': order.order_items.count(),
                    'created_at': order.created_at.isoformat()
                }
                orders_data.append(order_data)
            
            return JsonResponse({'orders': orders_data})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

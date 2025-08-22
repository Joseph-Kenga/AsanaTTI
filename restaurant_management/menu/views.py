from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Category, Item, Size, Topping, CookingPreference

@login_required
def menu_dashboard(request):
    """Main dashboard for menu management"""
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    total_items = Item.objects.filter(is_available=True).count()
    
    context = {
        'categories': categories,
        'total_items': total_items,
        'title': 'Menu Dashboard'
    }
    return render(request, 'menu/dashboard.html', context)

@login_required
def category_list(request):
    """List all menu categories"""
    categories = Category.objects.all().order_by('display_order', 'name')
    
    context = {
        'categories': categories,
        'title': 'Menu Categories'
    }
    return render(request, 'menu/category_list.html', context)

@login_required
def item_list(request):
    """List all menu items with filtering"""
    category_filter = request.GET.get('category', '')
    item_type_filter = request.GET.get('type', '')
    
    items = Item.objects.all()
    
    if category_filter:
        items = items.filter(category_id=category_filter)
    
    if item_type_filter:
        items = items.filter(item_type=item_type_filter)
    
    items = items.order_by('category', 'name')
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'items': items,
        'categories': categories,
        'item_types': Item.ITEM_TYPE_CHOICES,
        'title': 'Menu Items'
    }
    return render(request, 'menu/item_list.html', context)

@login_required
def item_detail(request, item_id):
    """Detailed view of a menu item"""
    item = get_object_or_404(Item, id=item_id)
    available_sizes = item.available_sizes.filter(is_available=True)
    available_toppings = item.available_toppings.filter(is_available=True)
    available_cooking_preferences = item.available_cooking_preferences.filter(is_available=True)
    
    context = {
        'item': item,
        'available_sizes': available_sizes,
        'available_toppings': available_toppings,
        'available_cooking_preferences': available_cooking_preferences,
        'title': item.name
    }
    return render(request, 'menu/item_detail.html', context)

@login_required
@csrf_exempt
def menu_api(request):
    """API endpoint for menu data"""
    if request.method == 'GET':
        category_id = request.GET.get('category_id')
        item_type = request.GET.get('item_type')
        
        items = Item.objects.filter(is_available=True)
        
        if category_id:
            items = items.filter(category_id=category_id)
        
        if item_type:
            items = items.filter(item_type=item_type)
        
        items_data = []
        for item in items:
            item_data = {
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'base_price': float(item.base_price),
                'category': item.category.name,
                'item_type': item.item_type,
                'preparation_time': item.preparation_time,
                'sizes': [],
                'toppings': [],
                'cooking_preferences': []
            }
            
            # Add available sizes
            for item_size in item.available_sizes.filter(is_available=True):
                size_data = {
                    'id': item_size.size.id,
                    'name': item_size.size.name,
                    'price': float(item_size.price)
                }
                item_data['sizes'].append(size_data)
            
            # Add available toppings
            for item_topping in item.available_toppings.filter(is_available=True):
                topping_data = {
                    'id': item_topping.topping.id,
                    'name': item_topping.topping.name,
                    'price': float(item_topping.topping.price)
                }
                item_data['toppings'].append(topping_data)
            
            # Add available cooking preferences
            for item_cooking in item.available_cooking_preferences.filter(is_available=True):
                cooking_data = {
                    'id': item_cooking.cooking_preference.id,
                    'name': item_cooking.cooking_preference.name,
                    'description': item_cooking.cooking_preference.description
                }
                item_data['cooking_preferences'].append(cooking_data)
            
            items_data.append(item_data)
        
        return JsonResponse({'items': items_data})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

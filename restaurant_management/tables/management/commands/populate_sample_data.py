from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tables.models import Table
from menu.models import Category, Item, Size, Topping, CookingPreference, ItemSize, ItemTopping, ItemCookingPreference
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate the database with sample restaurant data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample tables
        self.create_tables()
        
        # Create menu categories
        self.create_categories()
        
        # Create menu items
        self.create_menu_items()
        
        # Create sizes, toppings, and cooking preferences
        self.create_customizations()
        
        # Link items with customizations
        self.link_customizations()
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))

    def create_tables(self):
        """Create sample tables"""
        tables_data = [
            {'table_number': 1, 'name': 'Window Table', 'capacity': 4},
            {'table_number': 2, 'name': 'Corner Table', 'capacity': 6},
            {'table_number': 3, 'name': 'Bar Table', 'capacity': 2},
            {'table_number': 4, 'name': 'Family Table', 'capacity': 8},
            {'table_number': 5, 'name': 'Romantic Table', 'capacity': 2},
            {'table_number': 6, 'name': 'Group Table', 'capacity': 10},
            {'table_number': 7, 'name': 'Outdoor Table', 'capacity': 4},
            {'table_number': 8, 'name': 'VIP Table', 'capacity': 6},
        ]
        
        for table_data in tables_data:
            Table.objects.get_or_create(
                table_number=table_data['table_number'],
                defaults=table_data
            )
        
        self.stdout.write(f'Created {len(tables_data)} tables')

    def create_categories(self):
        """Create menu categories"""
        categories_data = [
            {'name': 'Appetizers', 'description': 'Start your meal with our delicious appetizers'},
            {'name': 'Main Courses', 'description': 'Our signature main dishes'},
            {'name': 'Pizzas', 'description': 'Fresh-baked pizzas with premium toppings'},
            {'name': 'Burgers', 'description': 'Juicy burgers with fresh ingredients'},
            {'name': 'Salads', 'description': 'Fresh and healthy salad options'},
            {'name': 'Desserts', 'description': 'Sweet endings to your meal'},
            {'name': 'Beverages', 'description': 'Refreshing drinks and cocktails'},
            {'name': 'Coffee & Tea', 'description': 'Hot and cold coffee and tea selections'},
        ]
        
        for cat_data in categories_data:
            Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
        
        self.stdout.write(f'Created {len(categories_data)} categories')

    def create_menu_items(self):
        """Create sample menu items"""
        items_data = [
            # Appetizers
            {
                'name': 'Bruschetta',
                'description': 'Toasted bread topped with tomatoes, garlic, and basil',
                'category': 'Appetizers',
                'item_type': 'food',
                'base_price': Decimal('8.99'),
                'preparation_time': 10
            },
            {
                'name': 'Mozzarella Sticks',
                'description': 'Crispy breaded mozzarella served with marinara sauce',
                'category': 'Appetizers',
                'item_type': 'food',
                'base_price': Decimal('7.99'),
                'preparation_time': 8
            },
            
            # Main Courses
            {
                'name': 'Grilled Salmon',
                'description': 'Fresh Atlantic salmon grilled to perfection',
                'category': 'Main Courses',
                'item_type': 'food',
                'base_price': Decimal('24.99'),
                'preparation_time': 20
            },
            {
                'name': 'Beef Tenderloin',
                'description': 'Premium cut beef tenderloin with herb butter',
                'category': 'Main Courses',
                'item_type': 'food',
                'base_price': Decimal('29.99'),
                'preparation_time': 25
            },
            
            # Pizzas
            {
                'name': 'Margherita Pizza',
                'description': 'Classic pizza with tomato sauce, mozzarella, and basil',
                'category': 'Pizzas',
                'item_type': 'food',
                'base_price': Decimal('16.99'),
                'preparation_time': 15
            },
            {
                'name': 'Pepperoni Pizza',
                'description': 'Pizza topped with pepperoni, mozzarella, and tomato sauce',
                'category': 'Pizzas',
                'item_type': 'food',
                'base_price': Decimal('18.99'),
                'preparation_time': 15
            },
            
            # Burgers
            {
                'name': 'Classic Burger',
                'description': 'Beef patty with lettuce, tomato, and special sauce',
                'category': 'Burgers',
                'item_type': 'food',
                'base_price': Decimal('14.99'),
                'preparation_time': 12
            },
            {
                'name': 'Chicken Burger',
                'description': 'Grilled chicken breast with avocado and chipotle mayo',
                'category': 'Burgers',
                'item_type': 'food',
                'base_price': Decimal('13.99'),
                'preparation_time': 12
            },
            
            # Salads
            {
                'name': 'Caesar Salad',
                'description': 'Romaine lettuce, parmesan cheese, croutons, and caesar dressing',
                'category': 'Salads',
                'item_type': 'food',
                'base_price': Decimal('12.99'),
                'preparation_time': 8
            },
            {
                'name': 'Greek Salad',
                'description': 'Mixed greens, feta cheese, olives, and greek dressing',
                'category': 'Salads',
                'item_type': 'food',
                'base_price': Decimal('11.99'),
                'preparation_time': 8
            },
            
            # Desserts
            {
                'name': 'Chocolate Cake',
                'description': 'Rich chocolate cake with chocolate ganache',
                'category': 'Desserts',
                'item_type': 'dessert',
                'base_price': Decimal('8.99'),
                'preparation_time': 5
            },
            {
                'name': 'Tiramisu',
                'description': 'Classic Italian dessert with coffee and mascarpone',
                'category': 'Desserts',
                'item_type': 'dessert',
                'base_price': Decimal('9.99'),
                'preparation_time': 5
            },
            
            # Beverages
            {
                'name': 'Coca Cola',
                'description': 'Classic Coca Cola soft drink',
                'category': 'Beverages',
                'item_type': 'drink',
                'base_price': Decimal('3.99'),
                'preparation_time': 2
            },
            {
                'name': 'Orange Juice',
                'description': 'Fresh squeezed orange juice',
                'category': 'Beverages',
                'item_type': 'drink',
                'base_price': Decimal('4.99'),
                'preparation_time': 3
            },
            {
                'name': 'Beer',
                'description': 'Local craft beer selection',
                'category': 'Beverages',
                'item_type': 'drink',
                'base_price': Decimal('6.99'),
                'preparation_time': 2
            },
            
            # Coffee & Tea
            {
                'name': 'Espresso',
                'description': 'Single shot of premium espresso',
                'category': 'Coffee & Tea',
                'item_type': 'drink',
                'base_price': Decimal('3.99'),
                'preparation_time': 3
            },
            {
                'name': 'Cappuccino',
                'description': 'Espresso with steamed milk and foam',
                'category': 'Coffee & Tea',
                'item_type': 'drink',
                'base_price': Decimal('4.99'),
                'preparation_time': 5
            },
        ]
        
        for item_data in items_data:
            category = Category.objects.get(name=item_data['category'])
            Item.objects.get_or_create(
                name=item_data['name'],
                defaults={
                    'description': item_data['description'],
                    'category': category,
                    'item_type': item_data['item_type'],
                    'base_price': item_data['base_price'],
                    'preparation_time': item_data['preparation_time']
                }
            )
        
        self.stdout.write(f'Created {len(items_data)} menu items')

    def create_customizations(self):
        """Create sizes, toppings, and cooking preferences"""
        
        # Sizes
        sizes_data = [
            {'name': 'Small', 'price_modifier': Decimal('0.00')},
            {'name': 'Medium', 'price_modifier': Decimal('2.00')},
            {'name': 'Large', 'price_modifier': Decimal('4.00')},
        ]
        
        for size_data in sizes_data:
            Size.objects.get_or_create(
                name=size_data['name'],
                defaults=size_data
            )
        
        # Toppings
        toppings_data = [
            {'name': 'Extra Cheese', 'price': Decimal('1.50')},
            {'name': 'Mushrooms', 'price': Decimal('1.00')},
            {'name': 'Pepperoni', 'price': Decimal('2.00')},
            {'name': 'Bacon', 'price': Decimal('2.50')},
            {'name': 'Olives', 'price': Decimal('1.00')},
            {'name': 'Bell Peppers', 'price': Decimal('1.00')},
            {'name': 'Onions', 'price': Decimal('0.50')},
            {'name': 'Jalapeños', 'price': Decimal('1.00')},
        ]
        
        for topping_data in toppings_data:
            Topping.objects.get_or_create(
                name=topping_data['name'],
                defaults=topping_data
            )
        
        # Cooking Preferences
        cooking_preferences_data = [
            {'name': 'Rare', 'description': 'Red center, cool'},
            {'name': 'Medium Rare', 'description': 'Red center, warm'},
            {'name': 'Medium', 'description': 'Pink center, warm'},
            {'name': 'Medium Well', 'description': 'Slightly pink center'},
            {'name': 'Well Done', 'description': 'No pink, fully cooked'},
        ]
        
        for cooking_data in cooking_preferences_data:
            CookingPreference.objects.get_or_create(
                name=cooking_data['name'],
                defaults=cooking_data
            )
        
        self.stdout.write(f'Created {len(sizes_data)} sizes, {len(toppings_data)} toppings, and {len(cooking_preferences_data)} cooking preferences')

    def link_customizations(self):
        """Link items with their available customizations"""
        
        # Link pizza items with sizes and toppings
        pizza_items = Item.objects.filter(category__name='Pizzas')
        sizes = Size.objects.all()
        toppings = Topping.objects.all()
        
        for pizza in pizza_items:
            # Add sizes
            for size in sizes:
                price = pizza.base_price + size.price_modifier
                ItemSize.objects.get_or_create(
                    item=pizza,
                    size=size,
                    defaults={'price': price}
                )
            
            # Add toppings
            for topping in toppings:
                ItemTopping.objects.get_or_create(
                    item=pizza,
                    topping=topping
                )
        
        # Link burger items with cooking preferences
        burger_items = Item.objects.filter(category__name='Burgers')
        cooking_preferences = CookingPreference.objects.all()
        
        for burger in burger_items:
            for cooking in cooking_preferences:
                ItemCookingPreference.objects.get_or_create(
                    item=burger,
                    cooking_preference=cooking
                )
        
        # Link main course items with cooking preferences
        main_courses = Item.objects.filter(category__name='Main Courses')
        
        for main_course in main_courses:
            for cooking in cooking_preferences:
                ItemCookingPreference.objects.get_or_create(
                    item=main_course,
                    cooking_preference=cooking
                )
        
        # Link beverage items with sizes
        beverage_items = Item.objects.filter(item_type='drink')
        
        for beverage in beverage_items:
            for size in sizes:
                price = beverage.base_price + size.price_modifier
                ItemSize.objects.get_or_create(
                    item=beverage,
                    size=size,
                    defaults={'price': price}
                )
        
        self.stdout.write('Linked items with customizations')
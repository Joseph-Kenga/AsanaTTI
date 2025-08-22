# Restaurant Management System

A comprehensive multi-vendor restaurant management system built with Django that handles table management, order processing, kitchen/bar workflows, and billing operations.

## Features

### 🍽️ Table Management
- **Dynamic Table Creation**: Add tables with custom names and capacities
- **Real-time Status Tracking**: Monitor table availability, occupancy, and status
- **Visual Status Indicators**: Color-coded table status (Available, Occupied, Reserved, Cleaning)
- **Occupancy Management**: Track how many people are seated at each table
- **Table Transfers**: Move orders between tables seamlessly

### 📋 Order Management
- **Multi-item Orders**: Create orders with multiple items, quantities, and customizations
- **Size Options**: Different sizes with price variations (Small, Medium, Large)
- **Toppings System**: Add toppings to items with additional pricing
- **Cooking Preferences**: Specify cooking preferences for food items (Rare, Medium, Well Done)
- **Order Status Workflow**: Track orders from Pending → Preparing → Ready → Served → Completed
- **Kitchen/Bar Separation**: Automatic routing of food orders to kitchen and drink orders to bar
- **Order Modifications**: Add items to existing orders or modify quantities

### 🍳 Kitchen & Bar Workflows
- **Dedicated Views**: Separate interfaces for kitchen and bar staff
- **Real-time Updates**: Live order status updates
- **Preparation Time Tracking**: Monitor preparation times for each item
- **Order Prioritization**: View orders by creation time and status

### 💰 Billing & Payment
- **Bill Generation**: Create bills for tables with multiple orders
- **Payment Processing**: Support for cash, card, and mobile money payments
- **Receipt Generation**: Print detailed receipts with itemized breakdowns
- **Tax Calculation**: Automatic tax calculation (10% default)
- **Discount Support**: Apply discounts to bills
- **Payment History**: Track all payment transactions

### 📖 Menu Management
- **Category Organization**: Organize items by categories (Appetizers, Main Courses, etc.)
- **Item Customization**: Define sizes, toppings, and cooking preferences per item
- **Price Management**: Set base prices and size modifiers
- **Availability Control**: Mark items as available/unavailable
- **Preparation Time**: Set preparation times for each item

### 👥 User Management
- **Role-based Access**: Different interfaces for waiters, kitchen staff, bar staff, and cashiers
- **User Authentication**: Secure login system
- **Activity Tracking**: Track who created orders, processed payments, etc.

## System Architecture

### Apps Structure
- **tables**: Table management and status tracking
- **menu**: Menu items, categories, and customizations
- **orders**: Order creation, management, and workflow
- **billing**: Payment processing, receipt generation, and financial tracking

### Database Models

#### Tables App
- `Table`: Restaurant tables with capacity and status tracking

#### Menu App
- `Category`: Menu categories (Appetizers, Main Courses, etc.)
- `Item`: Menu items with pricing and preparation details
- `Size`: Size options (Small, Medium, Large)
- `Topping`: Available toppings with pricing
- `CookingPreference`: Cooking preferences (Rare, Medium, Well Done)
- `ItemSize`, `ItemTopping`, `ItemCookingPreference`: Junction tables for item customizations

#### Orders App
- `Order`: Main order entity with status tracking
- `OrderItem`: Individual items in orders with customizations
- `OrderItemTopping`: Toppings applied to order items
- `OrderStatusHistory`: Complete audit trail of order status changes

#### Billing App
- `Bill`: Bill entity with payment status and totals
- `Payment`: Individual payment transactions
- `Receipt`: Receipt generation and storage
- `TableTransfer`: Track table transfers between orders

## Installation & Setup

### Prerequisites
- Python 3.8+
- Django 5.2+
- Pillow (for image handling)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd restaurant_management
   ```

2. **Install dependencies**
   ```bash
   pip install django pillow
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Populate sample data**
   ```bash
   python manage.py populate_sample_data
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the system**
   - Main application: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

## Usage Guide

### For Waiters
1. **View Tables**: Check table dashboard for available tables
2. **Create Orders**: Click "Create Order" on available tables
3. **Add Items**: Select items, sizes, toppings, and cooking preferences
4. **Modify Orders**: Add items to existing orders or change quantities
5. **Monitor Status**: Track order progress through the system

### For Kitchen Staff
1. **Access Kitchen View**: Navigate to Kitchen dashboard
2. **View Pending Orders**: See all food orders waiting to be prepared
3. **Update Status**: Mark orders as "Preparing" then "Ready"
4. **Monitor Preparation Times**: Ensure timely order completion

### For Bar Staff
1. **Access Bar View**: Navigate to Bar dashboard
2. **View Drink Orders**: See all beverage orders
3. **Process Orders**: Prepare and mark drinks as ready
4. **Track Inventory**: Monitor drink preparation

### For Cashiers
1. **Create Bills**: Generate bills for tables with completed orders
2. **Process Payments**: Accept payments through various methods
3. **Generate Receipts**: Print detailed receipts for customers
4. **Transfer Tables**: Move orders between tables if needed
5. **Clear Tables**: Mark tables as available after payment

### For Managers
1. **Admin Interface**: Access Django admin for system management
2. **Menu Management**: Add/edit menu items, categories, and pricing
3. **Table Management**: Configure table layouts and capacities
4. **User Management**: Manage staff accounts and permissions
5. **Reports**: View financial reports and order analytics

## API Endpoints

### Tables API
- `GET /api/tables/status/`: Get real-time table status

### Orders API
- `GET /api/orders/status/`: Get order status updates
- `GET /api/orders/status/?type=kitchen`: Get kitchen orders
- `GET /api/orders/status/?type=bar`: Get bar orders

### Menu API
- `GET /api/menu/items/`: Get menu items
- `GET /api/menu/items/?category_id=1`: Get items by category
- `GET /api/menu/items/?item_type=food`: Get items by type

### Billing API
- `GET /api/billing/?table_id=1`: Get table billing information

## Configuration

### Settings
- **Database**: SQLite by default (can be changed to PostgreSQL/MySQL)
- **Static Files**: Configured for development and production
- **Media Files**: Image uploads for menu items
- **Tax Rate**: 10% default (configurable in billing models)

### Customization
- **Tax Rate**: Modify in `billing/models.py` Bill.calculate_totals()
- **Order Statuses**: Add/modify in `orders/models.py` Order.ORDER_STATUS_CHOICES
- **Payment Methods**: Extend in `billing/models.py` Bill.PAYMENT_METHOD_CHOICES
- **Table Statuses**: Modify in `tables/models.py` Table.TABLE_STATUS_CHOICES

## Security Features

- **Authentication Required**: All views require login
- **CSRF Protection**: Enabled on all forms
- **SQL Injection Protection**: Django ORM provides protection
- **XSS Protection**: Template escaping and sanitization
- **Permission-based Access**: Different interfaces for different roles

## Performance Optimizations

- **Database Indexing**: Optimized queries with proper indexing
- **Caching**: Template caching and query optimization
- **Real-time Updates**: AJAX-based status updates
- **Lazy Loading**: Efficient loading of related data

## Deployment

### Production Setup
1. **Set DEBUG=False** in settings
2. **Configure database** (PostgreSQL recommended)
3. **Set up static file serving** (nginx/Apache)
4. **Configure media file storage**
5. **Set up SSL certificate**
6. **Configure backup strategy**

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:pass@host:port/db
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Roadmap

### Future Features
- **Inventory Management**: Track ingredient levels and automatic reordering
- **Customer Management**: Customer profiles and loyalty programs
- **Reservation System**: Table reservations and booking management
- **Mobile App**: Native mobile applications for staff
- **Analytics Dashboard**: Advanced reporting and analytics
- **Multi-location Support**: Manage multiple restaurant locations
- **Integration APIs**: Third-party integrations (delivery, POS, etc.)
- **Real-time Notifications**: Push notifications for order updates
- **Advanced Reporting**: Financial reports, sales analytics, staff performance
- **Menu Planning**: Seasonal menus and special promotions

---

**Built with ❤️ using Django**
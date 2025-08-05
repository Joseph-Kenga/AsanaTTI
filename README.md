# 🏦 SACCO Lending System

A comprehensive Django-based loan management system designed specifically for **Jackline Kayanda SACCO** by **Tubanje Technologies Ltd**.

## 📋 Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [User Roles](#user-roles)
- [Database Schema](#database-schema)
- [Deployment](#deployment)
- [Support](#support)

## ✨ Features

### 👥 Member Management
- **Complete member registration** with comprehensive profile management
- **Document management** (ID copies, payslips, bank statements, etc.)
- **Next of kin** and **guarantor** information tracking
- **Member activity logs** and interaction history
- **Photo upload** with automatic resizing
- **Member status management** (Active, Inactive, Suspended, Blacklisted)

### 💰 Loan Management
- **Multiple loan types** with flexible configuration
- **Interest calculation methods**: Flat rate, Reducing balance, Compound
- **Loan application workflow**: Draft → Submitted → Under Review → Approved/Rejected → Disbursed
- **Guarantor and collateral management**
- **Loan top-ups and restructuring**
- **Document attachment** for applications and active loans
- **Automatic loan numbering** and tracking

### 💳 Repayment System
- **Automated repayment schedules** generation
- **Flexible payment processing** (Cash, Bank Transfer, Mobile Money, M-Pesa)
- **Penalty calculations** for overdue payments
- **Early repayment** with settlement calculations
- **Payment allocation** (Penalties → Interest → Principal)
- **Repayment reminders** via SMS/Email

### 📊 Reports & Analytics
- **Comprehensive reporting system** with PDF/Excel export
- **Scheduled reports** with automatic generation
- **Interactive dashboards** with customizable widgets
- **KPI metrics** and performance tracking
- **Report templates** for different user roles
- **Data visualization** with charts and graphs

### 📱 Notifications
- **Multi-channel notifications** (SMS, Email, In-app)
- **Automated notification rules** based on events
- **Bulk messaging** capabilities
- **Notification templates** with dynamic content
- **Delivery tracking** and response monitoring
- **SMS provider integration** (Africa's Talking, Twilio, etc.)

### 🔐 Security & Access Control
- **Role-based permissions** (Admin, Accountant, Loan Officer, Member)
- **User activity logging** and audit trails
- **Session management** with timeout control
- **Password reset** functionality
- **Two-factor authentication** ready

## 🏗️ System Architecture

The system is built using Django with a modular architecture:

```
sacco_lending_system/
├── members/           # Member management
├── loans/             # Loan processing
├── repayments/        # Repayment tracking
├── reports/           # Reporting system
├── notifications/     # Communication system
├── static/            # Static files (CSS, JS, Images)
├── media/             # Uploaded files
├── templates/         # HTML templates
└── logs/              # Application logs
```

## 🚀 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (optional, uses SQLite by default)
- Redis (for notifications and caching)

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd sacco_lending_system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Start development server**
```bash
python manage.py runserver
```

7. **Access the system**
- Home page: http://localhost:8000/
- Admin panel: http://localhost:8000/admin/

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# SACCO Configuration
COMPANY_NAME=Jackline Kayanda SACCO
DEFAULT_INTEREST_RATE=10.0
DEFAULT_LOAN_TERM_MONTHS=12
PENALTY_RATE=5.0
MINIMUM_LOAN_AMOUNT=1000.0
MAXIMUM_LOAN_AMOUNT=500000.0
CURRENCY=KES

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@sacco.com

# SMS Configuration
SMS_PROVIDER=africastalking
SMS_API_KEY=your-sms-api-key

# M-Pesa Configuration
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_SHORTCODE=your-shortcode
```

### Database Configuration

For PostgreSQL (recommended for production):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sacco_db',
        'USER': 'sacco_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📖 Usage

### Admin Interface

The Django admin interface provides comprehensive management capabilities:

1. **Access**: http://localhost:8000/admin/
2. **Login** with superuser credentials
3. **Navigate** through different modules:
   - **Members**: Manage member profiles, documents, activities
   - **Loans**: Process applications, manage active loans
   - **Repayments**: Track payments, manage schedules
   - **Reports**: Generate and schedule reports
   - **Notifications**: Manage templates and campaigns

### Key Workflows

#### 1. Member Registration
1. Create User account with 'member' role
2. Create Member profile with personal details
3. Add Next of Kin information
4. Upload required documents
5. Assign to Loan Officer (optional)

#### 2. Loan Application Process
1. Member submits loan application
2. Loan Officer reviews and assigns guarantors
3. Application moves through approval workflow
4. Upon approval, loan is disbursed
5. Repayment schedule is automatically generated

#### 3. Repayment Processing
1. Payments are recorded in the system
2. Amounts are allocated to schedules automatically
3. Overdue payments trigger penalty calculations
4. Reminders are sent based on notification rules

## 🔌 API Documentation

The system includes REST API endpoints for integration:

- **Members API**: `/api/members/`
- **Loans API**: `/api/loans/`
- **Repayments API**: `/api/repayments/`
- **Reports API**: `/api/reports/`
- **Notifications API**: `/api/notifications/`

*Note: API implementation is planned for future phases*

## 👤 User Roles

### Administrator
- Full system access
- User management
- System configuration
- All reports and analytics

### Accountant  
- Financial data access
- Payment processing
- Financial reports
- Audit trails

### Loan Officer
- Assigned member management
- Loan application processing
- Repayment tracking
- Client communication

### Member
- Personal profile management
- Loan application submission
- Repayment history viewing
- Document uploads

## 🗄️ Database Schema

### Core Models

#### Members App
- **User**: Extended Django user with roles
- **Member**: Comprehensive member profiles
- **NextOfKin**: Emergency contacts
- **Guarantor**: Loan guarantors with collateral
- **MemberDocument**: Document management
- **MemberActivity**: Activity tracking

#### Loans App
- **LoanType**: Configurable loan products
- **LoanApplication**: Application workflow
- **Loan**: Active loan management
- **LoanGuarantor**: Guarantor assignments
- **LoanDocument**: Loan documentation
- **LoanTopUp**: Loan restructuring

#### Repayments App
- **RepaymentSchedule**: Payment schedules
- **RepaymentTransaction**: Payment records
- **PenaltyTransaction**: Penalty tracking
- **RepaymentReminder**: Communication logs
- **EarlyRepayment**: Settlement calculations

#### Reports App
- **ReportTemplate**: Report definitions
- **Report**: Generated reports
- **Dashboard**: Custom dashboards
- **KPIMetric**: Performance metrics

#### Notifications App
- **NotificationTemplate**: Message templates
- **Notification**: Individual messages
- **BulkNotification**: Mass communications
- **SMSProvider**: SMS service configuration

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
```bash
# Install production dependencies
pip install gunicorn psycopg2-binary

# Collect static files
python manage.py collectstatic

# Run migrations
python manage.py migrate
```

2. **Gunicorn Configuration**
```bash
gunicorn sacco_lending_system.wsgi:application --bind 0.0.0.0:8000
```

3. **Nginx Configuration** (recommended)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "sacco_lending_system.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 📞 Support

### System Requirements Covered

✅ **Member Management**: Complete profile and document system  
✅ **Loan Processing**: Multi-type loans with flexible terms  
✅ **Repayment Tracking**: Automated schedules and penalties  
✅ **Reporting System**: PDF/Excel exports with scheduling  
✅ **Notification System**: SMS/Email with templates  
✅ **Role-based Access**: Admin, Accountant, Loan Officer, Member  
✅ **Dashboard & KPIs**: Real-time metrics and analytics  
✅ **Audit Trails**: Complete activity logging  
✅ **Document Management**: Upload and categorization  
✅ **Integration Ready**: M-Pesa and external APIs  

### Future Enhancements

🔄 **Savings Module**: Member savings accounts  
🔄 **Insurance Module**: Loan protection insurance  
🔄 **Mobile App**: Native mobile applications  
🔄 **Investment Module**: Investment products  
🔄 **Advanced Analytics**: Machine learning insights  

### Technical Support

For technical support and customization:

- **Developer**: Tubanje Technologies Ltd
- **Client**: Jackline Kayanda SACCO  
- **Project Date**: July 2025

### Training & Documentation

- **User Manuals**: Available in `/docs/` directory
- **Video Tutorials**: Training materials provided
- **System Training**: On-site training available
- **Technical Support**: 6 months included

---

**© 2025 Tubanje Technologies Ltd. All rights reserved.**
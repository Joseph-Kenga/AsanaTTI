"""
URL configuration for sacco_lending_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import HttpResponse

def home_view(request):
    """Simple home page view"""
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SACCO Lending System</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                text-align: center; 
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 10px;
                backdrop-filter: blur(10px);
            }
            h1 { color: white; margin-bottom: 30px; }
            .features { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; 
                margin: 30px 0; 
            }
            .feature { 
                background: rgba(255,255,255,0.1); 
                padding: 20px; 
                border-radius: 8px; 
                border: 1px solid rgba(255,255,255,0.2);
            }
            .btn { 
                display: inline-block; 
                padding: 12px 24px; 
                background: #4CAF50; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px; 
                margin: 10px;
                transition: background 0.3s;
            }
            .btn:hover { background: #45a049; }
            .btn-secondary { background: #2196F3; }
            .btn-secondary:hover { background: #1976D2; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏦 SACCO Lending System</h1>
            <p><strong>Prepared for:</strong> Jackline Kayanda SACCO</p>
            <p><strong>Developed by:</strong> Tubanje Technologies Ltd</p>
            
            <div class="features">
                <div class="feature">
                    <h3>👥 Member Management</h3>
                    <p>Complete member registration, profiles, and document management</p>
                </div>
                <div class="feature">
                    <h3>💰 Loan Processing</h3>
                    <p>Application, approval, disbursement, and tracking system</p>
                </div>
                <div class="feature">
                    <h3>💳 Repayment Tracking</h3>
                    <p>Automated schedules, penalty calculations, and payment processing</p>
                </div>
                <div class="feature">
                    <h3>📊 Reports & Analytics</h3>
                    <p>Comprehensive reporting with PDF/Excel export capabilities</p>
                </div>
                <div class="feature">
                    <h3>📱 Notifications</h3>
                    <p>SMS/Email reminders and automated communication system</p>
                </div>
                <div class="feature">
                    <h3>📈 Dashboard & KPIs</h3>
                    <p>Real-time performance metrics and business intelligence</p>
                </div>
            </div>
            
            <div style="margin-top: 30px;">
                <a href="/admin/" class="btn">🔧 Admin Panel</a>
                <a href="/api/" class="btn btn-secondary">🔌 API Documentation</a>
            </div>
            
            <div style="margin-top: 40px; font-size: 14px; opacity: 0.8;">
                <p>System Features Include:</p>
                <p>✅ Role-based access control (Admin, Accountant, Loan Officer, Member)<br>
                ✅ Multi-loan type support with flexible interest calculations<br>
                ✅ Guarantor and collateral management<br>
                ✅ Automated penalty calculations and overdue tracking<br>
                ✅ Member self-service portal<br>
                ✅ M-Pesa integration ready<br>
                ✅ Comprehensive audit trails</p>
            </div>
        </div>
    </body>
    </html>
    """)

urlpatterns = [
    # Home page
    path('', home_view, name='home'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints (to be implemented)
    path('api/', include([
        # path('members/', include('members.urls')),
        # path('loans/', include('loans.urls')),
        # path('repayments/', include('repayments.urls')),
        # path('reports/', include('reports.urls')),
        # path('notifications/', include('notifications.urls')),
    ])),
    
    # Member portal (to be implemented)
    # path('portal/', include('portal.urls')),
    
    # Staff dashboard (to be implemented)  
    # path('dashboard/', include('dashboard.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Add debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

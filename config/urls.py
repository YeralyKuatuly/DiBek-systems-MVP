"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib import admin


schema_view = get_schema_view(
   openapi.Info(
      title="DiBek API",
      default_version='v1',
      description="API documentation for DiBek MVP",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register('companies', views.CompanyViewSet)
router.register('items', views.ItemViewSet)
router.register('cart', views.CartViewSet, basename='cart')
router.register('orders', views.OrderRequestViewSet)
router.register('payments', views.PaymentViewSet, basename='payment')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),
    path('api/auth/token/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('api/auth/signup/', views.SignUpView.as_view(), name='signup'),
    path('api/', include(router.urls)),
]

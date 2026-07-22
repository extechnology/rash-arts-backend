from django.urls import path, include

urlpatterns = [
    path('auth/', include('Application.Authentication.auth_urls'))
]
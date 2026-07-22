"""
URL configuration for courmanbackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from ninja import NinjaAPI

from courses.views import api as courses_api
from grading.views import api as grading_api
from iam.views import api as iam_api
from profiles.views import api as profiles_api

api = NinjaAPI(title="Courman API", version="1.0.0")
api.add_router("/iam/", iam_api)
api.add_router("/profiles/", profiles_api)
api.add_router("/courses/", courses_api)
api.add_router("/grading/", grading_api)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]

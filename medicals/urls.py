from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # Add this line

urlpatterns = [
    path('admin/', admin.site.urls),
    path('records/', include('records.urls')),
    path('', RedirectView.as_view(url='/records/patients/', permanent=True)),  # This line does the redirection
]

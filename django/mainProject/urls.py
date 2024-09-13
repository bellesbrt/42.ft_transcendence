from django.urls import path, include
from django.contrib import admin

# URL patterns
urlpatterns = [
	path('admin/', admin.site.urls),
	path('', include('mainApp.urls')),
]

# Error handling
handler404 = 'mainApp.views.mainView.custom404'
handler405 = 'mainApp.views.mainView.custom405'
handler500 = 'mainApp.views.mainView.custom500'

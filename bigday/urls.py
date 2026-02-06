from django.contrib import admin     # 👈 importa o admin
from django.urls import path, include
from . import views

urlpatterns = [
    # Rota do painel de administração
    path('admin/', admin.site.urls),  # 👈 adiciona o admin

    # Rotas principais do seu site
    path('', views.home_view, name='home'),
    path('presentes/', views.all_gifts_view, name='all_gifts'),
    path('create_preference/', views.create_preference, name='create_preference'),
    path("pagamento/sucesso/", views.payment_success, name="payment_success"),

    # Inclui as rotas do app "guests" (convites, rsvp, dashboard etc.)
    path('', include('guests.urls')),  # 👈 adiciona isso também
]

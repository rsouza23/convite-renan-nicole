from __future__ import unicode_literals
import datetime
import uuid
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _  # 👈 para suportar traduções

# tipos de convite
ALLOWED_TYPES = [
    ('formal', 'Formal'),
    ('fun', 'Divertido'),
    ('dimagi', 'Dimagi'),
]


def _random_uuid():
    return uuid.uuid4().hex


class Party(models.Model):
    """
    Uma festa ou grupo de convidados.
    """
    name = models.TextField(verbose_name="Nome do grupo ou família")
    type = models.CharField(max_length=10, choices=ALLOWED_TYPES, verbose_name="Tipo de convite")
    category = models.CharField(max_length=20, null=True, blank=True, verbose_name="Categoria")
    save_the_date_sent = models.DateTimeField(null=True, blank=True, default=None, verbose_name="Save the date enviado")
    save_the_date_opened = models.DateTimeField(null=True, blank=True, default=None, verbose_name="Save the date aberto")
    invitation_id = models.CharField(max_length=32, db_index=True, default=_random_uuid, unique=True, verbose_name="Código do convite")
    invitation_sent = models.DateTimeField(null=True, blank=True, default=None, verbose_name="Convite enviado")
    invitation_opened = models.DateTimeField(null=True, blank=True, default=None, verbose_name="Convite aberto")
    is_invited = models.BooleanField(default=False, verbose_name="Foi convidado?")
    rehearsal_dinner = models.BooleanField(default=False, verbose_name="Jantar de ensaio")
    is_attending = models.BooleanField(default=None, null=True, verbose_name="Vai comparecer?")
    comments = models.TextField(null=True, blank=True, verbose_name="Comentários")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Festa"
        verbose_name_plural = "Festas"
        ordering = ['category', 'name']

    @classmethod
    def in_default_order(cls):
        return cls.objects.order_by('category', '-is_invited', 'name')

    @property
    def ordered_guests(self):
        return self.guest_set.order_by('is_child', 'pk')

    @property
    def any_guests_attending(self):
        return any(self.guest_set.values_list('is_attending', flat=True))

    @property
    def guest_emails(self):
        return list(filter(None, self.guest_set.values_list('email', flat=True)))


MEALS = [
    ('beef', 'Carne vermelha'),
    ('fish', 'Peixe'),
    ('hen', 'Frango'),
    ('vegetarian', 'Vegetariano'),
]


class Guest(models.Model):
    """
    Um convidado individual.
    """
    party = models.ForeignKey('Party', on_delete=models.CASCADE, verbose_name="Festa / Grupo")
    first_name = models.TextField(verbose_name="Nome")
    last_name = models.TextField(null=True, blank=True, verbose_name="Sobrenome")
    email = models.TextField(null=True, blank=True, verbose_name="E-mail")
    is_attending = models.BooleanField(default=None, null=True, verbose_name="Vai comparecer?")
    meal = models.CharField(max_length=20, choices=MEALS, null=True, blank=True, verbose_name="Refeição")
    is_child = models.BooleanField(default=False, verbose_name="É criança?")

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def unique_id(self):
        # usado em templates
        return str(self.pk)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Convidado"
        verbose_name_plural = "Convidados"
        ordering = ['first_name']
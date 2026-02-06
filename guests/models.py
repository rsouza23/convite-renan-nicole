from __future__ import unicode_literals
import uuid
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _  # suporte a traduções


# --- Tipos de convite ---
ALLOWED_TYPES = [
    ('formal', 'Formal'),
    ('fun', 'Divertido'),
    ('dimagi', 'Dimagi'),
]


def _random_uuid():
    return uuid.uuid4().hex


# --- Modelo de Grupo/Família ---
class Party(models.Model):
    """
    Representa um grupo ou família convidada.
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Nome do grupo ou família"
    )
    type = models.CharField(
        max_length=10,
        choices=ALLOWED_TYPES,
        verbose_name="Tipo de convite"
    )
    category = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Categoria"
    )

    save_the_date_sent = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Save the date enviado"
    )
    save_the_date_opened = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Save the date aberto"
    )

    invitation_id = models.CharField(
        max_length=32,
        db_index=True,
        default=_random_uuid,
        unique=True,
        verbose_name="Código do convite"
    )

    invitation_sent = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Convite enviado"
    )
    invitation_opened = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Convite aberto"
    )

    is_invited = models.BooleanField(default=False, verbose_name="Convite enviado?")
    rehearsal_dinner = models.BooleanField(default=False, verbose_name="Jantar de ensaio")
    is_attending = models.BooleanField(default=None, null=True, verbose_name="Vai comparecer?")
    comments = models.TextField(null=True, blank=True, verbose_name="Comentários")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Grupo/Família"
        verbose_name_plural = "Grupos/Famílias"
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
    def guest_contacts(self):
        """Lista de contatos (WhatsApp) dos convidados."""
        return list(filter(None, self.guest_set.values_list('contact', flat=True)))

    @property
    def total_accesses(self):
        """Retorna o número total de acessos registrados para este grupo."""
        return self.inviteaccesslog_set.count()


# --- Modelo de Convidado ---
class Guest(models.Model):
    """
    Um convidado individual.
    """
    party = models.ForeignKey('Party', on_delete=models.CASCADE, verbose_name="Grupo/Família")
    first_name = models.CharField(max_length=60, verbose_name="Nome")
    last_name = models.CharField(max_length=60, null=True, blank=True, verbose_name="Sobrenome")

    contact = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Contato (WhatsApp)"
    )

    is_attending = models.BooleanField(default=None, null=True, verbose_name="Vai comparecer?")
    is_child = models.BooleanField(default=False, verbose_name="É criança?")

    @property
    def name(self):
        return f"{self.first_name} {self.last_name or ''}".strip()

    @property
    def unique_id(self):
        """Retorna o ID único do convidado, usado nos formulários do RSVP."""
        return str(self.pk)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Convidado"
        verbose_name_plural = "Convidados"
        ordering = ['first_name']


# --- Modelo de Rastreabilidade (acessos ao convite) ---
class InviteAccessLog(models.Model):
    """
    Registra cada vez que um convite é acessado (para rastreabilidade).
    """
    party = models.ForeignKey('Party', on_delete=models.CASCADE, verbose_name="Grupo/Família")
    accessed_at = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora do acesso")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Endereço IP")
    user_agent = models.TextField(null=True, blank=True, verbose_name="Navegador / Dispositivo")

    def __str__(self):
        return f"{self.party.name} - {self.accessed_at.strftime('%d/%m/%Y %H:%M:%S')}"

    class Meta:
        verbose_name = "Registro de Acesso"
        verbose_name_plural = "Rastreabilidade de Convites"
        ordering = ['-accessed_at']


# --- SINAL AUTOMÁTICO ---
@receiver(post_save, sender=Party)
def marcar_convite_como_enviado(sender, instance, created, **kwargs):
    """
    Marca automaticamente o grupo como 'convite enviado' se houver código válido.
    Evita loop recursivo ao salvar novamente dentro do sinal.
    """
    if created and instance.invitation_id and not instance.is_invited:
        Party.objects.filter(pk=instance.pk).update(is_invited=True)

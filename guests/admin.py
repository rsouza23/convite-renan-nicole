from django.contrib import admin
from .models import Guest, Party


# Inlines (para exibir convidados dentro da festa)
class GuestInline(admin.TabularInline):
    model = Guest
    fields = ('first_name', 'last_name', 'email', 'is_attending', 'meal', 'is_child')
    readonly_fields = ('first_name', 'last_name', 'email')


# Configuração do modelo Party (Festas)
class PartyAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'type', 'category', 'save_the_date_sent',
        'invitation_sent', 'rehearsal_dinner', 'invitation_opened',
        'is_invited', 'is_attending'
    )
    list_filter = (
        'type', 'category', 'is_invited', 'is_attending',
        'rehearsal_dinner', 'invitation_opened'
    )
    inlines = [GuestInline]

    class Meta:
        verbose_name = "Festa"
        verbose_name_plural = "Festas"


# Configuração do modelo Guest (Convidados)
class GuestAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'party', 'email',
        'is_attending', 'is_child', 'meal'
    )
    list_filter = (
        'is_attending', 'is_child', 'meal',
        'party__is_invited', 'party__category', 'party__rehearsal_dinner'
    )

    class Meta:
        verbose_name = "Convidado"
        verbose_name_plural = "Convidados"


# Registro dos modelos no painel admin
admin.site.register(Party, PartyAdmin)
admin.site.register(Guest, GuestAdmin)


# Personalização do cabeçalho do painel
admin.site.site_header = "Administração do Casamento"
admin.site.index_title = "Gerenciamento de Convidados e Festas"
admin.site.site_title = "Painel - Casamento Renan & Nicole"

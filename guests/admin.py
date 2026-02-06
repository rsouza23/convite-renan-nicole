from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from .models import Guest, Party, InviteAccessLog


# --- Inline: convidados dentro do grupo/família ---
class GuestInline(admin.TabularInline):
    model = Guest
    fields = ('first_name', 'last_name', 'contact', 'is_child')
    readonly_fields = ()
    extra = 1
    show_change_link = True


# --- Inline: registros de acesso (rastreabilidade) ---
class InviteAccessInline(admin.TabularInline):
    model = InviteAccessLog
    fields = ('accessed_at', 'ip_address', 'user_agent')
    readonly_fields = ('accessed_at', 'ip_address', 'user_agent')
    extra = 0
    can_delete = False
    verbose_name_plural = "📊 Rastreabilidade de Acessos (Convite aberto)"


# --- Admin de Grupos / Famílias ---
@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'category', 'convite_enviado', 'acessos_convite', 'link_convite_tabela')
    search_fields = ('name', 'category', 'invitation_id')
    list_filter = ('is_invited',)
    inlines = [GuestInline, InviteAccessInline]

    # Campos somente leitura
    readonly_fields = ('invitation_id', 'invite_link')

    # Agrupamento dos campos no formulário
    fieldsets = [
        ("📋 Informações do Grupo / Família", {
            "fields": ("name", "category")
        }),
        ("✉️ Convite", {
            "fields": ("invitation_id", "invite_link", "is_invited")
        }),
        ("📝 Observações Internas", {
            "fields": ("comments",)
        }),
    ]

    # Campo customizado: indica se o convite foi enviado
    def convite_enviado(self, obj):
        if obj.is_invited:
            return format_html('<span style="color:green; font-weight:bold;">✅ Sim</span>')
        else:
            return format_html('<span style="color:#999;">❌ Não</span>')
    convite_enviado.short_description = "Convite enviado?"

    # Quantidade total de acessos
    def acessos_convite(self, obj):
        total = obj.total_accesses
        cor = "green" if total > 0 else "#999"
        return format_html(f'<span style="color:{cor}; font-weight:bold;">{total}</span>')
    acessos_convite.short_description = "Acessos"

    # Exibe o link completo dentro da página do grupo
    def invite_link(self, obj):
        base_url = getattr(settings, "WEDDING_WEBSITE_URL", "https://rsouza01.pythonanywhere.com")
        full_link = f"{base_url}/invite/{obj.invitation_id}"
        return format_html(
            f"""
            <a href="{full_link}" target="_blank">{full_link}</a><br>
            <button type="button" class="button"
                style="margin-top:5px;"
                onclick="navigator.clipboard.writeText('{full_link}');
                this.innerText='Copiado!';
                setTimeout(()=>this.innerText='Copiar link',1500)">
                Copiar link
            </button>
            """
        )
    invite_link.short_description = "Link do Convite"

    # Mostra o mesmo botão na listagem principal
    def link_convite_tabela(self, obj):
        base_url = getattr(settings, "WEDDING_WEBSITE_URL", "https://rsouza01.pythonanywhere.com")
        full_link = f"{base_url}/invite/{obj.invitation_id}"
        return format_html(
            f"""
            <a href="{full_link}" target="_blank" style="text-decoration:none;">🔗</a>
            <button type="button" class="button"
                style="padding:2px 8px; margin-left:4px; font-size:12px;"
                onclick="navigator.clipboard.writeText('{full_link}');
                this.innerText='✅';
                setTimeout(()=>this.innerText='📋',1200)">
                📋
            </button>
            """
        )
    link_convite_tabela.short_description = "Link"

    # Exibe nome curto na listagem (evita texto gigante)
    def short_name(self, obj):
        return obj.name[:25] + ("..." if len(obj.name) > 25 else "")
    short_name.short_description = "Nome do Grupo"

    class Media:
        css = {'all': ('admin/css/custom_admin.css',)}


# --- Admin de Convidados ---
@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'party', 'contact', 'is_child')
    list_filter = ('is_child', 'party__is_invited', 'party__category')
    search_fields = ('first_name', 'last_name', 'party__name', 'contact')

    class Meta:
        verbose_name = "Convidado"
        verbose_name_plural = "Convidados"


# --- Personalização do painel ---
admin.site.site_header = "Administração do Casamento"
admin.site.index_title = "Gerenciamento de Grupos / Famílias e Convidados"
admin.site.site_title = "Painel - Casamento Renan & Nicole"

# Renomeia “Festas” → “Grupos / Famílias”
Party._meta.verbose_name = "Grupo / Família"
Party._meta.verbose_name_plural = "Grupos / Famílias"

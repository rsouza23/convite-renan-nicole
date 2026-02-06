import base64
from collections import namedtuple
import random
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView

from guests import csv_import
from guests.invitation import (
    get_invitation_context, INVITATION_TEMPLATE,
    guess_party_by_invite_id_or_404, send_invitation_email
)
from guests.models import Guest, Party
from guests.save_the_date import (
    get_save_the_date_context, send_save_the_date_email,
    SAVE_THE_DATE_TEMPLATE, SAVE_THE_DATE_CONTEXT_MAP
)


# ==============================
# LISTA DE CONVIDADOS
# ==============================
class GuestListView(ListView):
    model = Guest


# ==============================
# EXPORTAÇÃO CSV
# ==============================
@login_required
def export_guests(request):
    export = csv_import.export_guests()
    response = HttpResponse(export.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=all-guests.csv'
    return response


# ==============================
# DASHBOARD ADMIN
# ==============================
@login_required
def dashboard(request):
    parties_with_pending_invites = Party.objects.filter(
        is_invited=True
    ).order_by('category', 'name')

    attending_guests = Guest.objects.filter(is_attending=True)
    notcoming_guests = Guest.objects.filter(is_attending=False)
    pending_guests = Guest.objects.filter(party__is_invited=True, is_attending=None)

    category_breakdown = attending_guests.values('party__category').annotate(count=Count('*'))

    return render(request, 'guests/dashboard.html', context={
        'couple_name': settings.BRIDE_AND_GROOM,
        'website_url': settings.WEDDING_WEBSITE_URL,
        'guests': attending_guests.count(),
        'possible_guests': Guest.objects.filter(party__is_invited=True).exclude(is_attending=False).count(),
        'not_coming_guests': notcoming_guests.count(),
        'pending_invites': parties_with_pending_invites.count(),
        'pending_guests': pending_guests.count(),
        'unopened_invite_count': Party.objects.filter(is_invited=True, invitation_opened=None).count(),
        'total_invites': Party.objects.filter(is_invited=True).count(),
        'guestlist': attending_guests.order_by('party__name', 'first_name'),
        'notcoming': notcoming_guests.order_by('party__name', 'first_name'),
        'category_breakdown': category_breakdown,
        'parties': Party.objects.all(),
    })


# ==============================
# CONVITE INDIVIDUAL
# ==============================
def invitation(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)

    if not party.is_invited:
        party.is_invited = True
    if not getattr(party, 'invitation_opened', None):
        party.invitation_opened = datetime.utcnow()
    party.save(update_fields=['is_invited', 'invitation_opened'])

    if request.method == 'POST':
        for response in _parse_invite_params(request.POST):
            guest = Guest.objects.get(pk=response.guest_pk)
            assert guest.party == party
            guest.is_attending = response.is_attending
            guest.save()

        if request.POST.get('comments'):
            comments = request.POST.get('comments')
            party.comments = comments if not party.comments else f"{party.comments}; {comments}"

        # 🕒 registra data da última confirmação
        party.invitation_sent = datetime.utcnow()
        party.save(update_fields=['comments', 'invitation_sent'])

        return HttpResponseRedirect(reverse('rsvp-confirm', args=[invite_id]))

    return render(request, 'guests/invitation_modern.html', {
        'party': party,
        'couple_name': settings.BRIDE_AND_GROOM,
        'website_url': settings.WEDDING_WEBSITE_URL,
    })


InviteResponse = namedtuple('InviteResponse', ['guest_pk', 'is_attending'])


def _parse_invite_params(params):
    responses = {}
    for param, value in params.items():
        if param.startswith('attending'):
            pk = int(param.split('-')[-1])
            responses[pk] = {'attending': value == 'yes'}

    for pk, response in responses.items():
        yield InviteResponse(pk, response['attending'])


# ==============================
# CONFIRMAÇÃO DE RSVP
# ==============================
def rsvp_confirm(request, invite_id=None):
    party = guess_party_by_invite_id_or_404(invite_id)
    guests = party.ordered_guests.all()

    total = guests.count()
    confirmed = guests.filter(is_attending=True).count()
    declined = guests.filter(is_attending=False).count()

    if confirmed == total and total > 0:
        status = "all"
    elif confirmed > 0 and declined > 0:
        status = "some"
    elif confirmed == 0 and declined == total:
        status = "none"
    else:
        status = "unknown"

    return render(request, 'guests/rsvp_confirmation.html', {
        'party': party,
        'status': status,
        'support_email': settings.DEFAULT_WEDDING_REPLY_EMAIL,
        'couple_name': settings.BRIDE_AND_GROOM,
        'website_url': settings.WEDDING_WEBSITE_URL,
    })


# ==============================
# EMAILS E TEMPLATES
# ==============================
@login_required
def invitation_email_preview(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    context = get_invitation_context(party)
    return render(request, INVITATION_TEMPLATE, context=context)


@login_required
def invitation_email_test(request, invite_id):
    party = guess_party_by_invite_id_or_404(invite_id)
    send_invitation_email(party, recipients=[settings.DEFAULT_WEDDING_TEST_EMAIL])
    return HttpResponse('sent!')


def save_the_date_random(request):
    template_id = random.choice(list(SAVE_THE_DATE_CONTEXT_MAP.keys()))
    return save_the_date_preview(request, template_id)


def save_the_date_preview(request, template_id):
    context = get_save_the_date_context(template_id)
    context['email_mode'] = False
    return render(request, SAVE_THE_DATE_TEMPLATE, context=context)


@login_required
def test_email(request, template_id):
    context = get_save_the_date_context(template_id)
    send_save_the_date_email(context, [settings.DEFAULT_WEDDING_TEST_EMAIL])
    return HttpResponse('sent!')


def _base64_encode(filepath):
    with open(filepath, "rb") as image_file:
        return base64.b64encode(image_file.read())


# ==============================
# PÁGINA INTERMEDIÁRIA /invite/
# ==============================
def invite_lookup(request):
    if request.method == "POST":
        query = request.POST.get("query", "").strip()
        party = Party.objects.filter(invitation_id__iexact=query).first() or \
                Party.objects.filter(name__icontains=query).first()

        if party:
            if not party.is_invited:
                party.is_invited = True
                party.save(update_fields=['is_invited'])
            return redirect(f"/invite/{party.invitation_id}/")

        return render(request, "guests/invite.html", {
            "error": "Nenhum convite encontrado. Verifique o nome ou código informado."
        })

    return render(request, "guests/invite.html")

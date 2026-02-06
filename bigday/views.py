from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import mercadopago
import json

# Página inicial
def home_view(request):
    return render(request, 'home.html')

# Página de presentes (versão completa)
def all_gifts_view(request):
    gifts = {
        "Cozinha": [
            {"name": "Geladeira Frost Free", "price": 3500.00, "image": "bigday/images/gifts/geladeira.jpg", "description": "Ajude-nos a equipar nossa cozinha com uma geladeira nova. ❄️"},
            {"name": "Fogão 4 bocas", "price": 1200.00, "image": "bigday/images/gifts/fogao.jpg", "description": "Nosso cantinho precisa de um fogão para muitas receitas juntos. 🍝"},
            {"name": "Micro-ondas 30L", "price": 750.00, "image": "bigday/images/gifts/microondas.jpg", "description": "Praticidade para as refeições do dia a dia. 🍲"},
            {"name": "Jogo de Panelas", "price": 480.00, "image": "bigday/images/gifts/panelas.jpg", "description": "Contribua para que possamos preparar muitas receitas juntos. 🍳"},
            {"name": "Liquidificador", "price": 290.00, "image": "bigday/images/gifts/liquidificador.jpg", "description": "Perfeito para nossos cafés da manhã e sucos frescos. 🧃"},
        ],
        "Casa & Lavanderia": [
            {"name": "Máquina de Lavar", "price": 2000.00, "image": "bigday/images/gifts/lavadora.jpg", "description": "Facilite nosso dia a dia com uma lavadora novinha. 🧺"},
            {"name": "Aspirador de pó", "price": 500.00, "image": "bigday/images/gifts/aspirador.jpg", "description": "Deixe nossa casa sempre limpinha. 🧹"},
            {"name": "Ferro de passar", "price": 220.00, "image": "bigday/images/gifts/ferro.jpg", "description": "Ajude a manter nossas roupas impecáveis. 👕"},
        ],
        "Decoração & Conforto": [
            {"name": "Conjunto de Toalhas", "price": 160.00, "image": "bigday/images/gifts/toalhas.jpg", "description": "Para momentos relaxantes e aconchegantes. 🛁"},
            {"name": "Jogo de Cama Queen", "price": 290.00, "image": "bigday/images/gifts/jogo-cama.jpg", "description": "Deixe nosso descanso mais confortável. 💤"},
            {"name": "Tapete para sala", "price": 350.00, "image": "bigday/images/gifts/tapete.jpg", "description": "Um toque de aconchego para nosso novo lar. 🏡"},
        ],
        "Viagem & Experiências": [
            {"name": "Contribuição para Lua de Mel", "price": 500.00, "image": "bigday/images/gifts/viagem.jpg", "description": "Ajude-nos a viver dias inesquecíveis na lua de mel. 🌴✈️"},
            {"name": "Jantar Romântico", "price": 300.00, "image": "bigday/images/gifts/jantar.jpg", "description": "Um jantar especial para brindar o amor. 🍷🍽️"},
        ],
    }

    return render(request, 'gifts/all_gifts.html', {'gifts': gifts})


# Integração Mercado Pago
@csrf_exempt
def create_preference(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    try:
        data = json.loads(request.body)
        title = data.get("title", "Presente de Casamento")
        price = float(data.get("price", 10.00))
    except Exception as e:
        return JsonResponse({"error": f"Erro ao processar JSON: {e}"}, status=400)

    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": price
            }
        ],
        "back_urls": {
        "success": "https://rsouza01.pythonanywhere.com/pagamento/sucesso/",
        "failure": "https://rsouza01.pythonanywhere.com/",
        "pending": "https://rsouza01.pythonanywhere.com/"
        },
        "auto_return": "approved",


        # 🔹 Configuração dos métodos de pagamento (Pix incluso)
        "payment_methods": {
            "excluded_payment_types": [
                {"id": "ticket"}  # se quiser ocultar boleto, tire essa linha
            ],
            "included_payment_methods": [
                {"id": "pix"},         # força exibir Pix
                {"id": "bolbradesco"}, # boleto Bradesco
                {"id": "visa"},        # exemplo de cartão
                {"id": "master"}       # exemplo de cartão
            ],
            "installments": 12
        }
    }

    try:
        preference = sdk.preference().create(preference_data)
        return JsonResponse(preference["response"])
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Página de agradecimento após pagamento
def payment_success(request):
    return render(request, 'success.html')
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from datetime import timedelta
from datetime import date
from .models import Transaction, Budget, BudgetHistory, Category
from .nlp_processing import process_voice_transaction
from rest_framework import generics, filters, serializers
from rest_framework.pagination import PageNumberPagination
import csv
from .serializers import TransactionSerializer
import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Profile
from .serializers import BudgetSerializer, BudgetHistorySerializer
from payments.models import RecurringPayment

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_voice_entry(request):
    """
    Processes voice input and returns structured transaction details for user confirmation.
    """
    voice_text = request.data.get("voice_text", "")
    if not voice_text:
        return Response({"error": "No voice input received"}, status=400)

    transaction_data = process_voice_transaction(voice_text)
    return Response(transaction_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_voice_transaction(request):
    """
    Saves user-confirmed transaction to the database.
    """
    user = request.user
    amount = request.data.get("amount")
    transaction_type = request.data.get("transaction_type", "expense")
    category = request.data.get("category", "General")
    description = request.data.get("description", "")
    transaction_date = request.data.get("date") or date.today()

    if not amount or not transaction_type or not category:
        return Response({"error": "Missing transaction details"}, status=400)

    category_obj, _ = Category.objects.get_or_create(
        user=user,
        name=str(category).strip() or "General",
    )

    transaction = Transaction.objects.create(
        user=user,
        amount=amount,
        category_type=transaction_type if transaction_type in {"income", "expense"} else "expense",
        category=category_obj,
        description=description,
        date=transaction_date,
    )

    return Response({"message": "Transaction saved successfully!", "transaction_id": transaction.id})


@api_view(['GET'])
def get_transactions(request):
    transactions = Transaction.objects.select_related('category').all().order_by('-date')[:10]  # Fetch latest 10 transactions

    data = [
        {
            "id": t.id,
            "category_name": t.category.name,  # Fetch category name
            "category_type": t.category_type,  # Income or Expense
            "description": t.description,
            "amount": float(t.amount),
            "date": t.date.isoformat(),  # Convert date to JSON format
        }
        for t in transactions
    ]
    
    return JsonResponse(data, safe=False)






@api_view(['GET'])
@permission_classes([IsAuthenticated])
def upcoming_bills(request):
    """
    Fetch upcoming recurring payments for the user.
    """
    user = request.user
    today = now().date()
    upcoming_payments = RecurringPayment.objects.filter(
        user=user, 
        next_payment_date__gte=today,  # Payments due today or later
        status="active"
    ).order_by('next_payment_date')

    bills_list = [
        {
            "id": payment.id,
            "name": payment.name,
            "amount": float(payment.amount),
            "category": payment.category,
            "frequency": payment.frequency,
            "days_remaining": (payment.next_payment_date - today).days,
            "next_payment_date": payment.next_payment_date.strftime("%Y-%m-%d")
        } for payment in upcoming_payments
    ]

    return Response(bills_list)


def track_budget_history(user):
    """
    Stores historical budget data and calculates suggested budget.
    """
    current_month = now().month
    current_year = now().year

    budgets = Budget.objects.filter(user=user)

    for budget in budgets:
        category = budget.category
        prev_limit = budget.monthly_limit

        # Get total spending for this category in the last month
        last_month = (now() - timedelta(days=30)).month
        total_spent = Transaction.objects.filter(
            user=user, category_id=category, date__month=last_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        # AI Logic to Suggest Budget Adjustment
        suggested_limit = prev_limit
        if total_spent > prev_limit:
            suggested_limit = prev_limit * 1.1  # Increase budget by 10% if overspending
        elif total_spent < (prev_limit * 0.7):
            suggested_limit = prev_limit * 0.9  # Decrease budget by 10% if underused

        # Save to BudgetHistory Table
        BudgetHistory.objects.update_or_create(
            user=user,
            category=category,
            month=current_month,
            year=current_year,
            defaults={
                "previous_limit": prev_limit,
                "actual_spent": total_spent,
                "suggested_limit": suggested_limit,
            }
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_transactions_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Date', 'Category', 'Amount', 'Description'])

    transactions = Transaction.objects.all().values_list('id', 'date', 'category__name', 'amount', 'description')
    for transaction in transactions:
        writer.writerow(transaction)

    return response


# Pagination class for handling multiple transactions
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Show 10 transactions per page
    page_size_query_param = 'page_size'
    max_page_size = 100


# View for listing and creating transactions
class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description']
    ordering_fields = ['date', 'amount']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(user_id=user.id).order_by('-date')
        category = self.request.query_params.get('category', None)
        min_amount = self.request.query_params.get('min_amount', None)
        date = self.request.query_params.get('date', None)

        if category:
            queryset = queryset.filter(category__id=category)
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if date:
            queryset = queryset.filter(date=date)

        return queryset




class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = serializers.ModelSerializer
    serializer_class.Meta = type("Meta", (object,), {"model": Category, "fields": "__all__"})



class CurrencyConverter(APIView):
    def get(self, request):
        base_currency = request.query_params.get('base', 'USD')
        target_currency = request.query_params.get('target', 'INR')

        api_url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        response = requests.get(api_url)

        if response.status_code != 200:
            return Response({"error": "Failed to fetch exchange rates"}, status=500)

        data = response.json()
        conversion_rate = data["rates"].get(target_currency, None)

        if conversion_rate:
            return Response({"rate": conversion_rate}, status=200)
        else:
            return Response({"error": "Invalid currency"}, status=400)



class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(user_id=user.id).order_by('-date')

        # Convert transactions to user’s preferred currency
        user_profile = UsersProfile.objects.filter(user_id=user.id).first()
        user_currency = user_profile.preferred_currency if user_profile else 'USD'
        base_currency = 'USD'  # Assuming transactions are stored in USD
        
        if user_currency != base_currency:
            for transaction in queryset:
                rate = self.get_conversion_rate(base_currency, user_currency)
                transaction.amount = transaction.amount * rate  # Convert amount

        return queryset

    def get_conversion_rate(self, base_currency, target_currency):
        api_url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            return data["rates"].get(target_currency, 1)
        return 1

class BudgetView(generics.ListCreateAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TransactionsBudget.objects.filter(user_id=self.kwargs['user_id'])

# Fetch budget history
class BudgetHistoryView(generics.ListAPIView):
    serializer_class = BudgetHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TransactionsBudgetHistory.objects.filter(
            user_id=self.kwargs['user_id'], 
            month=self.request.query_params.get('month'), 
            year=self.request.query_params.get('year')
        )
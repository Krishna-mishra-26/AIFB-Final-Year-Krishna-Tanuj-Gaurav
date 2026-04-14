from django.urls import path
from .views import (
    process_voice_entry, confirm_voice_transaction, get_transactions, upcoming_bills,
    export_transactions_csv, TransactionListCreateView,  CategoryListView
)
from .views import CurrencyConverter
from .views import BudgetView, BudgetHistoryView

urlpatterns = [
    path('process-voice-entry/', process_voice_entry, name='process_voice_entry'),
    path('confirm-voice-transaction/', confirm_voice_transaction, name='confirm_voice_transaction'),
    path('get-transactions/', get_transactions, name='get_transactions'),
    path('api/upcoming-bills/', upcoming_bills, name='upcoming-bills'),

    path('export-transactions-csv/', export_transactions_csv, name='export_transactions_csv'),
    path('transactions/', TransactionListCreateView.as_view(), name='transaction_list_create'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('api/currency-convert/', CurrencyConverter.as_view(), name='currency-converter'),
    path('budget/<uuid:user_id>/', BudgetView.as_view(), name='budget'),
    path('budget-history/<uuid:user_id>/', BudgetHistoryView.as_view(), name='budget-history'),

]

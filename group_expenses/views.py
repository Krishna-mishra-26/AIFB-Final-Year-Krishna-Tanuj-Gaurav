from rest_framework import viewsets
from .models import Group, GroupExpense, GroupMember, Settlement
from .serializers import GroupSerializer, GroupExpenseSerializer, GroupMemberSerializer, SettlementSerializer
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import datetime
from django.shortcuts import render


def group_expenses_view(request):
    return render(request, 'frontend/group_expenses.html')



# View to render the group dashboard
def group_dashboard(request, group_id):
    try:
        # Fetch the group and related data dynamically from the database
        group = Group.objects.get(id=group_id)
        group_members = GroupMember.objects.filter(group=group)

        # Fetch recent expenses and balances dynamically
        expenses = GroupExpense.objects.filter(group=group).order_by('-date')[:5]  # Fetch the latest 5 expenses
        balances = Settlement.objects.filter(group=group)  # Fetch all settlements related to the group

        return render(request, 'group_expenses/group_dashboard.html', {
            'group': group,
            'group_members': group_members,
            'expenses': expenses,
            'balances': balances
        })
    except Group.DoesNotExist:
        return render(request, 'error.html', {'error': 'Group not found'})

# Add a new expense to the group
def add_expense(request, group_id):
    if request.method == 'POST':
        description = request.POST.get('description')
        amount = float(request.POST.get('amount'))
        category = request.POST.get('category')
        date = request.POST.get('date')
        split_type = request.POST.get('splitType')
        paid_by = request.POST.get('paid_by')  # ID of the member who paid

        # Basic validation
        if not description or not amount:
            return render(request, 'frontend/group_expenses.html', {
                'error': 'Description and amount are required.'
            })

        # Save the expense
        expense = GroupExpense.objects.create(
            description=description,
            amount=amount,
            category=category,
            date=date,
            split_type=split_type,
            paid_by_id=paid_by,
            group_id=group_id  # Store which group the expense belongs to
        )

        # If split type is 'equal', split the expense equally among members
        if split_type == 'equal':
            members = GroupMember.objects.filter(group_id=group_id)
            split_amount = amount / len(members)

            # Create settlements for each member
            for member in members:
                Settlement.objects.create(
                    group_id=group_id,
                    member_id=member.id,
                    amount=split_amount,
                    expense=expense
                )

        return HttpResponseRedirect(reverse('group_expenses:group_dashboard', args=[group_id]))  # Redirect to group dashboard

    # If GET request or something else
    return render(request, 'frontend/group_expenses.html')

# ViewSet for managing groups
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

# ViewSet for managing group expenses
class GroupExpenseViewSet(viewsets.ModelViewSet):
    queryset = GroupExpense.objects.all()
    serializer_class = GroupExpenseSerializer

# ViewSet for managing group members
class GroupMemberViewSet(viewsets.ModelViewSet):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer

# ViewSet for managing settlements
class SettlementViewSet(viewsets.ModelViewSet):
    queryset = Settlement.objects.all()
    serializer_class = SettlementSerializer

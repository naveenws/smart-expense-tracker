import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponse
from .models import Expense
from .forms import ExpenseForm, SignUpForm
from datetime import date, timedelta
from django.db.models import Sum

def user_signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Account created successfully')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    transactions = Expense.objects.filter(user=request.user).order_by('-date')
    
    # Filtering
    filter_by = request.GET.get('filter', 'all')
    today = date.today()
    if filter_by == 'today':
        transactions = transactions.filter(date=today)
    elif filter_by == 'week':
        start_week = today - timedelta(today.weekday())
        transactions = transactions.filter(date__gte=start_week)
    elif filter_by == 'month':
        transactions = transactions.filter(date__year=today.year, date__month=today.month)

    # Calculate Totals
    income_qs = transactions.filter(transaction_type='Income')
    expense_qs = transactions.filter(transaction_type='Expense')

    total_income = sum(item.amount for item in income_qs)
    total_expense = sum(item.amount for item in expense_qs)
    balance = total_income - total_expense

    # Aggregations for charts (Expenses by Category)
    # Use order_by() to clear default sorting which breaks GROUP BY
    category_data = expense_qs.order_by('category').values('category').annotate(total=Sum('amount'))
    categories = [item['category'] for item in category_data]
    category_totals = [float(item['total']) for item in category_data]

    # Chart data for Income vs Expense
    type_labels = ['Income', 'Expense']
    type_totals = [float(total_income), float(total_expense)]

    context = {
        'expenses': transactions, # Kept the name expenses for template compatibility
        'categories': categories,
        'category_totals': category_totals,
        'type_labels': type_labels,
        'type_totals': type_totals,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'filter_by': filter_by,
    }
    return render(request, 'dashboard.html', context)

def predict_category(description):
    desc = description.lower()
    if any(word in desc for word in ['uber', 'lyft', 'taxi', 'train', 'bus', 'flight', 'fuel']):
        return 'Travel'
    elif any(word in desc for word in ['pizza', 'burger', 'restaurant', 'food', 'grocery', 'swiggy', 'zomato']):
        return 'Food'
    elif any(word in desc for word in ['movie', 'netflix', 'spotify', 'game', 'concert', 'cinema']):
        return 'Entertainment'
    elif any(word in desc for word in ['hospital', 'doctor', 'medicine', 'pharmacy', 'clinic']):
        return 'Health'
    elif any(word in desc for word in ['electricity', 'water', 'internet', 'rent', 'bill']):
        return 'Utilities'
    elif any(word in desc for word in ['amazon', 'flipkart', 'cloth', 'shoe', 'mall']):
        return 'Shopping'
    return 'Other'

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            if expense.category == 'Other':
                # Try to predict if left as 'Other' or maybe always try?
                expense.category = predict_category(expense.description)
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'expense_form.html', {'form': form, 'action': 'Add'})

@login_required
def edit_expense(request, id):
    expense = get_object_or_404(Expense, id=id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expense_form.html', {'form': form, 'action': 'Edit'})

@login_required
def delete_expense(request, id):
    expense = get_object_or_404(Expense, id=id, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('dashboard')
    return render(request, 'confirm_delete.html', {'expense': expense})

@login_required
def export_expenses_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Description', 'Category', 'Amount', 'Notes'])

    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    for expense in expenses:
        writer.writerow([expense.date, expense.description, expense.category, expense.amount, expense.notes])

    return response


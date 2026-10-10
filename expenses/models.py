from django.db import models
from django.contrib.auth.models import User

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Travel', 'Travel'),
        ('Entertainment', 'Entertainment'),
        ('Utilities', 'Utilities'),
        ('Health', 'Health'),
        ('Shopping', 'Shopping'),
        ('Salary', 'Salary'),
        ('Bonus', 'Bonus'),
        ('Investment', 'Investment'),
        ('Other', 'Other'),
    ]

    TRANSACTION_TYPES = [
        ('Income', 'Income'),
        ('Expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='Expense')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_type}: {self.description} - {self.amount}"

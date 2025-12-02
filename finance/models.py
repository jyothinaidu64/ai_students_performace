from django.db import models
from django.contrib.auth.models import User
from students.models import Student

class FeeStructure(models.Model):
    """
    What is the total fee for a class/academic year.
    """
    name = models.CharField(max_length=100)  # "2025 Annual Fee", "Term 1 Fee"
    class_section = models.CharField(max_length=20)  # "10A"
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.class_section})"


class FeeAssignment(models.Model):
    """
    Specific fee assigned to each student (based on FeeStructure, with discounts).
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def net_amount(self):
        return self.total_amount - self.discount_amount

    def amount_paid(self):
        return sum(p.amount for p in self.payments.all())

    def balance(self):
        return self.net_amount - self.amount_paid()

    def __str__(self):
        return f"{self.student} - {self.fee_structure}"


class FeePayment(models.Model):
    """
    Each payment the parent makes.
    """
    assignment = models.ForeignKey(
        FeeAssignment,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mode = models.CharField(
        max_length=30,
        choices=(("CASH", "Cash"), ("ONLINE", "Online"), ("CARD", "Card")),
        default="ONLINE",
    )
    receipt_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"Payment {self.receipt_number} - {self.amount}"

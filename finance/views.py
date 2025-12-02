# finance/views.py

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from accounts.decorators import role_required
from students.models import Student
from .models import FeeAssignment, FeePayment


# -------------------------------------------------------------------
# Student view: My Fees
# -------------------------------------------------------------------

@login_required
def my_fees_view(request):
    """
    Student view: see all fee assignments + payments + balances.
    """
    student = get_object_or_404(Student, user=request.user)

    assignments = (
        FeeAssignment.objects
        .filter(student=student)
        .select_related("fee_structure")
        .prefetch_related("payments")
    )

    rows = []
    total_net = Decimal("0.00")
    total_paid = Decimal("0.00")

    for fa in assignments:
        net = fa.net_amount or Decimal("0.00")
        paid = fa.amount_paid() or Decimal("0.00")
        balance = fa.balance() or Decimal("0.00")

        total_net += net
        total_paid += paid

        rows.append({
            "assignment": fa,
            "fee_name": fa.fee_structure.name,
            "total": fa.total_amount,
            "discount": fa.discount_amount,
            "net": net,
            "paid": paid,
            "balance": balance,
        })

    total_balance = total_net - total_paid

    context = {
        "student": student,
        "assignments": assignments,  # raw queryset if template still uses it
        "rows": rows,                # richer per-assignment data
        "total_net": total_net,
        "total_paid": total_paid,
        "total_balance": total_balance,
    }
    return render(request, "finance/my_fees.html", context)


# -------------------------------------------------------------------
# Receipt detail
# -------------------------------------------------------------------

@login_required
def receipt_detail_view(request, payment_id):
    """
    Show details for a single payment / receipt.
    Basic permission check: if user is a student, must own this payment.
    """
    payment = get_object_or_404(FeePayment, id=payment_id)

    # Simple permission check for students:
    if hasattr(request.user, "role") and request.user.role == request.user.Role.STUDENT:
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return render(
                request,
                "finance/no_student_profile.html",
                {"user": request.user},
                status=404,
            )

        if payment.assignment.student_id != student.id:
            # Student trying to see another student's receipt
            return render(
                request,
                "finance/forbidden.html",
                {"reason": "You are not allowed to view this receipt."},
                status=403,
            )

    return render(request, "finance/receipt_detail.html", {"payment": payment})


# -------------------------------------------------------------------
# Management view: Finance Overview
# -------------------------------------------------------------------

@role_required("MANAGEMENT")
def finance_overview(request):
    """
    Management view: high-level fee summary per class and totals.

    Based on FeeAssignment:
    - total_amount
    - discount_amount
    - related payments (FeePayment) via 'payments' related_name.
    """

    qs = (
        FeeAssignment.objects
        .select_related("student__school_class")
        .prefetch_related("payments")
    )

    # If your User has a school field, show only that school's data
    if hasattr(request.user, "school") and request.user.school_id:
        qs = qs.filter(student__school_class__school=request.user.school)

    total_assigned = Decimal("0.00")  # net of discounts
    total_paid = Decimal("0.00")

    per_class = {}

    for fa in qs:
        total = fa.total_amount or Decimal("0.00")
        discount = fa.discount_amount or Decimal("0.00")

        net = total - discount

        # Sum of all payments recorded for this assignment
        paid = Decimal("0.00")
        for p in fa.payments.all():
            paid += p.amount or Decimal("0.00")

        total_assigned += net
        total_paid += paid

        cls = fa.student.school_class
        key = cls.id

        if key not in per_class:
            per_class[key] = {
                "class_obj": cls,
                "students": set(),
                "assigned": Decimal("0.00"),
                "paid": Decimal("0.00"),
            }

        entry = per_class[key]
        entry["students"].add(fa.student_id)
        entry["assigned"] += net
        entry["paid"] += paid

    total_outstanding = total_assigned - total_paid

    per_class_rows = []
    for data in per_class.values():
        assigned = data["assigned"]
        paid = data["paid"]
        outstanding = assigned - paid
        per_class_rows.append({
            "class_obj": data["class_obj"],
            "student_count": len(data["students"]),
            "assigned": assigned,
            "paid": paid,
            "outstanding": outstanding,
        })

    # Sort by class name
    per_class_rows.sort(key=lambda r: str(r["class_obj"]))

    context = {
        "total_assigned": total_assigned,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
        "per_class_rows": per_class_rows,
        "nav_finance_active": "active",
    }
    return render(request, "finance/overview.html", context)



from django.shortcuts import redirect  # if not already imported


@role_required("MANAGEMENT")
def finance_class_detail(request, class_id):
    """
    Management drill-down: per-student fee summary for a single class.
    Shows net (after discount), paid, balance per student.
    """

    # Get all assignments for the given class
    assignments = (
        FeeAssignment.objects
        .select_related("student__user", "student__school_class", "fee_structure")
        .prefetch_related("payments")
        .filter(student__school_class_id=class_id)
    )

    # If your management user is tied to a school, enforce that:
    if hasattr(request.user, "school") and request.user.school_id:
        assignments = assignments.filter(student__school_class__school=request.user.school)

    # Handle invalid/empty class
    if not assignments.exists():
        # Optionally redirect back with a message; for now just show empty state
        class_obj = None
    else:
        class_obj = assignments.first().student.school_class

    # Aggregate per student
    from decimal import Decimal
    per_student = {}

    for fa in assignments:
        student = fa.student
        key = student.id

        total = fa.total_amount or Decimal("0.00")
        discount = fa.discount_amount or Decimal("0.00")
        net = total - discount

        paid = Decimal("0.00")
        for p in fa.payments.all():
            paid += p.amount or Decimal("0.00")

        if key not in per_student:
            per_student[key] = {
                "student": student,
                "assigned": Decimal("0.00"),
                "paid": Decimal("0.00"),
            }

        entry = per_student[key]
        entry["assigned"] += net
        entry["paid"] += paid

    rows = []
    total_assigned = Decimal("0.00")
    total_paid = Decimal("0.00")

    for data in per_student.values():
        assigned = data["assigned"]
        paid = data["paid"]
        balance = assigned - paid

        total_assigned += assigned
        total_paid += paid

        rows.append({
            "student": data["student"],
            "assigned": assigned,
            "paid": paid,
            "balance": balance,
        })

    rows.sort(key=lambda r: r["student"].user.get_full_name().lower() if r["student"].user.get_full_name() else r["student"].user.username.lower())

    total_balance = total_assigned - total_paid

    context = {
        "class_obj": class_obj,
        "rows": rows,
        "total_assigned": total_assigned,
        "total_paid": total_paid,
        "total_balance": total_balance,
        "nav_finance_active": "active",
    }
    return render(request, "finance/class_detail.html", context)

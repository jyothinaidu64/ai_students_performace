from .models import School

def current_school(request):
    """
    Injects current_school into all templates.
    For now, it's derived from request.user.school.
    Later you can extend this to use subdomain, slug, etc.
    """
    user = getattr(request, "user", None)
    if user and user.is_authenticated and getattr(user, "school_id", None):
        return {"current_school": user.school}

    # Fallback: you can choose a default school or None
    # For now: just None
    return {"current_school": None}


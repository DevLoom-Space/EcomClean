import time


def static_version(request):
    """Return a STATIC_VERSION value for cache-busting in templates.

    In development this is a timestamp generated at import time so it's stable
    for the lifetime of the process but changes when the server restarts.
    """
    return {"STATIC_VERSION": str(int(time.time()))}


def cart_count(request):
    """Return a small cart count from session for templates.

    This is intentionally minimal: it reads `request.session['cart_count']`
    and falls back to 0 when missing.
    """
    try:
        return {"cart_count": int(request.session.get("cart_count", 0))}
    except Exception:
        return {"cart_count": 0}

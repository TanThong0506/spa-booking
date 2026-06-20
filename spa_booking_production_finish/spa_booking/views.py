from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    database_status = "ok"
    http_status = 200

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        database_status = "error"
        http_status = 503

    return JsonResponse(
        {
            "status": (
                "ok"
                if http_status == 200
                else "unhealthy"
            ),
            "service": "spa-booking",
            "database": database_status,
        },
        status=http_status,
    )

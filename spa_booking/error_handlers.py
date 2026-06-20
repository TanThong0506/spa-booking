import logging

from django.shortcuts import render


logger = logging.getLogger(__name__)


def bad_request(request, exception=None):
    logger.warning(
        'Bad request: path=%s exception=%s',
        request.path,
        exception,
    )
    return render(
        request,
        'errors/400.html',
        status=400,
    )


def permission_denied(request, exception=None):
    logger.warning(
        'Permission denied: path=%s user=%s exception=%s',
        request.path,
        request.user,
        exception,
    )
    return render(
        request,
        'errors/403.html',
        status=403,
    )


def page_not_found(request, exception=None):
    logger.info(
        'Page not found: path=%s exception=%s',
        request.path,
        exception,
    )
    return render(
        request,
        'errors/404.html',
        status=404,
    )


def server_error(request):
    logger.error(
        'Unhandled server error: path=%s',
        request.path,
        exc_info=True,
    )
    return render(
        request,
        'errors/500.html',
        status=500,
    )


def csrf_failure(request, reason=''):
    logger.warning(
        'CSRF verification failed: path=%s reason=%s',
        request.path,
        reason,
    )
    return render(
        request,
        'errors/403.html',
        {
            'custom_title': 'Phiên làm việc đã hết hạn',
            'custom_message': (
                'Vui lòng tải lại trang và thực hiện thao tác một lần nữa.'
            ),
        },
        status=403,
    )

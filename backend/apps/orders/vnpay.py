import hashlib
import hmac
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone


VNPAY_VERSION = '2.1.0'
VNPAY_COMMAND = 'pay'
VNPAY_CURRENCY = 'VND'
VNPAY_LOCALE = 'vn'
VNPAY_ORDER_TYPE = 'other'


class VNPayConfigError(Exception):
    pass


def is_configured():
    return bool(settings.VNPAY_TMN_CODE and settings.VNPAY_HASH_SECRET_KEY)


def build_payment_url(*, order, request, return_url):
    if not is_configured():
        raise VNPayConfigError('VNPay chua duoc cau hinh TMN code hoac hash secret.')

    created_at = timezone.localtime(timezone.now())
    expire_at = created_at + timedelta(minutes=settings.VNPAY_EXPIRE_MINUTES)

    params = {
        'vnp_Version': VNPAY_VERSION,
        'vnp_Command': VNPAY_COMMAND,
        'vnp_TmnCode': settings.VNPAY_TMN_CODE,
        'vnp_Amount': _to_vnpay_amount(order.total_amount),
        'vnp_CurrCode': VNPAY_CURRENCY,
        'vnp_TxnRef': order.order_code,
        'vnp_OrderInfo': f'Thanh toan don hang {order.order_code}',
        'vnp_OrderType': VNPAY_ORDER_TYPE,
        'vnp_Locale': VNPAY_LOCALE,
        'vnp_ReturnUrl': return_url,
        'vnp_IpAddr': get_client_ip(request),
        'vnp_CreateDate': created_at.strftime('%Y%m%d%H%M%S'),
        'vnp_ExpireDate': expire_at.strftime('%Y%m%d%H%M%S'),
    }

    signed_params = sign_params(params)
    return f'{settings.VNPAY_PAYMENT_URL}?{urlencode(signed_params)}'


def validate_response(params):
    secure_hash = params.get('vnp_SecureHash')
    if not secure_hash:
        return False

    signed_data = {
        key: value
        for key, value in params.items()
        if key.startswith('vnp_') and key not in ('vnp_SecureHash', 'vnp_SecureHashType')
    }
    expected_hash = make_secure_hash(signed_data)
    return hmac.compare_digest(expected_hash.lower(), secure_hash.lower())


def sign_params(params):
    signed_params = {
        key: value
        for key, value in params.items()
        if value is not None and str(value) != ''
    }
    signed_params['vnp_SecureHash'] = make_secure_hash(signed_params)
    return signed_params


def make_secure_hash(params):
    hash_data = urlencode(sorted(params.items()))
    return hmac.new(
        settings.VNPAY_HASH_SECRET_KEY.encode('utf-8'),
        hash_data.encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def _to_vnpay_amount(amount):
    value = Decimal(amount).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return str(int(value * 100))

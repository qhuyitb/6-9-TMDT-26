from decimal import Decimal
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlparse

from django.test import RequestFactory
from django.test import SimpleTestCase, override_settings
from django.urls import resolve

from .vnpay import build_payment_url, validate_response
from .views import VNPayIPNView, handle_vnpay_ipn


@override_settings(
    VNPAY_TMN_CODE='TESTTMN',
    VNPAY_HASH_SECRET_KEY='test-secret',
    VNPAY_PAYMENT_URL='https://sandbox.vnpayment.vn/paymentv2/vpcpay.html',
    VNPAY_EXPIRE_MINUTES=15,
)
class VNPayPaymentUrlTests(SimpleTestCase):
    def test_build_payment_url_is_signed_without_ipn_param(self):
        order = SimpleNamespace(
            order_code='ORD-TEST-IPN',
            total_amount=Decimal('125000'),
        )
        request = SimpleNamespace(META={'REMOTE_ADDR': '127.0.0.1'})

        payment_url = build_payment_url(
            order=order,
            request=request,
            return_url='https://example.test/api/orders/vnpay/return/',
        )
        params = dict(parse_qsl(urlparse(payment_url).query))

        self.assertNotIn('vnp_IpnUrl', params)
        self.assertTrue(validate_response(params))


@override_settings(VNPAY_HASH_SECRET_KEY='test-secret')
class VNPayIPNTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_ipn_route_points_to_backend_handler(self):
        match = resolve('/api/orders/vnpay/ipn/')

        self.assertIs(match.func.view_class, VNPayIPNView)

    def test_handle_vnpay_ipn_rejects_empty_request(self):
        result = handle_vnpay_ipn({})

        self.assertEqual(result['rsp_code'], '99')
        self.assertEqual(result['message'], 'Input data required')

    def test_handle_vnpay_ipn_rejects_invalid_signature(self):
        result = handle_vnpay_ipn({
            'vnp_TxnRef': 'ORD-TEST-IPN',
            'vnp_Amount': '12500000',
            'vnp_SecureHash': 'invalid',
        })

        self.assertEqual(result['rsp_code'], '97')
        self.assertEqual(result['message'], 'Invalid signature')

    def test_ipn_view_logs_received_request_and_response(self):
        request = self.request_factory.get(
            '/api/orders/vnpay/ipn/',
            {
                'vnp_TxnRef': 'ORD-TEST-IPN',
                'vnp_Amount': '12500000',
                'vnp_SecureHash': 'invalid-signature-value',
            },
            REMOTE_ADDR='127.0.0.1',
        )

        with self.assertLogs('payments.vnpay.ipn', level='INFO') as logs:
            response = VNPayIPNView.as_view()(request)

        self.assertEqual(response.data['RspCode'], '97')
        self.assertTrue(any('VNPay IPN received' in item for item in logs.output))
        self.assertTrue(any('VNPay IPN response rsp_code=97' in item for item in logs.output))
        self.assertTrue(any('invalid-...re-value' in item for item in logs.output))
        self.assertFalse(any('invalid-signature-value' in item for item in logs.output))

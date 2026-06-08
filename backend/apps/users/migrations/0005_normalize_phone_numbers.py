# Generated manually to normalize existing phone data and enforce validation.

import re

from django.core.validators import RegexValidator
from django.db import migrations, models


PHONE_ERROR_MESSAGE = 'Số điện thoại phải là số nội địa hợp lệ, ví dụ 0912345678.'
PHONE_PATTERN = r'^0[35789]\d{8}$'
PHONE_INPUT_PATTERN = r'^0[35789]\d{8}$'
PHONE_VALIDATOR = RegexValidator(regex=PHONE_INPUT_PATTERN, message=PHONE_ERROR_MESSAGE)


def normalize_phone_number(value):
    phone = re.sub(r'[^\d+]', '', str(value or '').strip())
    if not phone:
        return ''

    if phone.startswith('+'):
        phone = phone[1:]

    return phone


def valid_or_fallback_phone(current_value, fallback_value):
    normalized = normalize_phone_number(current_value)
    if re.fullmatch(PHONE_PATTERN, normalized):
        return normalized
    return fallback_value


def forwards(apps, schema_editor):
    User = apps.get_model('users', 'User')
    UserAddress = apps.get_model('users', 'UserAddress')
    db_alias = schema_editor.connection.alias

    used_phones = set()

    for user in User.objects.using(db_alias).order_by('id'):
        fallback_phone = f'09{user.pk:08d}'
        phone = valid_or_fallback_phone(user.phone, fallback_phone)
        if phone in used_phones:
            phone = fallback_phone
        user.phone = phone
        user.save(update_fields=['phone'])
        used_phones.add(phone)

    user_phone_map = dict(User.objects.using(db_alias).values_list('id', 'phone'))

    for address in UserAddress.objects.using(db_alias).order_by('id'):
        fallback_phone = user_phone_map.get(address.user_id) or f'09{address.pk:08d}'
        phone = valid_or_fallback_phone(address.receiver_phone, fallback_phone)
        if phone in used_phones and phone != user_phone_map.get(address.user_id):
            phone = fallback_phone
        address.receiver_phone = phone
        address.save(update_fields=['receiver_phone'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_cartitem_unit_price'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(max_length=10, unique=True, validators=[PHONE_VALIDATOR]),
        ),
        migrations.AlterField(
            model_name='useraddress',
            name='receiver_phone',
            field=models.CharField(max_length=10, validators=[PHONE_VALIDATOR]),
        ),
    ]
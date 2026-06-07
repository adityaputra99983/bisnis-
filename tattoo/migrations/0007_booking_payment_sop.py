# SOP-compliant payment: bukti bayar, verifikasi, batas waktu

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tattoo', '0006_artistpaymentsettings_v3_comprehensive'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='payment_expires_at',
            field=models.DateTimeField(blank=True, help_text='Batas waktu customer untuk menyelesaikan pembayaran', null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_confirmed_at',
            field=models.DateTimeField(blank=True, help_text='Waktu customer menekan tombol konfirmasi', null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_proof',
            field=models.ImageField(blank=True, help_text='Bukti pembayaran (foto struk / screenshot transfer)', null=True, upload_to='payments/proofs/'),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_proof_uploaded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_verification_status',
            field=models.CharField(choices=[('not_required', 'Tidak Perlu Verifikasi'), ('pending', 'Menunggu Verifikasi'), ('approved', 'Disetujui'), ('rejected', 'Ditolak')], default='not_required', help_text='Status verifikasi bukti pembayaran oleh artist', max_length=20),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_verification_note',
            field=models.TextField(blank=True, help_text='Catatan dari artist (alasan tolak / info approval)', null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_verified_by',
            field=models.ForeignKey(blank=True, help_text='Artist yang memverifikasi pembayaran', null=True, on_delete=models.deletion.SET_NULL, related_name='verified_payments', to=settings.AUTH_USER_MODEL),
        ),
    ]

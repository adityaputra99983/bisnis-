# Generated for Artist Payment Settings v3

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tattoo', '0005_artistpaymentsettings_card_fee_percent_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='bank_cimb_number',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='bank_cimb_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_bca',
            field=models.BooleanField(default=True, verbose_name='BCA VA'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_mandiri',
            field=models.BooleanField(default=True, verbose_name='Mandiri VA'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_bni',
            field=models.BooleanField(default=True, verbose_name='BNI VA'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_bri',
            field=models.BooleanField(default=True, verbose_name='BRI VA'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_permata',
            field=models.BooleanField(default=False, verbose_name='Permata VA'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_cimb',
            field=models.BooleanField(default=False, verbose_name='CIMB Niaga VA'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_gopay',
            field=models.BooleanField(default=True, verbose_name='GoPay'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_ovo',
            field=models.BooleanField(default=True, verbose_name='OVO'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_dana',
            field=models.BooleanField(default=True, verbose_name='DANA'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_shopeepay',
            field=models.BooleanField(default=True, verbose_name='ShopeePay'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_linkaja',
            field=models.BooleanField(default=False, verbose_name='LinkAja'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='va_fee_percent',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Biaya tambahan khusus Virtual Account', max_digits=5, verbose_name='Biaya VA Bank (%)'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='ewallet_fee_percent',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Biaya tambahan khusus E-Wallet', max_digits=5, verbose_name='Biaya E-Wallet (%)'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='retail_fee_percent',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Biaya tambahan khusus Indomaret/Alfamart', max_digits=5, verbose_name='Biaya Convenience Store (%)'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='enable_qris',
            field=models.BooleanField(default=False, verbose_name='Aktifkan QRIS'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='qris_merchant_name',
            field=models.CharField(blank=True, help_text='Nama yang tampil di aplikasi e-wallet customer', max_length=200, null=True, verbose_name='Nama Merchant QRIS'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='qris_image',
            field=models.ImageField(blank=True, help_text='Upload QR Code statis QRIS (PNG/JPG, max 2MB)', null=True, upload_to='payments/qris/', verbose_name='Gambar QRIS'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='qris_fee_percent',
            field=models.DecimalField(decimal_places=2, default=0.7, help_text='Default 0.7% sesuai standar QRIS Indonesia', max_digits=5, verbose_name='Biaya QRIS (%)'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='qris_note',
            field=models.TextField(blank=True, help_text='Instruksi tambahan untuk customer saat bayar via QRIS', null=True, verbose_name='Catatan QRIS'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='confirmation_mode',
            field=models.CharField(choices=[('manual', 'Manual (customer klik "Saya sudah bayar")'), ('auto', 'Otomatis (perlu webhook / integrasi Midtrans)')], default='manual', max_length=10, verbose_name='Mode Konfirmasi Pembayaran'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='payment_expiry_hours',
            field=models.PositiveIntegerField(default=24, help_text='Customer harus membayar dalam waktu ini sebelum booking expire', verbose_name='Batas Waktu Pembayaran (jam)'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='min_payment_amount',
            field=models.DecimalField(decimal_places=0, default=0, help_text='Booking di bawah nominal ini wajib bayar di studio (0 = tanpa minimum)', max_digits=12, verbose_name='Minimum Nominal untuk Online Payment'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='accept_payment_247',
            field=models.BooleanField(default=True, help_text='Nonaktifkan untuk membatasi pembayaran di jam tertentu saja', verbose_name='Terima Pembayaran 24/7'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='working_hours_start',
            field=models.TimeField(blank=True, default='08:00', null=True, verbose_name='Jam Mulai Terima Pembayaran'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='working_hours_end',
            field=models.TimeField(blank=True, default='22:00', null=True, verbose_name='Jam Terakhir Terima Pembayaran'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='notification_email',
            field=models.EmailField(blank=True, help_text='Kosongkan jika ingin pakai email akun kamu', max_length=254, null=True, verbose_name='Email Notifikasi Pembayaran'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='notification_whatsapp',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='WhatsApp Notifikasi (08xxx)'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='notify_on_pending',
            field=models.BooleanField(default=True, verbose_name='Notif saat pembayaran pending'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='notify_on_paid',
            field=models.BooleanField(default=True, verbose_name='Notif saat pembayaran berhasil'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='notify_on_failed',
            field=models.BooleanField(default=True, verbose_name='Notif saat pembayaran gagal'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='notify_on_expired',
            field=models.BooleanField(default=True, verbose_name='Notif saat pembayaran expired'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='general_payment_note',
            field=models.TextField(blank=True, help_text='Catatan ini tampil di halaman instruksi pembayaran customer', null=True, verbose_name='Catatan Umum Pembayaran'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='refund_policy',
            field=models.TextField(blank=True, help_text='Jelaskan syarat & ketentuan refund kamu', null=True, verbose_name='Kebijakan Refund'),
        ),
        migrations.AddField(
            model_name='artistpaymentsettings',
            name='terms_accepted',
            field=models.BooleanField(default=False, verbose_name='Menyetujui Syarat & Ketentuan'),
        ),
    ]

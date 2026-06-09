from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class ServiceCategory(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=100, default="bi-palette",
                            help_text="Bootstrap icon class")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Service Categories"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Service(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Pemula'),
        ('intermediate', 'Menengah'),
        ('advanced', 'Mahir'),
        ('master', 'Master'),
    ]

    category = models.ForeignKey(
        ServiceCategory, on_delete=models.CASCADE,
        related_name='services', null=True, blank=True
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    short_desc = models.CharField(max_length=300, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    price_label = models.CharField(max_length=100, default="Mulai dari",
                                   help_text="Label harga, mis: 'Mulai dari' / 'Fix price'")
    duration = models.CharField(max_length=100, help_text="Estimasi waktu pengerjaan")
    difficulty = models.CharField(
        max_length=20, choices=DIFFICULTY_CHOICES, default='intermediate'
    )
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_popular = models.BooleanField(default=False, help_text="Tandai sebagai layanan populer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category__sort_order', 'name']

    def __str__(self):
        return self.name


class ServicePackage(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name='packages'
    )
    name = models.CharField(max_length=200, help_text="Nama paket, mis: Small / Medium / Large")
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    duration = models.CharField(max_length=100)
    is_recommended = models.BooleanField(default=False, help_text="Rekomendasikan paket ini")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.service.name} - {self.name}"


class Artist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    nickname = models.CharField(max_length=100, help_text="Nama panggilan / julukan")
    bio = models.TextField()
    short_bio = models.CharField(max_length=300, blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=1)
    photo = models.ImageField(upload_to='artists/', blank=True, null=True)
    photo_thumbnail = models.ImageField(upload_to='artists/thumbs/', blank=True, null=True)
    specialties = models.ManyToManyField(Service, related_name='artists', blank=True)
    is_available_mobile = models.BooleanField(
        default=True,
        verbose_name="Bisa panggil ke rumah",
        help_text="Bersedia datang ke lokasi customer"
    )
    is_available_studio = models.BooleanField(
        default=True,
        verbose_name="Bisa di studio",
        help_text="Melayani di studio"
    )
    mobile_fee = models.DecimalField(
        max_digits=10, decimal_places=0, default=50000,
        help_text="Biaya tambahan untuk panggilan ke rumah"
    )
    service_area = models.CharField(
        max_length=300,
        default="Seluruh area Bali",
        help_text="Wilayah layanan"
    )
    instagram = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.nickname} ({self.name})"


class Portfolio(models.Model):
    artist = models.ForeignKey(
        Artist, on_delete=models.CASCADE, related_name='portfolios'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='portfolios/')
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Portfolios"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.artist.nickname} - {self.title}"


class Booking(models.Model):
    MODE_CHOICES = [
        ('studio', 'Datang ke Studio'),
        ('mobile', 'Panggil ke Rumah'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Menunggu Konfirmasi'),
        ('confirmed', 'Dikonfirmasi'),
        ('in_progress', 'Sedang Dikerjakan'),
        ('completed', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    package = models.ForeignKey(
        ServicePackage, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='bookings'
    )
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='studio')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_date = models.DateField()
    booking_time = models.TimeField()
    location_address = models.TextField(
        blank=True, null=True,
        help_text="Alamat lengkap (diisi jika mode panggil ke rumah)"
    )
    notes = models.TextField(blank=True, null=True, help_text="Catatan tambahan")
    design_reference = models.ImageField(
        upload_to='references/', blank=True, null=True,
        help_text="Upload referensi desain (opsional)"
    )
    total_price = models.DecimalField(max_digits=12, decimal_places=0)
    travel_fee = models.DecimalField(
        max_digits=10, decimal_places=0, default=0,
        help_text="Biaya perjalanan (jika mode mobile)"
    )
    is_paid = models.BooleanField(default=False)

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Belum Dibayar'),
        ('pending', 'Menunggu Pembayaran'),
        ('paid', 'Lunas'),
        ('failed', 'Gagal'),
        ('refunded', 'Dikembalikan'),
    ]
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid'
    )
    transaction_id = models.CharField(max_length=200, blank=True, null=True,
                                       help_text="ID transaksi dari payment gateway")
    payment_method = models.CharField(max_length=100, blank=True, null=True,
                                       help_text="Metode pembayaran yang digunakan")
    paid_at = models.DateTimeField(blank=True, null=True)
    snap_token = models.CharField(max_length=500, blank=True, null=True,
                                   help_text="Snap token untuk Midtrans")

    # === Batas waktu & bukti bayar (SOP) ===
    payment_expires_at = models.DateTimeField(
        blank=True, null=True,
        help_text="Batas waktu customer untuk menyelesaikan pembayaran"
    )
    payment_confirmed_at = models.DateTimeField(
        blank=True, null=True,
        help_text="Waktu customer menekan tombol konfirmasi"
    )
    payment_proof = models.ImageField(
        upload_to='payments/proofs/', blank=True, null=True,
        help_text="Bukti pembayaran (foto struk / screenshot transfer)"
    )
    payment_proof_uploaded_at = models.DateTimeField(blank=True, null=True)

    VERIFICATION_CHOICES = [
        ('not_required', 'Tidak Perlu Verifikasi'),
        ('pending', 'Menunggu Verifikasi'),
        ('approved', 'Disetujui'),
        ('rejected', 'Ditolak'),
    ]
    payment_verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_CHOICES, default='not_required',
        help_text="Status verifikasi bukti pembayaran oleh artist"
    )
    payment_verification_note = models.TextField(
        blank=True, null=True,
        help_text="Catatan dari artist (alasan tolak / info approval)"
    )
    payment_verified_at = models.DateTimeField(blank=True, null=True)
    payment_verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verified_payments',
        help_text="Artist yang memverifikasi pembayaran"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date', '-booking_time']

    def __str__(self):
        return f"{self.user.username} - {self.artist.nickname} - {self.booking_date}"


class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} - {self.rating}/5"


class ArtistPaymentSettings(models.Model):
    """Payment gateway configuration per artist.

    Bank & e-wallet fields di sini adalah akun penampungan payout.
    enable_* flag menentukan metode mana yang ditawarkan ke customer.
    """

    artist = models.OneToOneField(
        Artist, on_delete=models.CASCADE, related_name='payment_settings'
    )

    accept_online_payment = models.BooleanField(
        default=True,
        verbose_name="Terima Pembayaran Online",
        help_text="Aktifkan payment gateway untuk pesanan kamu",
    )

    # === Enabled payment method groups ===
    enable_bank_va = models.BooleanField(default=True, verbose_name="Virtual Account Bank")
    enable_ewallet = models.BooleanField(default=True, verbose_name="E-Wallet")
    enable_credit_card = models.BooleanField(default=False, verbose_name="Kartu Kredit / Debit")
    enable_convenience_store = models.BooleanField(default=True, verbose_name="Convenience Store")

    # === Bank accounts (untuk payout) ===
    bank_bca_number = models.CharField(max_length=30, blank=True, null=True)
    bank_bca_name = models.CharField(max_length=200, blank=True, null=True)
    bank_mandiri_number = models.CharField(max_length=30, blank=True, null=True)
    bank_mandiri_name = models.CharField(max_length=200, blank=True, null=True)
    bank_bni_number = models.CharField(max_length=30, blank=True, null=True)
    bank_bni_name = models.CharField(max_length=200, blank=True, null=True)
    bank_bri_number = models.CharField(max_length=30, blank=True, null=True)
    bank_bri_name = models.CharField(max_length=200, blank=True, null=True)
    bank_permata_number = models.CharField(max_length=30, blank=True, null=True)
    bank_permata_name = models.CharField(max_length=200, blank=True, null=True)
    bank_cimb_number = models.CharField(max_length=30, blank=True, null=True)
    bank_cimb_name = models.CharField(max_length=200, blank=True, null=True)

    # === Per-bank enable / disable ===
    enable_bca = models.BooleanField(default=True, verbose_name="BCA VA")
    enable_mandiri = models.BooleanField(default=True, verbose_name="Mandiri VA")
    enable_bni = models.BooleanField(default=True, verbose_name="BNI VA")
    enable_bri = models.BooleanField(default=True, verbose_name="BRI VA")
    enable_permata = models.BooleanField(default=False, verbose_name="Permata VA")
    enable_cimb = models.BooleanField(default=False, verbose_name="CIMB Niaga VA")

    # === Per-ewallet enable / disable ===
    enable_gopay = models.BooleanField(default=True, verbose_name="GoPay")
    enable_ovo = models.BooleanField(default=True, verbose_name="OVO")
    enable_dana = models.BooleanField(default=True, verbose_name="DANA")
    enable_shopeepay = models.BooleanField(default=True, verbose_name="ShopeePay")
    enable_linkaja = models.BooleanField(default=False, verbose_name="LinkAja")

    # === E-wallet accounts (untuk payout) ===
    ewallet_gopay = models.CharField(max_length=30, blank=True, null=True,
                                      help_text="Nomor HP terdaftar di GoPay")
    ewallet_ovo = models.CharField(max_length=30, blank=True, null=True,
                                    help_text="Nomor HP terdaftar di OVO")
    ewallet_dana = models.CharField(max_length=30, blank=True, null=True,
                                     help_text="Nomor HP terdaftar di DANA")
    ewallet_shopeepay = models.CharField(max_length=30, blank=True, null=True)
    ewallet_linkaja = models.CharField(max_length=30, blank=True, null=True)

    # === Platform fee (opsional, jika artist mau kenakan biaya tambahan) ===
    platform_fee_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Biaya layanan tambahan dalam persen (0 = tanpa biaya)",
    )

    # === Midtrans split payment (advanced) ===
    use_split_payment = models.BooleanField(
        default=False,
        verbose_name="Gunakan Midtrans Split Payment",
        help_text="Untuk sistem marketplace / bagi hasil otomatis",
    )
    midtrans_merchant_id = models.CharField(
        max_length=200, blank=True, null=True,
        verbose_name="Midtrans Sub-Merchant ID",
    )

    # === Credit / Debit Card configuration ===
    CARD_METHOD_CHOICES = [
        ('edc', 'EDC Machine (terminal fisik di studio)'),
        ('link', 'Payment Link (customer bayar via link)'),
        ('manual', 'Manual Confirmation (konfirmasi via WhatsApp)'),
    ]

    card_processing_method = models.CharField(
        max_length=20, blank=True, null=True,
        choices=CARD_METHOD_CHOICES,
        verbose_name="Metode Proses Kartu",
        help_text="Bagaimana customer membayar via kartu",
    )
    card_payment_link = models.URLField(
        max_length=500, blank=True, null=True,
        verbose_name="Link Pembayaran Kartu",
        help_text="URL payment gateway atau form untuk customer bayar kartu (opsional)",
    )
    card_fee_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Biaya Proses Kartu (%)",
        help_text="Biaya tambahan yang dibebankan ke customer (contoh: 2.5 untuk 2.5%)",
    )
    card_note = models.TextField(
        blank=True, null=True,
        verbose_name="Catatan Pembayaran Kartu",
        help_text="Instruksi tambahan untuk customer (misal: 'Tap kartu di studio saat kedatangan')",
    )

    # === Per-method fees ===
    va_fee_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Biaya VA Bank (%)",
        help_text="Biaya tambahan khusus Virtual Account",
    )
    ewallet_fee_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Biaya E-Wallet (%)",
        help_text="Biaya tambahan khusus E-Wallet",
    )
    retail_fee_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Biaya Convenience Store (%)",
        help_text="Biaya tambahan khusus Indomaret/Alfamart",
    )

    # === QRIS ===
    enable_qris = models.BooleanField(default=False, verbose_name="Aktifkan QRIS")
    qris_merchant_name = models.CharField(
        max_length=200, blank=True, null=True,
        verbose_name="Nama Merchant QRIS",
        help_text="Nama yang tampil di aplikasi e-wallet customer",
    )
    qris_image = models.ImageField(
        upload_to='payments/qris/', blank=True, null=True,
        verbose_name="Gambar QRIS",
        help_text="Upload QR Code statis QRIS (PNG/JPG, max 2MB)",
    )
    qris_fee_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.7,
        verbose_name="Biaya QRIS (%)",
        help_text="Default 0.7% sesuai standar QRIS Indonesia",
    )
    qris_note = models.TextField(
        blank=True, null=True,
        verbose_name="Catatan QRIS",
        help_text="Instruksi tambahan untuk customer saat bayar via QRIS",
    )

    # === Payment behavior ===
    CONFIRMATION_CHOICES = [
        ('manual', 'Manual (customer klik "Saya sudah bayar")'),
        ('auto', 'Otomatis (perlu webhook / integrasi Midtrans)'),
    ]
    confirmation_mode = models.CharField(
        max_length=10, choices=CONFIRMATION_CHOICES, default='manual',
        verbose_name="Mode Konfirmasi Pembayaran",
    )
    payment_expiry_hours = models.PositiveIntegerField(
        default=24,
        verbose_name="Batas Waktu Pembayaran (jam)",
        help_text="Customer harus membayar dalam waktu ini sebelum booking expire",
    )
    min_payment_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name="Minimum Nominal untuk Online Payment",
        help_text="Booking di bawah nominal ini wajib bayar di studio (0 = tanpa minimum)",
    )

    # === Working hours ===
    accept_payment_247 = models.BooleanField(
        default=True,
        verbose_name="Terima Pembayaran 24/7",
        help_text="Nonaktifkan untuk membatasi pembayaran di jam tertentu saja",
    )
    working_hours_start = models.TimeField(
        blank=True, null=True, default='08:00',
        verbose_name="Jam Mulai Terima Pembayaran",
    )
    working_hours_end = models.TimeField(
        blank=True, null=True, default='22:00',
        verbose_name="Jam Terakhir Terima Pembayaran",
    )

    # === Notification settings ===
    notification_email = models.EmailField(
        blank=True, null=True,
        verbose_name="Email Notifikasi Pembayaran",
        help_text="Kosongkan jika ingin pakai email akun kamu",
    )
    notification_whatsapp = models.CharField(
        max_length=30, blank=True, null=True,
        verbose_name="WhatsApp Notifikasi (08xxx)",
    )
    notify_on_pending = models.BooleanField(
        default=True, verbose_name="Notif saat pembayaran pending"
    )
    notify_on_paid = models.BooleanField(
        default=True, verbose_name="Notif saat pembayaran berhasil"
    )
    notify_on_failed = models.BooleanField(
        default=True, verbose_name="Notif saat pembayaran gagal"
    )
    notify_on_expired = models.BooleanField(
        default=True, verbose_name="Notif saat pembayaran expired"
    )

    # === General notes / policies ===
    general_payment_note = models.TextField(
        blank=True, null=True,
        verbose_name="Catatan Umum Pembayaran",
        help_text="Catatan ini tampil di halaman instruksi pembayaran customer",
    )
    refund_policy = models.TextField(
        blank=True, null=True,
        verbose_name="Kebijakan Refund",
        help_text="Jelaskan syarat & ketentuan refund kamu",
    )
    terms_accepted = models.BooleanField(
        default=False,
        verbose_name="Menyetujui Syarat & Ketentuan",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment settings — {self.artist.nickname}"

    def get_enabled_methods(self):
        """Return list of payment type codes yang di-enable (termasuk per-bank/per-ewallet)."""
        methods = []
        if self.enable_bank_va:
            if getattr(self, 'enable_bca', True):     methods += ["bca_va"]
            if getattr(self, 'enable_mandiri', True): methods += ["mandiri_va"]
            if getattr(self, 'enable_bni', True):     methods += ["bni_va"]
            if getattr(self, 'enable_bri', True):     methods += ["bri_va"]
            if getattr(self, 'enable_permata', False): methods += ["permata_va"]
            if getattr(self, 'enable_cimb', False):   methods += ["cimb_va"]
            methods += ["bca_klikbca", "bca_klikpay", "bri_epay", "echannel", "other_va"]
        if self.enable_ewallet:
            if getattr(self, 'enable_gopay', True):     methods += ["gopay"]
            if getattr(self, 'enable_shopeepay', True): methods += ["shopeepay"]
            if getattr(self, 'enable_dana', True):      methods += ["dana"]
            if getattr(self, 'enable_ovo', True):       methods += ["ovo"]
            if getattr(self, 'enable_linkaja', False):  methods += ["linkaja"]
        if getattr(self, 'enable_qris', False):
            methods += ["qris"]
        if self.enable_convenience_store:
            methods += ["indomaret", "alfamart"]
        if self.enable_credit_card:
            methods += ["credit_card"]
        return methods

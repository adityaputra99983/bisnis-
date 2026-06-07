"""Custom payment gateway (tanpa external API).

Alur SOP-compliant:
1. Customer pilih metode di payment_page.html
2. payment_initiate() membuat payment session (transaction_id) + set expires_at
3. Untuk metode retail (Indomaret/Alfamart) & kartu manual:
   - Customer wajib upload bukti pembayaran
   - Status booking → "menunggu verifikasi" (payment_verification_status='pending')
4. Untuk metode lain (bank VA / e-wallet / QRIS real-time):
   - Customer cukup klik "Saya sudah bayar" → langsung confirmed
5. Artist/admin verifikasi bukti bayar:
   - Approve → payment_status='paid' + booking.status='confirmed'
   - Reject  → payment_verification_status='rejected', customer bisa upload ulang
6. Jika expires_at terlewat → booking.payment_status='failed' (auto-expire)

Fungsi-fungsi di sini:
- generate_payment_session(): buat transaction_id & set expires_at
- get_payment_instructions(method, booking): return dict instruksi per metode
- mark_booking_as_paid(booking, method, proof_file): set status sesuai SOP
- verify_payment_proof(booking, action, note, by): approve/reject oleh artist
- METHOD_LABELS, METHOD_GROUPS, METHOD_REQUIRES_PROOF: konstanta
"""

import uuid
from django.utils import timezone
from datetime import timedelta


# ===== Konstanta metode pembayaran =====

METHOD_LABELS = {
    # Bank VA
    'bca_va':      {'group': 'bank_va', 'name_id': 'BCA Virtual Account',      'name_en': 'BCA Virtual Account'},
    'mandiri_va':  {'group': 'bank_va', 'name_id': 'Mandiri Virtual Account',  'name_en': 'Mandiri Virtual Account'},
    'bni_va':      {'group': 'bank_va', 'name_id': 'BNI Virtual Account',      'name_en': 'BNI Virtual Account'},
    'bri_va':      {'group': 'bank_va', 'name_id': 'BRI Virtual Account',      'name_en': 'BRI Virtual Account'},
    'permata_va':  {'group': 'bank_va', 'name_id': 'Permata Virtual Account',  'name_en': 'Permata Virtual Account'},
    'cimb_va':     {'group': 'bank_va', 'name_id': 'CIMB Niaga VA',            'name_en': 'CIMB Niaga VA'},
    # E-Wallet
    'gopay':       {'group': 'ewallet', 'name_id': 'GoPay',  'name_en': 'GoPay'},
    'shopeepay':   {'group': 'ewallet', 'name_id': 'ShopeePay', 'name_en': 'ShopeePay'},
    'dana':        {'group': 'ewallet', 'name_id': 'DANA',   'name_en': 'DANA'},
    'ovo':         {'group': 'ewallet', 'name_id': 'OVO',    'name_en': 'OVO'},
    'linkaja':     {'group': 'ewallet', 'name_id': 'LinkAja', 'name_en': 'LinkAja'},
    # Convenience Store
    'indomaret':   {'group': 'retail', 'name_id': 'Indomaret', 'name_en': 'Indomaret'},
    'alfamart':    {'group': 'retail', 'name_id': 'Alfamart',  'name_en': 'Alfamart'},
    # Credit / Debit Card
    'credit_card': {'group': 'credit_card', 'name_id': 'Kartu Kredit / Debit', 'name_en': 'Credit / Debit Card'},
    # QRIS
    'qris': {'group': 'qris', 'name_id': 'QRIS', 'name_en': 'QRIS'},
}

METHOD_TO_ACCOUNT_KEY = {
    'bca_va': 'bca', 'mandiri_va': 'mandiri', 'bni_va': 'bni',
    'bri_va': 'bri', 'permata_va': 'permata', 'cimb_va': 'cimb',
    'gopay': 'gopay', 'ovo': 'ovo', 'dana': 'dana',
    'shopeepay': 'shopeepay', 'linkaja': 'linkaja',
    'indomaret': 'indomaret', 'alfamart': 'alfamart',
    'credit_card': 'credit_card',
    'qris': 'qris',
}

METHOD_LOGO = {
    'bca_va': 'bca.svg', 'mandiri_va': 'mandiri.svg',
    'bni_va': 'bni.svg', 'bri_va': 'bri.svg',
    'permata_va': 'permata.svg', 'cimb_va': 'cimb.svg',
    'gopay': 'gopay.svg', 'ovo': 'ovo.svg', 'dana': 'dana.svg',
    'shopeepay': 'shopeepay.svg', 'linkaja': 'linkaja.svg',
    'indomaret': 'indomaret.svg', 'alfamart': 'alfamart.svg',
    'credit_card': 'card.svg',
    'qris': 'qris.svg',
}

CARD_BRANDS = ['visa', 'mastercard', 'jcb', 'amex']


# ===== SOP: metode yang WAJIB upload bukti pembayaran =====
# Full SOP: SEMUA metode pembayaran wajib upload bukti.
# Override per-metode di sini jika ada yang dikecualikan.
METHOD_REQUIRES_PROOF = {
    # Retail / tunai
    'indomaret':   True,
    'alfamart':    True,
    # Credit / Debit Card
    'credit_card': True,
    # Bank VA
    'bca_va':      True,
    'mandiri_va':  True,
    'bni_va':      True,
    'bri_va':      True,
    'permata_va':  True,
    'cimb_va':     True,
    # E-Wallet
    'gopay':       True,
    'shopeepay':   True,
    'dana':        True,
    'ovo':         True,
    'linkaja':     True,
    # QRIS
    'qris':        True,
}


def method_requires_proof(method):
    """Return True jika metode ini mewajibkan upload bukti pembayaran.

    Full SOP: semua metode wajib upload bukti bayar yang akan diverifikasi
    oleh artist sebelum booking dikonfirmasi.
    """
    if method in METHOD_REQUIRES_PROOF:
        return METHOD_REQUIRES_PROOF[method]
    return True  # default full SOP: semua metode wajib upload bukti


def is_payment_expired(booking):
    """Return True jika payment sudah lewat batas waktu."""
    if not booking.payment_expires_at:
        return False
    if booking.payment_status in ('paid', 'failed', 'refunded'):
        return False
    return timezone.now() > booking.payment_expires_at


# ===== Payment Session =====

def generate_payment_session(booking):
    """Buat transaction_id + set expires_at. Idempotent untuk transaction_id."""
    from django.conf import settings as dj_settings

    expiry_hours = getattr(dj_settings, 'PAYMENT_EXPIRY_HOURS', 24)
    if not booking.transaction_id:
        booking.transaction_id = f"TATTOO-{booking.id}-{uuid.uuid4().hex[:8].upper()}"
    if not booking.payment_expires_at:
        booking.payment_expires_at = timezone.now() + timedelta(hours=expiry_hours)
    if booking.payment_status not in ('paid', 'failed', 'refunded'):
        booking.payment_status = 'pending'
    booking.save(update_fields=['transaction_id', 'payment_expires_at', 'payment_status'])
    return booking.transaction_id


# ===== Payment Instructions =====

def get_payment_instructions(method, booking, accounts):
    """Return dict instruksi pembayaran untuk metode tertentu.

    accounts: dict dari settings.PLATFORM_PAYMENT_ACCOUNTS
    """
    account_key = METHOD_TO_ACCOUNT_KEY.get(method)
    label = METHOD_LABELS.get(method, {}).get('name_id', method)

    if not account_key or account_key not in accounts:
        return None

    info = accounts[account_key]
    group = METHOD_LABELS.get(method, {}).get('group')

    base = {
        'method': method,
        'method_label': label,
        'method_logo': METHOD_LOGO.get(method),
        'group': group,
        'amount': int(booking.total_price),
        'transaction_id': booking.transaction_id,
        'booking_id': booking.id,
        'requires_proof': method_requires_proof(method),
        'expires_at': booking.payment_expires_at.isoformat() if booking.payment_expires_at else None,
    }

    # Helper: tambahkan langkah SOP upload bukti di akhir instruksi
    sop_upload_steps = []
    if base['requires_proof']:
        sop_upload_steps = [
            "Screenshot / foto bukti pembayaran dari aplikasi atau struk kasir",
            "Upload foto bukti di form konfirmasi di bawah",
            "Centang pernyataan SOP, lalu klik 'Kirim Bukti Pembayaran'",
            "Booking akan berstatus 'Menunggu Verifikasi' sampai artist memverifikasi",
        ]

    if group == 'bank_va':
        base.update({
            'type': 'bank_transfer',
            'bank_name': info['bank_name'],
            'account_number': info['account_number'],
            'account_name': info['account_name'],
            'instructions': [
                f"Buka aplikasi {info['bank_name']} mobile / internet banking",
                f"Pilih menu Transfer → Virtual Account / Antar Rekening",
                f"Masukkan nomor: {info['account_number']}",
                f"Masukkan nominal: Rp {int(booking.total_price):,}",
                f"Simpan / konfirmasi — pastikan nama tujuan: {info['account_name']}",
            ] + sop_upload_steps,
        })
    elif group == 'ewallet':
        base.update({
            'type': 'ewallet',
            'provider': info['provider'],
            'number': info['number'],
            'name': info['name'],
            'instructions': [
                f"Buka aplikasi {info['provider']}",
                f"Pilih menu Kirim / Transfer",
                f"Masukkan nomor tujuan: {info['number']}",
                f"a.n. {info['name']}",
                f"Kirim nominal: Rp {int(booking.total_price):,}",
            ] + sop_upload_steps,
        })
    elif group == 'retail':
        prefix = info.get('payment_code_prefix', 'TATTOO')
        payment_code = f"{prefix}-{booking.id:04d}-{uuid.uuid4().hex[:6].upper()}"
        base.update({
            'type': 'retail',
            'provider': info['provider'],
            'payment_code': payment_code,
            'instructions': [
                f"Datang ke kasir {info['provider']} terdekat",
                f"Berikan kode pembayaran: {payment_code}",
                f"Bayar tunai sebesar: Rp {int(booking.total_price):,}",
                "Simpan struk sebagai bukti pembayaran yang sah",
            ] + sop_upload_steps,
        })
    elif group == 'credit_card':
        card_info = info or {}
        processing = card_info.get('processing_method', 'manual')
        link = card_info.get('payment_link') or ''
        note = card_info.get('note') or ''
        fee_pct = float(card_info.get('fee_percent', 0) or 0)
        base_amount = int(booking.total_price)
        total_with_fee = int(base_amount * (1 + fee_pct / 100)) if fee_pct else base_amount

        instructions = []
        if processing == 'edc':
            instructions = [
                "Datang ke studio sesuai jadwal yang sudah disepakati",
                "Sebutkan nama pemesanan kamu kepada artist",
                "Artist akan memproses pembayaran melalui mesin EDC (Visa/Mastercard/JCB/Amex)",
                f"Total yang akan ditagihkan: Rp {total_with_fee:,}" + (f" (sudah termasuk biaya proses {fee_pct}%)" if fee_pct else ""),
            ]
        elif processing == 'link' and link:
            instructions = [
                f"Klik link pembayaran berikut untuk membayar via kartu:",
                link,
                "Login atau masukkan detail kartu kamu di halaman pembayaran",
                f"Selesaikan pembayaran sebesar Rp {total_with_fee:,}" + (f" (sudah termasuk biaya proses {fee_pct}%)" if fee_pct else ""),
                "Setelah pembayaran berhasil, kembali ke halaman ini",
            ]
        elif processing == 'link':
            instructions = [
                "Artist akan mengirim link pembayaran kartu via WhatsApp",
                f"Total yang harus dibayar: Rp {total_with_fee:,}" + (f" (sudah termasuk biaya proses {fee_pct}%)" if fee_pct else ""),
                "Buka link dari WhatsApp dan masukkan detail kartu kamu",
                "Setelah pembayaran berhasil, kembali ke halaman ini",
            ]
        else:  # manual / fallback
            instructions = [
                "Hubungi artist via WhatsApp untuk konfirmasi pembayaran kartu",
                f"Total yang harus dibayar: Rp {total_with_fee:,}" + (f" (sudah termasuk biaya proses {fee_pct}%)" if fee_pct else ""),
                "Siapkan kartu kamu (Visa / Mastercard / JCB / Amex)",
            ]

        if note:
            instructions.append(f"Catatan dari artist: {note}")

        # Tambahkan SOP upload steps
        instructions.extend(sop_upload_steps)

        base.update({
            'type': 'credit_card',
            'processing_method': processing,
            'payment_link': link,
            'fee_percent': fee_pct,
            'total_with_fee': total_with_fee,
            'note': note,
            'card_brands': CARD_BRANDS,
            'instructions': instructions,
        })
    elif group == 'qris':
        qris_info = info or {}
        fee_pct = float(qris_info.get('fee_percent', 0) or 0)
        base_amount = int(booking.total_price)
        total_with_fee = int(base_amount * (1 + fee_pct / 100)) if fee_pct else base_amount
        qris_note = qris_info.get('note', '') or ''
        base.update({
            'type': 'qris',
            'qris_image': qris_info.get('image_url', ''),
            'merchant_name': qris_info.get('merchant_name', ''),
            'fee_percent': fee_pct,
            'total_with_fee': total_with_fee,
            'note': qris_note,
            'instructions': [
                f"Buka aplikasi e-wallet kamu (GoPay / OVO / DANA / ShopeePay / mobile banking)",
                f"Pilih menu Bayar / Scan QR",
                "Scan QR Code QRIS yang ditampilkan",
                f"Pastikan merchant: {qris_info.get('merchant_name', '')}",
                f"Bayar sebesar Rp {total_with_fee:,}" + (f" (sudah termasuk biaya QRIS {fee_pct}%)" if fee_pct else ""),
            ] + sop_upload_steps + ([f"Catatan: {qris_note}"] if qris_note else []),
        })
    else:
        return None

    return base


# ===== Mark as Paid (SOP-compliant) =====

def mark_booking_as_paid(booking, method, proof_file=None, verified_by=None):
    """Tandai booking sesuai SOP.

    - Untuk metode yang requires_proof: simpan bukti, set verifikasi='pending'.
      Status booking TIDAK langsung confirmed — menunggu approval artist.
    - Untuk metode real-time (VA, e-wallet, QRIS): langsung paid + confirmed.

    Return (success, error_message).
    """
    valid_methods = set(METHOD_LABELS.keys())
    if method not in valid_methods:
        return False, 'Metode pembayaran tidak valid.'

    if booking.payment_status == 'paid':
        return True, None  # idempotent

    requires_proof = method_requires_proof(method)
    now = timezone.now()

    booking.payment_method = METHOD_LABELS.get(method, {}).get('name_id', method)
    booking.payment_confirmed_at = now
    booking.payment_expires_at = None  # sesi pembayaran sudah dipakai

    if requires_proof:
        # Wajib ada bukti bayar → status 'pending' menunggu verifikasi
        if not proof_file:
            return False, 'Bukti pembayaran wajib diupload untuk metode ini.'

        # Simpan file bukti
        booking.payment_proof = proof_file
        booking.payment_proof_uploaded_at = now
        booking.payment_verification_status = 'pending'
        booking.payment_verification_note = None
        booking.payment_verified_at = None
        booking.payment_verified_by = None

        # Status pembayaran: pending (artinya customer sudah submit, belum diverifikasi)
        # Status booking TIDAK diubah ke confirmed — tetap 'pending' sampai artist approve
        booking.payment_status = 'pending'
        booking.is_paid = False
    else:
        # Real-time method: langsung paid + confirmed
        booking.payment_status = 'paid'
        booking.is_paid = True
        booking.paid_at = now
        booking.payment_verification_status = 'not_required'
        booking.status = 'confirmed'

    booking.save()
    return True, None


# ===== Verifikasi bukti oleh artist =====

def verify_payment_proof(booking, action, note='', by=None):
    """Approve / reject bukti pembayaran oleh artist.

    action: 'approve' atau 'reject'
    note  : catatan (wajib untuk reject)
    by    : User yang memverifikasi

    Return (success, error_message).
    """
    if booking.payment_verification_status != 'pending':
        return False, 'Pembayaran ini tidak dalam status menunggu verifikasi.'

    action = (action or '').strip().lower()
    note = (note or '').strip()
    now = timezone.now()

    if action == 'approve':
        booking.payment_verification_status = 'approved'
        booking.payment_verification_note = note or None
        booking.payment_verified_at = now
        booking.payment_verified_by = by
        booking.payment_status = 'paid'
        booking.is_paid = True
        if not booking.paid_at:
            booking.paid_at = now
        booking.status = 'confirmed'
        booking.save()
        return True, None

    if action == 'reject':
        if not note:
            return False, 'Wajib berikan alasan penolakan untuk customer.'
        booking.payment_verification_status = 'rejected'
        booking.payment_verification_note = note
        booking.payment_verified_at = now
        booking.payment_verified_by = by
        booking.save()
        return True, None

    return False, 'Aksi tidak valid. Gunakan "approve" atau "reject".'


def expire_payment_if_needed(booking):
    """Auto-expire booking jika lewat batas waktu & belum lunas.

    Return True jika status baru saja diubah jadi failed.
    """
    if not is_payment_expired(booking):
        return False
    booking.payment_status = 'failed'
    booking.payment_expires_at = None
    booking.save(update_fields=['payment_status', 'payment_expires_at'])
    return True

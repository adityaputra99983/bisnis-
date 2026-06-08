/* =====================================================================
   booking.js — Interaktivitas form booking
   - Filter paket berdasarkan layanan yang dipilih
   - Toggle field alamat berdasarkan mode (studio / mobile)
   - Ringkasan harga & detail booking real-time di sidebar
   - Progress indicator step yang sudah terisi
   - Highlight step cards yang punya field error
   - Inisialisasi summary dari form value (untuk re-render setelah submit)
   ===================================================================== */
(function () {
    'use strict';

    const dataEl = document.getElementById('booking-form-data');
    const formEl = document.getElementById('booking-form');
    if (!dataEl || !formEl) return;

    let DATA;
    try {
        DATA = JSON.parse(dataEl.textContent || '{}');
    } catch (e) {
        console.error('[booking] Gagal parse data:', e);
        return;
    }

    const services = DATA.services || [];
    const packages = DATA.packages || [];
    const artists = DATA.artists || [];

    const $service = formEl.querySelector('[data-booking-field="service"]');
    const $package = formEl.querySelector('[data-booking-field="package"]');
    const $artist = formEl.querySelector('[data-booking-field="artist"]');
    const $date = formEl.querySelector('[data-booking-field="date"]');
    const $time = formEl.querySelector('[data-booking-field="time"]');
    const $modeRadios = formEl.querySelectorAll('input[name="mode"]');
    const $locationField = document.getElementById('location-field');

    /* ---------- Helpers ---------- */
    function fmtIDR(num) {
        if (num === null || num === undefined || isNaN(num)) return 'Rp 0';
        return 'Rp ' + Math.round(num).toLocaleString('id-ID');
    }

    function selectedMode() {
        const checked = formEl.querySelector('input[name="mode"]:checked');
        return checked ? checked.value : null;
    }

    function findService(id) {
        if (!id) return null;
        return services.find((s) => String(s.id) === String(id)) || null;
    }

    function findPackage(id) {
        if (!id) return null;
        return packages.find((p) => String(p.id) === String(id)) || null;
    }

    function findArtist(id) {
        if (!id) return null;
        return artists.find((a) => String(a.id) === String(id)) || null;
    }

    /* ---------- Filter paket berdasarkan layanan ---------- */
    function filterPackagesByService() {
        if (!$service || !$package) return;
        const serviceId = $service.value;
        const currentPkg = $package.value;
        let firstMatch = '';
        let matchCount = 0;

        Array.from($package.options).forEach((opt) => {
            if (!opt.value) {
                opt.hidden = false;
                opt.disabled = false;
                return;
            }
            const optService = opt.getAttribute('data-service');
            const matches = !serviceId || String(optService) === String(serviceId);
            opt.hidden = !matches;
            opt.disabled = !matches;
            if (matches) {
                matchCount += 1;
                if (!firstMatch) firstMatch = opt.value;
            }
        });

        // Reset jika paket sebelumnya tidak cocok lagi
        const stillValid = Array.from($package.options).some(
            (o) => o.value === currentPkg && !o.hidden
        );
        if (!stillValid) {
            $package.value = '';
        }

        // Hint paket
        const hint = document.getElementById('package-hint');
        if (hint) {
            if (!serviceId) {
                hint.textContent = 'Paket akan muncul setelah memilih layanan.';
            } else if (matchCount === 0) {
                hint.textContent = 'Belum ada paket untuk layanan ini — kamu bisa lanjut tanpa paket.';
            } else {
                hint.textContent = matchCount + ' paket tersedia. Pilih jika ada paket yang cocok, atau biarkan kosong.';
            }
        }
    }

    /* ---------- Tampilkan ringkasan artist ---------- */
    function updateArtistInfo() {
        if (!$artist) return;
        const box = document.getElementById('artist-info');
        if (!box) return;
        const artist = findArtist($artist.value);
        if (!artist) {
            box.style.display = 'none';
            return;
        }
        box.style.display = '';
        const studioEl = document.getElementById('aqi-studio');
        const mobileEl = document.getElementById('aqi-mobile');
        const feeEl = document.getElementById('aqi-fee');
        if (studioEl) studioEl.textContent = artist.studio ? 'Ya' : 'Tidak';
        if (mobileEl) mobileEl.textContent = artist.mobile ? 'Ya' : 'Tidak';
        if (feeEl) feeEl.textContent = artist.mobile ? fmtIDR(artist.mobile_fee) : '-';
    }

    /* ---------- Toggle field alamat berdasarkan mode ---------- */
    function toggleLocationField() {
        if (!$locationField) return;
        const mode = selectedMode();
        $locationField.style.display = mode === 'mobile' ? '' : 'none';
    }

    /* ---------- Update ringkasan di sidebar ---------- */
    function updateSummary() {
        const service = findService($service && $service.value);
        const pkg = findPackage($package && $package.value);
        const artist = findArtist($artist && $artist.value);
        const mode = selectedMode();

        function setVal(key, value) {
            formEl.querySelectorAll(`[data-summary="${key}"]`).forEach((el) => {
                if (!value) {
                    el.textContent = '—';
                    el.classList.add('is-empty');
                } else {
                    el.textContent = value;
                    el.classList.remove('is-empty');
                }
            });
        }

        function setPrice(key, value) {
            formEl.querySelectorAll(`[data-summary="${key}"]`).forEach((el) => {
                el.textContent = fmtIDR(value);
                el.classList.remove('is-empty');
            });
        }

        setVal('service', service ? service.name : null);
        setVal('package', pkg ? pkg.name : null);
        setVal('artist', artist ? artist.nickname : null);
        setVal(
            'mode',
            mode === 'studio'
                ? 'Datang ke Studio'
                : mode === 'mobile'
                ? 'Panggil ke Rumah'
                : null
        );
        setVal('duration', pkg ? pkg.duration : service ? service.duration : null);

        let dateText = null;
        if ($date && $date.value) {
            try {
                const d = new Date($date.value + 'T00:00:00');
                dateText = d.toLocaleDateString('id-ID', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                });
            } catch (e) {
                dateText = $date.value;
            }
        }
        setVal('date', dateText);
        setVal('time', $time && $time.value ? $time.value + ' WITA' : null);

        // Harga: paket (jika ada) > layanan
        let basePrice = 0;
        if (pkg) basePrice = Number(pkg.price) || 0;
        else if (service) basePrice = Number(service.price) || 0;

        // Travel fee
        let travelFee = 0;
        if (mode === 'mobile' && artist) {
            travelFee = Number(artist.mobile_fee) || 0;
        }

        const total = basePrice + travelFee;

        const travelBlock = formEl.querySelector('[data-summary-block="travel"]');

        setPrice('base-price', basePrice);
        setPrice('travel-fee', travelFee);
        if (travelBlock) travelBlock.style.display = travelFee > 0 ? '' : 'none';
        setPrice('total', total);
    }

    /* ---------- Progress indicator step ---------- */
    function updateStepProgress() {
        const completed = {
            1: Boolean($service && $service.value),
            2: Boolean($artist && $artist.value),
            3: Boolean(selectedMode()),
            4: Boolean($date && $date.value && $time && $time.value),
            5: true, // step 5 selalu opsional
        };

        // Cari step aktif berikutnya (yang belum lengkap)
        let activeStep = 5;
        for (let i = 1; i <= 5; i += 1) {
            if (!completed[i]) {
                activeStep = i;
                break;
            }
        }

        // Update progress bar di atas
        document.querySelectorAll('[data-step-indicator]').forEach((el) => {
            const n = Number(el.getAttribute('data-step-indicator'));
            el.classList.toggle('is-done', n < activeStep && completed[n]);
            el.classList.toggle('is-active', n === activeStep);
        });

        // Update step cards
        document.querySelectorAll('.booking-step-card').forEach((card) => {
            const n = Number(card.getAttribute('data-step'));
            card.classList.toggle('is-active', n === activeStep);
            card.classList.toggle('is-completed', n < activeStep && completed[n]);
        });

        // Tandai garis di progress
        document.querySelectorAll('.bfp-line').forEach((line, i) => {
            const stepBefore = i + 1;
            line.classList.toggle('is-done', completed[stepBefore] && stepBefore < activeStep);
        });
    }

    /* ---------- Tandai step card yang punya field error ---------- */
    function markErrorSteps() {
        document.querySelectorAll('.booking-step-card').forEach((card) => {
            const hasError = card.querySelector('.field-error');
            card.classList.toggle('has-error', Boolean(hasError));
            if (hasError) {
                const field = card.querySelector('.form-control, .form-select');
                if (field) field.classList.add('is-invalid');
            }
        });
    }

    /* ---------- Cegah submit jika mode mobile tapi alamat kosong ---------- */
    function attachClientValidation() {
        formEl.addEventListener('submit', (e) => {
            const mode = selectedMode();
            const addr = formEl.querySelector('[name="location_address"]');
            if (mode === 'mobile' && addr && !addr.value.trim()) {
                e.preventDefault();
                addr.focus();
                addr.classList.add('is-invalid');
                addr.style.borderColor = '#dc3545';
                if ($locationField) {
                    $locationField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }

    /* ---------- Bind events ---------- */
    function refresh() {
        filterPackagesByService();
        updateArtistInfo();
        toggleLocationField();
        updateSummary();
        updateStepProgress();
    }

    if ($service) $service.addEventListener('change', refresh);
    if ($package) $package.addEventListener('change', refresh);
    if ($artist) $artist.addEventListener('change', refresh);
    if ($date) $date.addEventListener('change', refresh);
    if ($time) $time.addEventListener('change', refresh);
    $modeRadios.forEach((r) => r.addEventListener('change', refresh));

    attachClientValidation();

    // PENTING: inisialisasi ulang saat halaman sudah siap
    // (untuk menangkap data dari form yang di-render ulang setelah submit)
    function boot() {
        refresh();
        markErrorSteps();
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();

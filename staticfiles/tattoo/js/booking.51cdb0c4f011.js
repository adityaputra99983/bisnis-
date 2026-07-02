(function () {
    'use strict';

    var dataEl = document.getElementById('booking-form-data');
    var formEl = document.getElementById('booking-form');
    if (!dataEl || !formEl) return;

    var DATA;
    try {
        DATA = JSON.parse(dataEl.textContent || '{}');
    } catch (e) {
        return;
    }

    var services = DATA.services || [];
    var packages = DATA.packages || [];
    var artists = DATA.artists || [];

    var $service = formEl.querySelector('[data-booking-field="service"]');
    var $package = formEl.querySelector('[data-booking-field="package"]');
    var $artist = formEl.querySelector('[data-booking-field="artist"]');
    var $date = formEl.querySelector('[data-booking-field="date"]');
    var $time = formEl.querySelector('[data-booking-field="time"]');
    var $modeRadios = formEl.querySelectorAll('input[name="mode"]');
    var $locationField = document.getElementById('location-field');

    var $packageOptions = $package ? Array.from($package.options) : [];
    var $summaryService = formEl.querySelector('[data-summary="service"]');
    var $summaryPackage = formEl.querySelector('[data-summary="package"]');
    var $summaryArtist = formEl.querySelector('[data-summary="artist"]');
    var $summaryMode = formEl.querySelector('[data-summary="mode"]');
    var $summaryDuration = formEl.querySelector('[data-summary="duration"]');
    var $summaryDate = formEl.querySelector('[data-summary="date"]');
    var $summaryTime = formEl.querySelector('[data-summary="time"]');
    var $summaryBasePrice = formEl.querySelector('[data-summary="base-price"]');
    var $summaryTravelFee = formEl.querySelector('[data-summary="travel-fee"]');
    var $summaryTotal = formEl.querySelector('[data-summary="total"]');
    var $travelBlock = formEl.querySelector('[data-summary-block="travel"]');
    var $artistInfo = document.getElementById('artist-info');
    var $aqiStudio = document.getElementById('aqi-studio');
    var $aqiMobile = document.getElementById('aqi-mobile');
    var $aqiFee = document.getElementById('aqi-fee');
    var $packageHint = document.getElementById('package-hint');
    var $stepIndicators = document.querySelectorAll('[data-step-indicator]');
    var $stepCards = document.querySelectorAll('.booking-step-card');
    var $bfpLines = document.querySelectorAll('.bfp-line');

    var lastServiceId = null;
    var lastArtistId = null;
    var lastMode = null;

    var $submitBtn = formEl.querySelector('button[type="submit"]');
    var originalBtnHTML = $submitBtn ? $submitBtn.innerHTML : '';
    var isSubmitting = false;

    function fmtIDR(num) {
        if (num === null || num === undefined || isNaN(num)) return 'Rp 0';
        return 'Rp ' + Math.round(num).toLocaleString('id-ID');
    }

    function selectedMode() {
        var checked = formEl.querySelector('input[name="mode"]:checked');
        return checked ? checked.value : null;
    }

    function findService(id) {
        if (!id) return null;
        return services.find(function (s) { return String(s.id) === String(id); }) || null;
    }

    function findPackage(id) {
        if (!id) return null;
        return packages.find(function (p) { return String(p.id) === String(id); }) || null;
    }

    function findArtist(id) {
        if (!id) return null;
        return artists.find(function (a) { return String(a.id) === String(id); }) || null;
    }

    function filterPackagesByService() {
        if (!$service || !$package || !$packageOptions.length) return;
        var serviceId = $service.value;
        if (serviceId === lastServiceId) return;
        lastServiceId = serviceId;

        var currentPkg = $package.value;
        var firstMatch = '';
        var matchCount = 0;
        var i, opt, optService, matches;

        for (i = 0; i < $packageOptions.length; i++) {
            opt = $packageOptions[i];
            if (!opt.value) {
                opt.hidden = false;
                opt.disabled = false;
                continue;
            }
            optService = opt.getAttribute('data-service');
            matches = !serviceId || String(optService) === String(serviceId);
            opt.hidden = !matches;
            opt.disabled = !matches;
            if (matches) {
                matchCount++;
                if (!firstMatch) firstMatch = opt.value;
            }
        }

        if (currentPkg) {
            var stillValid = false;
            for (i = 0; i < $packageOptions.length; i++) {
                if ($packageOptions[i].value === currentPkg && !$packageOptions[i].hidden) {
                    stillValid = true;
                    break;
                }
            }
            if (!stillValid) $package.value = '';
        }

        if ($packageHint) {
            if (!serviceId) {
                $packageHint.textContent = 'Paket akan muncul setelah memilih layanan.';
            } else if (matchCount === 0) {
                $packageHint.textContent = 'Belum ada paket untuk layanan ini — kamu bisa lanjut tanpa paket.';
            } else {
                $packageHint.textContent = matchCount + ' paket tersedia. Pilih jika ada paket yang cocok, atau biarkan kosong.';
            }
        }
    }

    function updateArtistInfo() {
        if (!$artist || !$artistInfo) return;
        var id = $artist.value;
        if (id === lastArtistId) return;
        lastArtistId = id;

        var artist = findArtist(id);
        if (!artist) {
            $artistInfo.style.display = 'none';
            return;
        }
        $artistInfo.style.display = '';
        if ($aqiStudio) $aqiStudio.textContent = artist.s ? 'Ya' : 'Tidak';
        if ($aqiMobile) $aqiMobile.textContent = artist.m ? 'Ya' : 'Tidak';
        if ($aqiFee) $aqiFee.textContent = artist.m ? fmtIDR(artist.mf) : '-';
    }

    function toggleLocationField() {
        if (!$locationField) return;
        var mode = selectedMode();
        if (mode === lastMode) return;
        lastMode = mode;
        $locationField.style.display = mode === 'mobile' ? '' : 'none';
    }

    function updateSummary() {
        var service = $service && $service.value ? findService($service.value) : null;
        var pkg = $package && $package.value ? findPackage($package.value) : null;
        var artist = $artist && $artist.value ? findArtist($artist.value) : null;
        var mode = selectedMode();

        if ($summaryService) $summaryService.textContent = service ? service.n : '—';
        if ($summaryPackage) $summaryPackage.textContent = pkg ? pkg.n : '—';
        if ($summaryArtist) $summaryArtist.textContent = artist ? artist.nn : '—';

        if ($summaryMode) {
            $summaryMode.textContent = mode === 'studio' ? 'Datang ke Studio' : mode === 'mobile' ? 'Panggil ke Rumah' : '—';
        }

        if ($summaryDuration) {
            $summaryDuration.textContent = pkg ? pkg.d : service ? service.d : '—';
        }

        if ($summaryDate && $date && $date.value) {
            try {
                var d = new Date($date.value + 'T00:00:00');
                $summaryDate.textContent = d.toLocaleDateString('id-ID', {
                    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
                });
            } catch (e) {
                $summaryDate.textContent = $date.value;
            }
        } else if ($summaryDate) {
            $summaryDate.textContent = '—';
        }

        if ($summaryTime) {
            $summaryTime.textContent = $time && $time.value ? $time.value + ' WITA' : '—';
        }

        var basePrice = 0;
        if (pkg) basePrice = Number(pkg.p) || 0;
        else if (service) basePrice = Number(service.p) || 0;

        var travelFee = 0;
        if (mode === 'mobile' && artist) travelFee = Number(artist.mf) || 0;

        var total = basePrice + travelFee;

        if ($summaryBasePrice) {
            $summaryBasePrice.textContent = fmtIDR(basePrice);
            $summaryBasePrice.setAttribute('data-region-price', basePrice || 0);
        }
        if ($summaryTravelFee) {
            $summaryTravelFee.textContent = fmtIDR(travelFee);
            $summaryTravelFee.setAttribute('data-region-price', travelFee || 0);
        }
        if ($travelBlock) $travelBlock.style.display = travelFee > 0 ? '' : 'none';
        if ($summaryTotal) {
            $summaryTotal.textContent = fmtIDR(total);
            $summaryTotal.setAttribute('data-region-price', total || 0);
        }
    }

    function updateStepProgress() {
        var completed = {};
        completed[1] = Boolean($service && $service.value);
        completed[2] = Boolean($artist && $artist.value);
        completed[3] = Boolean(selectedMode());
        completed[4] = Boolean($date && $date.value && $time && $time.value);
        completed[5] = true;

        var activeStep = 5;
        for (var i = 1; i <= 5; i++) {
            if (!completed[i]) { activeStep = i; break; }
        }

        $stepIndicators.forEach(function (el) {
            var n = Number(el.getAttribute('data-step-indicator'));
            el.classList.toggle('is-done', n < activeStep && completed[n]);
            el.classList.toggle('is-active', n === activeStep);
        });

        $stepCards.forEach(function (card) {
            var n = Number(card.getAttribute('data-step'));
            card.classList.toggle('is-active', n === activeStep);
            card.classList.toggle('is-completed', n < activeStep && completed[n]);
        });

        $bfpLines.forEach(function (line, idx) {
            var stepBefore = idx + 1;
            line.classList.toggle('is-done', completed[stepBefore] && stepBefore < activeStep);
        });
    }

    function markErrorSteps() {
        $stepCards.forEach(function (card) {
            var hasError = card.querySelector('.field-error');
            card.classList.toggle('has-error', Boolean(hasError));
            if (hasError) {
                var field = card.querySelector('.form-control, .form-select');
                if (field) field.classList.add('is-invalid');
            }
        });
    }

    function showBtnLoading() {
        if (!$submitBtn || isSubmitting) return;
        isSubmitting = true;
        $submitBtn.disabled = true;
        $submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Memproses...';
    }

    function attachClientValidation() {
        formEl.addEventListener('submit', function (e) {
            var mode = selectedMode();
            var addr = formEl.querySelector('[name="location_address"]');
            if (mode === 'mobile' && addr && !addr.value.trim()) {
                e.preventDefault();
                addr.focus();
                addr.classList.add('is-invalid');
                addr.style.borderColor = '#dc3545';
                if ($locationField) $locationField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return;
            }
            showBtnLoading();
        });
    }

    function onFieldChange() {
        try {
            filterPackagesByService();
            updateArtistInfo();
            toggleLocationField();
            updateSummary();
            updateStepProgress();
        } catch (e) {}
    }

    if ($service) $service.addEventListener('change', onFieldChange);
    if ($package) $package.addEventListener('change', onFieldChange);
    if ($artist) $artist.addEventListener('change', onFieldChange);
    if ($date) $date.addEventListener('change', onFieldChange);
    if ($time) $time.addEventListener('change', onFieldChange);
    $modeRadios.forEach(function (r) { r.addEventListener('change', onFieldChange); });

    attachClientValidation();

    function boot() {
        try {
            filterPackagesByService();
            updateArtistInfo();
            toggleLocationField();
            updateSummary();
            updateStepProgress();
            markErrorSteps();
        } catch (e) {}
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();

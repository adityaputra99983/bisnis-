from datetime import date

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Booking, Service, Artist, ServicePackage


class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('customer', 'Customer (Booking Tattoo)'),
        ('artist', 'Tattoo Artist (Profesional)'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES, initial='customer',
        widget=forms.RadioSelect(attrs={'class': 'role-radio'}),
        label="Daftar Sebagai"
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'})
    )
    phone = forms.CharField(
        max_length=20, required=False, label="Nomor Telepon",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0812xxxxxx'})
    )

    # ===== Artist-only fields =====
    artist_full_name = forms.CharField(
        max_length=200, required=False, label="Nama Lengkap Artist",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama lengkap kamu'})
    )
    artist_nickname = forms.CharField(
        max_length=100, required=False, label="Nama Panggilan / Julukan",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'mis: Inky, Bro Sam, dsb'})
    )
    artist_experience_years = forms.IntegerField(
        required=False, min_value=0, initial=1, label="Pengalaman (Tahun)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1', 'min': '0'})
    )
    artist_bio = forms.CharField(
        required=False, label="Bio Singkat",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                     'placeholder': 'Ceritakan gaya dan keahlian kamu...'})
    )
    artist_specialties = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'specialty-checkbox'}),
        label="Spesialisasi Layanan"
    )
    artist_photo = forms.ImageField(
        required=False, label="Foto Profil Artist",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    artist_instagram = forms.CharField(
        max_length=200, required=False, label="Instagram (opsional)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username_kamu'})
    )
    artist_service_area = forms.CharField(
        max_length=300, required=False, initial="Seluruh area Bali",
        label="Wilayah Layanan",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'mis: Ubud, Denpasar, Seluruh Bali'})
    )
    artist_mobile_fee = forms.DecimalField(
        required=False, min_value=0, initial=50000, max_digits=10, decimal_places=0,
        label="Biaya Panggilan ke Rumah (Rp)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '50000', 'min': '0'})
    )
    artist_available_studio = forms.BooleanField(
        required=False, initial=True, label="Melayani di Studio",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    artist_available_mobile = forms.BooleanField(
        required=False, initial=True, label="Bisa Panggilan ke Rumah",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Konfirmasi password'})

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role')
        if role == 'artist':
            required_pairs = [
                ('artist_full_name', 'Nama lengkap artist wajib diisi.'),
                ('artist_nickname', 'Nama panggilan wajib diisi.'),
                ('artist_bio', 'Bio singkat wajib diisi.'),
            ]
            for field_name, msg in required_pairs:
                if not cleaned.get(field_name):
                    self.add_error(field_name, msg)
            if not (cleaned.get('artist_available_studio') or cleaned.get('artist_available_mobile')):
                self.add_error('artist_available_studio',
                               'Pilih minimal satu mode layanan (Studio atau Panggil ke Rumah).')
        return cleaned

    def save_with_role(self):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.save()

        role = self.cleaned_data.get('role')
        artist_obj = None
        if role == 'artist':
            artist_obj = Artist.objects.create(
                user=user,
                name=self.cleaned_data['artist_full_name'],
                nickname=self.cleaned_data['artist_nickname'],
                bio=self.cleaned_data['artist_bio'],
                experience_years=self.cleaned_data.get('artist_experience_years') or 1,
                photo=self.cleaned_data.get('artist_photo'),
                instagram=self.cleaned_data.get('artist_instagram') or '',
                service_area=self.cleaned_data.get('artist_service_area') or 'Seluruh area Bali',
                mobile_fee=self.cleaned_data.get('artist_mobile_fee') or 50000,
                is_available_studio=bool(self.cleaned_data.get('artist_available_studio')),
                is_available_mobile=bool(self.cleaned_data.get('artist_available_mobile')),
                is_active=True,
            )
            specialties = self.cleaned_data.get('artist_specialties')
            if specialties:
                artist_obj.specialties.set(specialties)
        return user, artist_obj


class PackageSelectWidget(forms.Select):
    """Select widget yang menambahkan data-service & data-price ke setiap option,
    sehingga frontend bisa memfilter paket berdasarkan layanan yang dipilih
    dan menampilkan estimasi harga secara real-time."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index,
                                       subindex=subindex, attrs=attrs)
        if value:
            try:
                pkg = ServicePackage.objects.select_related('service').get(pk=value)
                option['attrs']['data-service'] = pkg.service_id
                option['attrs']['data-price'] = int(pkg.price)
                option['attrs']['data-duration'] = pkg.duration
            except (ServicePackage.DoesNotExist, ValueError, TypeError):
                pass
        return option


class ServiceSelectWidget(forms.Select):
    """Select widget yang menambahkan data-price ke setiap option layanan."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index,
                                       subindex=subindex, attrs=attrs)
        if value:
            try:
                svc = Service.objects.get(pk=value)
                option['attrs']['data-price'] = int(svc.price)
                option['attrs']['data-duration'] = svc.duration
            except (Service.DoesNotExist, ValueError, TypeError):
                pass
        return option


class ArtistSelectWidget(forms.Select):
    """Select widget yang menambahkan info ketersediaan mode & biaya panggilan."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index,
                                       subindex=subindex, attrs=attrs)
        if value:
            try:
                artist = Artist.objects.get(pk=value)
                option['attrs']['data-studio'] = '1' if artist.is_available_studio else '0'
                option['attrs']['data-mobile'] = '1' if artist.is_available_mobile else '0'
                option['attrs']['data-mobile-fee'] = int(artist.mobile_fee)
            except (Artist.DoesNotExist, ValueError, TypeError):
                pass
        return option


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['service', 'package', 'artist', 'mode', 'booking_date',
                  'booking_time', 'location_address', 'notes', 'design_reference']
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control',
                                                    'data-booking-field': 'date'}),
            'booking_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control',
                                                    'data-booking-field': 'time'}),
            'location_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control',
                                                       'placeholder': 'Masukkan alamat lengkap kamu (jalan, no. rumah, kelurahan, kecamatan, kota)...'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control',
                                            'placeholder': 'Ada referensi desain atau permintaan khusus? Ceritakan di sini...'}),
            'design_reference': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['service'].queryset = Service.objects.filter(is_active=True).order_by('name')
        self.fields['package'].queryset = ServicePackage.objects.filter(is_active=True).select_related('service')
        self.fields['artist'].queryset = Artist.objects.filter(is_active=True).order_by('nickname')

        self.fields['service'].empty_label = "-- Pilih Layanan --"
        self.fields['package'].empty_label = "-- Tanpa Paket --"
        self.fields['artist'].empty_label = "-- Pilih Artist --"
        self.fields['package'].required = False

        self.fields['service'].widget = ServiceSelectWidget(
            attrs={'class': 'form-select', 'data-booking-field': 'service'}
        )
        self.fields['package'].widget = PackageSelectWidget(
            attrs={'class': 'form-select', 'data-booking-field': 'package'}
        )
        self.fields['artist'].widget = ArtistSelectWidget(
            attrs={'class': 'form-select', 'data-booking-field': 'artist'}
        )
        self.fields['mode'].widget = forms.RadioSelect(
            attrs={'class': 'booking-mode-radio', 'data-booking-field': 'mode'}
        )

        self.fields['service'].widget.choices = self.fields['service'].choices
        self.fields['package'].widget.choices = self.fields['package'].choices
        self.fields['artist'].widget.choices = self.fields['artist'].choices
        self.fields['mode'].widget.choices = self.fields['mode'].choices

        self.fields['booking_date'].widget.attrs['min'] = date.today().isoformat()

        self.fields['service'].label = "Layanan Tattoo"
        self.fields['package'].label = "Pilih Paket"
        self.fields['artist'].label = "Tattoo Artist"
        self.fields['mode'].label = "Cara Layanan"
        self.fields['booking_date'].label = "Tanggal"
        self.fields['booking_time'].label = "Jam"
        self.fields['location_address'].label = "Alamat Lengkap"
        self.fields['notes'].label = "Catatan / Permintaan Khusus"
        self.fields['design_reference'].label = "Referensi Desain"

    def clean_booking_date(self):
        booking_date = self.cleaned_data.get('booking_date')
        if booking_date and booking_date < date.today():
            raise forms.ValidationError("Tanggal booking tidak boleh di masa lalu.")
        return booking_date

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')
        location = cleaned_data.get('location_address')
        artist = cleaned_data.get('artist')
        service = cleaned_data.get('service')
        package = cleaned_data.get('package')

        if mode == 'mobile' and not location:
            self.add_error('location_address',
                           "Alamat wajib diisi jika memilih 'Panggil ke Rumah'.")

        if artist and mode:
            if mode == 'mobile' and not artist.is_available_mobile:
                self.add_error('artist',
                               f"Artist {artist.nickname} tidak melayani panggilan ke rumah. "
                               "Pilih artist lain atau ubah mode ke 'Datang ke Studio'.")
            elif mode == 'studio' and not artist.is_available_studio:
                self.add_error('artist',
                               f"Artist {artist.nickname} tidak melayani di studio. "
                               "Pilih artist lain atau ubah mode ke 'Panggil ke Rumah'.")

        if package and service and package.service_id != service.id:
            self.add_error('package',
                           "Paket yang dipilih tidak sesuai dengan layanan. Pilih ulang paket.")

        return cleaned_data


class ReviewForm(forms.Form):
    rating = forms.ChoiceField(
        choices=[(i, f"{'★' * i}{'☆' * (5-i)}") for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        label="Rating"
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control',
                                      'placeholder': 'Ceritakan pengalaman kamu...'}),
        required=False,
        label="Ulasan"
    )


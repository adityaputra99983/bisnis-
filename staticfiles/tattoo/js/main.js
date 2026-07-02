const GLOBAL_CONFIG = {
    currentRegion: localStorage.getItem('bt_region') || 'IDR',
    exchangeRates: {
        'IDR': 1,
        'USD': 16500,
        'EUR': 17900,
        'SGD': 12200,
        'AUD': 10700,
        'RUB': 180
    },
    currencySymbols: {
        'IDR': 'Rp ',
        'USD': '$',
        'EUR': '€',
        'SGD': 'S$',
        'AUD': 'A$',
        'RUB': '₽'
    },
    ratesSource: 'cache',
    htmlLangMap: {
        'IDR': 'id',
        'USD': 'en',
        'AUD': 'en',
        'SGD': 'en',
        'EUR': 'fr',
        'RUB': 'ru'
    },
    translations: {
        'IDR': {
            home: 'Beranda', services: 'Layanan', artists: 'Artist', info: 'Info', booking: 'Booking',
            about_us: 'Tentang Kami', how_it_works: 'Cara Kerja', contact: 'Kontak',
            popular_title: 'Layanan Populer', popular_sub: 'Paling banyak dicari dan direkomendasikan',
            all_services: 'Semua Layanan', starts_from: 'Mulai dari', intl: 'Internasional',
            est_kurs: 'Estimasi Kurs Internasional', booking_btn: 'Lanjutkan Booking',
            more_services: 'Lihat Semua Layanan', artist_title: 'Artist Kami',
            artist_sub: 'Kenalan dengan tattoo artist berbakat di Bali',
            available_studio: 'Studio', available_mobile: 'Panggil ke Rumah',
            footer_desc: 'Premium tattoo studio di Bali. Melayani panggilan ke seluruh area Bali.',
            login: 'Masuk', register: 'Daftar', my_orders: 'Pesanan Saya', new_booking: 'Booking Baru',
            logout: 'Keluar', contact_wa: 'Hubungi via WA', pricing: 'Layanan & Harga',
            navigation: 'Navigasi', our_contact: 'Kontak Kami', design_custom: 'Desain Kustom',
            studio_location: 'Lokasi Studio', home_service: 'Layanan ke Rumah',
            back_to_home: 'Kembali ke Beranda', select_artist: 'Pilih Artist',
            booking_now: 'Booking Sekarang', see_artist: 'Lihat Artist',
            hero_badge: 'BALI INK HUB — Verified Tattoo Marketplace',
            hero_subtitle: 'Find the best tattoo artists in Bali — from Seminyak to Canggu and Ubud. Browse verified studios & mobile artists, compare real-time availability & prices, and book home service or studio session instantly.',
            stats_artists: 'Verified Artists', stats_services: 'Tattoo Services', stats_satisfied: 'Happy Clients',
            step_title: 'Cara Kerja', step_sub: 'Mudah dan cepat, hasil premium terjamin',
            step_1_title: 'Pilih Artist & Layanan', step_1_desc: 'Lihat portofolio artist dan pilih desain impianmu',
            step_2_title: 'Pilih Mode', step_2_desc: 'Datang ke studio premium atau panggil ke rumahmu',
            step_3_title: 'Booking', step_3_desc: 'Tentukan jadwal yang pas buat kamu',
            step_4_title: 'Mulai Tattoo!', step_4_desc: 'Dapatkan tattoo impianmu!',
            choose_mode_title: 'Pilih Cara Kamu', choose_mode_sub: 'Dua pilihan fleksibel, satu hasil maksimal',
            mode_studio_title: 'Tattoo di Studio', mode_studio_desc: 'Datang langsung ke studio premium kami yang nyaman dan higienis.',
            feat_ac: 'Studio premium ber-AC', feat_sterile: 'Alat steril & higienis', feat_consult: 'Konsultasi desain tatap muka', feat_free: 'Minuman & snack gratis',
            mode_mobile_desc: 'Malas keluar? Tenang, artist kami siap datang ke villa, hotel, atau rumah pribadi Anda.',
            feat_home: 'Artist datang ke tempatmu', feat_mobile_gear: 'Peralatan mobile lengkap', feat_all_bali: 'Layanan seluruh area Bali', feat_privacy: 'Privasi & kenyamanan maksimal',
            cat_title: 'Kategori Layanan', cat_sub: 'Temukan gaya tattoo yang sesuai dengan karaktermu',
            services_label: 'Layanan', see_profile: 'Lihat Profil', no_rating: 'Belum ada rating',
            ready_title: 'Siap Bikin Tattoo?', ready_sub: 'Yuk booking sekarang! Bisa di studio atau panggil ke tempatmu.',
            popular_badge: 'Populer', see_detail: 'Detail',
            // Booking Form
            form_service: 'Layanan', form_package: 'Paket (opsional)', form_artist: 'Artist',
            form_mode: 'Mode Layanan', form_date: 'Tanggal', form_time: 'Jam',
            form_address: 'Alamat Lengkap', form_address_note: 'Wajib diisi jika memilih "Panggil ke Rumah"',
            form_ref: 'Upload Referensi Desain (opsional)', form_notes: 'Catatan / Referensi Desain',
            form_submit: 'Buat Pesanan',
            // Listings
            all_artists: 'Semua Artist Profesional', artist_find: 'Cari artist favoritmu',
            service_find: 'Cari layanan tattoo', price_range: 'Rentang Harga',
            experience: 'Pengalaman', years: 'Tahun', expertise: 'Keahlian',
            // Navbar Orders
            view_all: 'Lihat Semua', active_label: 'Aktif', unpaid_label: 'Belum Lunas',
            total_label: 'Total', total_bookings: 'Total pesanan',
            manage_orders: 'Kelola Pesanan', no_orders_yet: 'Belum ada pesanan',
            // Booking Detail
            title_booking_detail: 'Detail Pesanan', back_to_orders: 'Kembali ke Pesanan',
            order_id: 'Pesanan', created_at: 'Dibuat',
            step_waiting_title: 'Menunggu Konfirmasi', step_waiting_sub: 'Artist akan segera memeriksa pesananmu',
            step_confirmed_title: 'Dikonfirmasi', step_confirmed_sub: 'Pesananmu sudah dikonfirmasi artist',
            step_progress_title: 'Sedang Dikerjakan', step_progress_sub: 'Tattoo sedang dikerjakan oleh artist',
            step_done_title: 'Selesai', step_done_sub: 'Tattoo selesai dan bisa di-review',
            cancelled_title: 'Pesanan Dibatalkan',
            cancelled_sub: 'Pesanan ini sudah dibatalkan. Silakan buat pesanan baru jika kamu masih ingin tattoo.',
            next_step: 'Langkah selanjutnya:',
            next_step_pending: 'Tunggu konfirmasi dari artist, lalu lakukan pembayaran untuk mengamankan jadwalmu.',
            next_step_pay: 'Lakukan pembayaran sekarang untuk mengamankan jadwal kamu.',
            next_step_confirmed: 'Datang sesuai jadwal — atau tunggu artist datang jika kamu memilih panggil ke rumah.',
            next_step_in_progress: 'Tattoo sedang dikerjakan. Nikmati prosesnya!',
            booking_info: 'Informasi Pesanan',
            label_service: 'Layanan', label_package: 'Paket', label_artist: 'Artist',
            label_mode: 'Mode Layanan', label_date: 'Tanggal', label_time: 'Jam',
            wita: 'WITA', mode_studio: 'Datang ke Studio', mode_mobile: 'Panggil ke Rumah',
            label_address: 'Alamat Lokasi', label_notes: 'Catatan / Permintaan',
            label_reference: 'Referensi Desain', click_enlarge: 'Klik untuk perbesar',
            about_artist: 'Tentang Artist', years_experience: 'tahun pengalaman',
            view_full_profile: 'Lihat Profil Lengkap',
            fee_details: 'Rincian Biaya', service_fee: 'Biaya Layanan',
            travel_fee: 'Biaya Panggilan', home_service_label: '(panggil ke rumah)',
            total_pay: 'Total Bayar', payment_paid: 'Pembayaran Lunas',
            method_label: 'Metode:', date_label_inline: 'Tanggal:',
            cancelled_no_pay: 'Pesanan dibatalkan — pembayaran tidak diperlukan.',
            payment_pending: 'Pembayaran kamu sedang menunggu konfirmasi.',
            payment_failed: 'Pembayaran sebelumnya gagal. Silakan coba lagi.',
            continue_payment: 'Lanjutkan Pembayaran', pay_now: 'Bayar Sekarang',
            secure_payment: 'Transaksi aman & terenkripsi',
            need_help: 'Butuh Bantuan?',
            help_text: 'Ada pertanyaan tentang pesanan ini? Hubungi kami langsung via WhatsApp.',
            chat_wa: 'Chat WhatsApp',
            your_review: 'Ulasan Kamu', given_on: 'Diberikan pada',
            give_review: 'Beri Ulasan',
            review_prompt: 'Bagaimana pengalaman tattoo kamu? Ulasanmu sangat berarti buat artist dan customer lain.',
            rating_question: 'Berapa rating yang kamu kasih?',
            comment_label: 'Ceritakan pengalamanmu (opsional)', send_review: 'Kirim Ulasan',
            // Payment Gateway
            pay_title: 'Pilih Metode Pembayaran', pay_subtitle: 'Pilih cara bayar yang nyaman untuk kamu',
            back_to_booking: 'Kembali ke Pesanan', order_summary: 'Ringkasan Pesanan',
            pay_service: 'Layanan', pay_artist: 'Artist', pay_date: 'Tanggal',
            pay_group_domestic: 'Pembayaran Domestik (Indonesia)',
            pay_sub_bank: 'Virtual Account Bank', pay_sub_ewallet: 'E-Wallet', pay_sub_retail: 'Convenience Store',
            pm_bca_va: 'BCA Virtual Account', pm_bca_va_desc: 'Bayar lewat m-BCA / KlikBCA',
            pm_mandiri_va: 'Mandiri Virtual Account', pm_mandiri_va_desc: "Bayar lewat Livin' / Mandiri Online",
            pm_bni_va: 'BNI Virtual Account', pm_bni_va_desc: 'Bayar lewat BNI Mobile / iBank',
            pm_bri_va: 'BRI Virtual Account', pm_bri_va_desc: 'Bayar lewat BRImo / Internet Banking',
            pm_permata_va: 'Permata Virtual Account', pm_permata_va_desc: 'Bayar lewat PermataMobile / Net',
            pm_cimb_va: 'CIMB Niaga VA', pm_cimb_va_desc: 'Bayar lewat OCTO Mobile / CIMB Clicks',
            pm_gopay: 'GoPay', pm_gopay_desc: 'Bayar dari aplikasi GoJek',
            pm_shopeepay: 'ShopeePay', pm_shopeepay_desc: 'Bayar dari aplikasi Shopee',
            pm_dana: 'DANA', pm_dana_desc: 'Bayar dari aplikasi DANA',
            pm_ovo: 'OVO', pm_ovo_desc: 'Bayar dari aplikasi OVO',
            pm_linkaja: 'LinkAja', pm_linkaja_desc: 'Bayar dari aplikasi LinkAja',
            pm_indomaret: 'Indomaret', pm_indomaret_desc: 'Bayar di kasir Indomaret terdekat',
            pm_alfamart: 'Alfamart', pm_alfamart_desc: 'Bayar di kasir Alfamart terdekat',
            pay_sub_card: 'Kartu Kredit / Debit',
            pay_group_intl: 'Pembayaran Internasional',
            pay_group_intl_sub: 'Untuk customer internasional — diproses manual oleh artist',
            pm_card: 'Kartu Kredit / Debit',
            pm_card_desc: 'Visa, Mastercard, JCB, American Express — diproses manual',
            pay_instr_card_method: 'Metode Pembayaran',
            pay_instr_link: 'Link Pembayaran',
            pay_open_link: 'Buka Link Pembayaran',
            pay_instr_fee_note: 'Termasuk biaya proses kartu',
            pay_card_edc: 'EDC Machine di Studio',
            pay_card_link: 'Payment Link',
            pay_card_manual: 'Konfirmasi Manual via WhatsApp',
            back_btn: 'Batal',
            pay_trust: 'Transaksi aman & terenkripsi. Pembayaran diproses secara internal.',
            // Payment instructions (transfer page)
            pay_instr_subtitle: 'Selesaikan pembayaran dalam 24 jam',
            pay_change_method: 'Ganti metode pembayaran',
            pay_instr_bank: 'Bank Tujuan',
            pay_instr_account: 'No. Rekening',
            pay_instr_name: 'Atas Nama',
            pay_instr_amount: 'Jumlah Transfer',
            pay_instr_provider: 'Aplikasi',
            pay_instr_number: 'Nomor Tujuan',
            pay_instr_store: 'Bayar di',
            pay_instr_code: 'Kode Pembayaran',
            pay_instr_steps_title: 'Cara Pembayaran',
            pay_instr_details: 'Detail Pembayaran',
            pay_method_eyebrow: 'Metode Pembayaran',
            pay_hero_eyebrow: 'PEMBAYARAN AMAN & TERENKRIPSI',
            pay_group_domestic_sub: 'Bank, e-wallet, dan convenience store di Indonesia',
            pay_copy: 'Salin',
            pay_trust_title: 'Transaksi 100% Aman',
            pay_help_title: 'Butuh Bantuan?',
            pay_help_desc: 'Tim customer service kami siap membantu kamu 24/7.',
            pay_i_paid: 'Saya sudah bayar',
            pay_i_paid_note: 'Klik tombol di atas setelah kamu menyelesaikan pembayaran. Booking akan otomatis dikonfirmasi.',
            pay_confirm_msg: 'Konfirmasi bahwa kamu sudah melakukan pembayaran?',
            pay_processing: 'Memproses...',
            pay_copy_success: 'Disalin!',
            view_pay_methods: 'Lihat Payment Gateway',
            pay_no_methods_title: 'Metode Pembayaran Tidak Tersedia',
            pay_no_methods_desc: 'Artist ini belum mengaktifkan metode pembayaran online. Silakan hubungi artist untuk metode pembayaran lain.'
        },
        'USD': {
            home: 'Home', services: 'Services', artists: 'Artists', info: 'Info', booking: 'Booking',
            about_us: 'About Us', how_it_works: 'How it Works', contact: 'Contact',
            popular_title: 'Popular Services', popular_sub: 'Most searched and highly recommended',
            all_services: 'All Services', starts_from: 'Starts from', intl: 'International',
            est_kurs: 'International Rate Estimation', booking_btn: 'Proceed with Booking',
            more_services: 'View All Services', artist_title: 'Our Artists',
            artist_sub: 'Meet the talented tattoo artists in Bali',
            available_studio: 'Studio', available_mobile: 'Home Service',
            footer_desc: 'Premium tattoo studio in Bali. Providing home services across Bali.',
            login: 'Login', register: 'Register', my_orders: 'My Orders', new_booking: 'New Booking',
            logout: 'Logout', contact_wa: 'Contact via WA', pricing: 'Services & Pricing',
            navigation: 'Navigation', our_contact: 'Our Contact', design_custom: 'Custom Design',
            studio_location: 'Studio Location', home_service: 'Home Service',
            back_to_home: 'Back to Home', select_artist: 'Select Artist',
            booking_now: 'Booking Now', see_artist: 'See Artist',
            hero_badge: 'Premium Tattoo Studio Bali',
            hero_subtitle: 'Fulfill your eternal art on your body. Professional artists, premium studio, or we come to you. All over Bali.',
            stats_artists: 'Professional Artists', stats_services: 'Tattoo Services', stats_satisfied: 'Satisfied Customers',
            step_title: 'How it Works', step_sub: 'Easy and fast, premium results guaranteed',
            step_1_title: 'Pick Artist & Service', step_1_desc: 'View artist portfolios and pick your dream design',
            step_2_title: 'Choose Mode', step_2_desc: 'Visit our premium studio or call us to your place',
            step_3_title: 'Booking', step_3_desc: 'Pick a schedule that fits you',
            step_4_title: 'Tattoo-on!', step_4_desc: 'Get your dream tattoo!',
            choose_mode_title: 'Choose Your Way', choose_mode_sub: 'Two flexible options, one maximal result',
            mode_studio_title: 'Tattoo at Studio', mode_studio_desc: 'Come directly to our comfortable, hygienic premium studio.',
            feat_ac: 'Premium Air-Conditioned Studio', feat_sterile: 'Sterile & Hygienic Equipment', feat_consult: 'Face-to-face Consultation', feat_free: 'Free Drinks & Snacks',
            mode_mobile_desc: 'Lazy to go out? Our artists are ready to come to your villa, hotel, or private home.',
            feat_home: 'Artist comes to your place', feat_mobile_gear: 'Full mobile equipment', feat_all_bali: 'Service across entire Bali', feat_privacy: 'Maximum privacy & comfort',
            cat_title: 'Service Categories', cat_sub: 'Find the tattoo style that matches your character',
            services_label: 'Services', see_profile: 'View Profile', no_rating: 'No rating yet',
            ready_title: 'Ready for a Tattoo?', ready_sub: 'Book now! Available at studio or home service.',
            popular_badge: 'Popular', see_detail: 'Detail',
            // Booking Form
            form_service: 'Service', form_package: 'Package (optional)', form_artist: 'Artist',
            form_mode: 'Service Mode', form_date: 'Date', form_time: 'Time',
            form_address: 'Full Address', form_address_note: 'Required for Home Service',
            form_ref: 'Upload Design Reference (optional)', form_notes: 'Notes / Design Reference',
            form_submit: 'Create Booking',
            // Listings
            all_artists: 'All Professional Artists', artist_find: 'Find your favorite artist',
            service_find: 'Find tattoo services', price_range: 'Price Range',
            experience: 'Experience', years: 'Years', expertise: 'Expertise',
            // Navbar Orders
            view_all: 'View All', active_label: 'Active', unpaid_label: 'Unpaid',
            total_label: 'Total', total_bookings: 'Total bookings',
            manage_orders: 'Manage Orders', no_orders_yet: 'No orders yet',
            // Booking Detail
            title_booking_detail: 'Booking Detail', back_to_orders: 'Back to Orders',
            order_id: 'Order', created_at: 'Created',
            step_waiting_title: 'Waiting for Confirmation', step_waiting_sub: 'The artist will review your booking soon',
            step_confirmed_title: 'Confirmed', step_confirmed_sub: 'Your booking has been confirmed by the artist',
            step_progress_title: 'In Progress', step_progress_sub: 'Your tattoo is being worked on by the artist',
            step_done_title: 'Completed', step_done_sub: 'Tattoo is done and ready to be reviewed',
            cancelled_title: 'Booking Cancelled',
            cancelled_sub: 'This booking has been cancelled. Please create a new booking if you still want a tattoo.',
            next_step: 'Next step:',
            next_step_pending: 'Wait for the artist to confirm, then make the payment to secure your schedule.',
            next_step_pay: 'Make the payment now to secure your schedule.',
            next_step_confirmed: 'Come on schedule — or wait for the artist to come if you chose home service.',
            next_step_in_progress: 'Your tattoo is being worked on. Enjoy the process!',
            booking_info: 'Booking Information',
            label_service: 'Service', label_package: 'Package', label_artist: 'Artist',
            label_mode: 'Service Mode', label_date: 'Date', label_time: 'Time',
            wita: 'WITA', mode_studio: 'Come to Studio', mode_mobile: 'Home Service',
            label_address: 'Location Address', label_notes: 'Notes / Requests',
            label_reference: 'Design Reference', click_enlarge: 'Click to enlarge',
            about_artist: 'About the Artist', years_experience: 'years of experience',
            view_full_profile: 'View Full Profile',
            fee_details: 'Cost Details', service_fee: 'Service Fee',
            travel_fee: 'Travel Fee', home_service_label: '(home service)',
            total_pay: 'Total Pay', payment_paid: 'Payment Completed',
            method_label: 'Method:', date_label_inline: 'Date:',
            cancelled_no_pay: 'Booking cancelled — no payment required.',
            payment_pending: 'Your payment is awaiting confirmation.',
            payment_failed: 'Previous payment failed. Please try again.',
            continue_payment: 'Continue Payment', pay_now: 'Pay Now',
            secure_payment: 'Secure & encrypted transaction',
            need_help: 'Need Help?',
            help_text: 'Any questions about this booking? Contact us directly via WhatsApp.',
            chat_wa: 'Chat WhatsApp',
            your_review: 'Your Review', given_on: 'Given on',
            give_review: 'Give a Review',
            review_prompt: 'How was your tattoo experience? Your review means a lot to the artist and other customers.',
            rating_question: 'What rating would you give?',
            comment_label: 'Tell us about your experience (optional)', send_review: 'Send Review',
            // Payment Gateway
            pay_title: 'Select Payment Method', pay_subtitle: 'Pick the payment way that works best for you',
            back_to_booking: 'Back to Booking', order_summary: 'Order Summary',
            pay_service: 'Service', pay_artist: 'Artist', pay_date: 'Date',
            pay_group_domestic: 'Domestic Payment (Indonesia)',
            pay_sub_bank: 'Bank Virtual Account', pay_sub_ewallet: 'E-Wallet', pay_sub_retail: 'Convenience Store',
            pm_bca_va: 'BCA Virtual Account', pm_bca_va_desc: 'Pay via m-BCA / KlikBCA',
            pm_mandiri_va: 'Mandiri Virtual Account', pm_mandiri_va_desc: "Pay via Livin' / Mandiri Online",
            pm_bni_va: 'BNI Virtual Account', pm_bni_va_desc: 'Pay via BNI Mobile / iBank',
            pm_bri_va: 'BRI Virtual Account', pm_bri_va_desc: 'Pay via BRImo / Internet Banking',
            pm_permata_va: 'Permata Virtual Account', pm_permata_va_desc: 'Pay via PermataMobile / Net',
            pm_cimb_va: 'CIMB Niaga VA', pm_cimb_va_desc: 'Pay via OCTO Mobile / CIMB Clicks',
            pm_gopay: 'GoPay', pm_gopay_desc: 'Pay from GoJek app',
            pm_shopeepay: 'ShopeePay', pm_shopeepay_desc: 'Pay from Shopee app',
            pm_dana: 'DANA', pm_dana_desc: 'Pay from DANA app',
            pm_ovo: 'OVO', pm_ovo_desc: 'Pay from OVO app',
            pm_linkaja: 'LinkAja', pm_linkaja_desc: 'Pay from LinkAja app',
            pm_indomaret: 'Indomaret', pm_indomaret_desc: 'Pay at nearest Indomaret cashier',
            pm_alfamart: 'Alfamart', pm_alfamart_desc: 'Pay at nearest Alfamart cashier',
            pay_sub_card: 'Credit / Debit Card',
            pay_group_intl: 'International Payment',
            pay_group_intl_sub: 'For international customers — manually processed by the artist',
            pm_card: 'Credit / Debit Card',
            pm_card_desc: 'Visa, Mastercard, JCB, American Express — manually processed',
            pay_instr_card_method: 'Payment Method',
            pay_instr_link: 'Payment Link',
            pay_open_link: 'Open Payment Link',
            pay_instr_fee_note: 'Includes card processing fee',
            pay_card_edc: 'EDC Machine at Studio',
            pay_card_link: 'Payment Link',
            pay_card_manual: 'Manual Confirmation via WhatsApp',
            back_btn: 'Cancel',
            pay_trust: 'Transactions are secure & encrypted. Payments are processed internally.',
            // Payment instructions (transfer page)
            pay_instr_subtitle: 'Complete your payment within 24 hours',
            pay_change_method: 'Change payment method',
            pay_instr_bank: 'Destination Bank',
            pay_instr_account: 'Account Number',
            pay_instr_name: 'Account Name',
            pay_instr_amount: 'Transfer Amount',
            pay_instr_provider: 'Application',
            pay_instr_number: 'Destination Number',
            pay_instr_store: 'Pay at',
            pay_instr_code: 'Payment Code',
            pay_instr_steps_title: 'How to Pay',
            pay_instr_details: 'Payment Details',
            pay_method_eyebrow: 'Payment Method',
            pay_hero_eyebrow: 'SECURE & ENCRYPTED PAYMENT',
            pay_group_domestic_sub: 'Banks, e-wallets, and convenience stores in Indonesia',
            pay_copy: 'Copy',
            pay_trust_title: '100% Secure Transaction',
            pay_help_title: 'Need Help?',
            pay_help_desc: 'Our customer service team is ready to help you 24/7.',
            pay_i_paid: 'I have paid',
            pay_i_paid_note: 'Click the button above after you complete the payment. Your booking will be confirmed automatically.',
            pay_confirm_msg: 'Confirm that you have completed the payment?',
            pay_processing: 'Processing...',
            pay_copy_success: 'Copied!',
            view_pay_methods: 'View Payment Gateway',
            pay_no_methods_title: 'No Payment Methods Available',
            pay_no_methods_desc: 'This artist has not enabled online payment yet. Please contact the artist for other payment methods.'
        },
        'EUR': {
            home: 'Accueil', services: 'Services', artists: 'Artistes', info: 'Infos', booking: 'Réservation',
            about_us: 'À Propos', how_it_works: 'Réservation', contact: 'Contact',
            popular_title: 'Services Populaires', popular_sub: 'Les plus recherchés et recommandés',
            all_services: 'Tous les Services', starts_from: 'À partir de', intl: 'International',
            est_kurs: 'Estimation du taux international', booking_btn: 'Continuer la réservation',
            more_services: 'Voir tous les services', artist_title: 'Nos Artistes',
            artist_sub: 'Rencontrez les tatoueurs de Bali',
            available_studio: 'Studio', available_mobile: 'Service à domicile',
            footer_desc: 'Studio de tatouage premium à Bali. Services à domicile dans tout Bali.',
            login: 'Connexion', register: 'S\'inscrire', my_orders: 'Mes Commandes', new_booking: 'Nouvelle Réservation',
            logout: 'Déconnexion', contact_wa: 'Contact via WA', pricing: 'Services & Tarifs',
            navigation: 'Navigation', our_contact: 'Contactez-nous', design_custom: 'Design Personnalisé',
            studio_location: 'Emplacement du Studio', home_service: 'Service à Domicile',
            back_to_home: 'Retour à l\'Accueil', select_artist: 'Choisir Artiste',
            booking_now: 'Réserver', see_artist: 'Voir Artiste',
            hero_badge: 'Studio de Tatouage Premium Bali',
            hero_subtitle: 'Réalisez l\'art éternel sur votre corps. Artistes professionnels, studio premium ou nous venons à vous.',
            stats_artists: 'Artistes Professionnels', stats_services: 'Services de Tatouage', stats_satisfied: 'Clients Satisfaits',
            step_title: 'Comment ça Marche', step_sub: 'Facile et rapide, résultats premium garantis',
            step_1_title: 'Choisir Artiste', step_1_desc: 'Consultez les portfolios et choisissez votre design',
            step_2_title: 'Choisir le Mode', step_2_desc: 'Visitez notre studio ou appelez-nous chez vous',
            step_3_title: 'Réservation', step_3_desc: 'Choisissez un créneau qui vous convient',
            step_4_title: 'Tatouage!', step_4_desc: 'Obtenez votre tatouage de rêve!',
            choose_mode_title: 'Choisissez Votre Voie', choose_mode_sub: 'Deux options flexibles, un résultat maximal',
            mode_studio_title: 'Tatouage au Studio', mode_studio_desc: 'Venez directement dans notre studio premium confortable et hygiénique.',
            feat_ac: 'Studio Premium Climatisé', feat_sterile: 'Équipement Stérile & Hygiénique', feat_consult: 'Consultation en Face à Face', feat_free: 'Boissons & Snacks Gratuits',
            mode_mobile_desc: 'Pas envie de sortir? Nos artistes viennent à votre villa, hôtel ou domicile.',
            feat_home: 'L\'artiste vient chez vous', feat_mobile_gear: 'Équipement mobile complet', feat_all_bali: 'Service dans tout Bali', feat_privacy: 'Intimité et confort maximum',
            cat_title: 'Catégories de Services', cat_sub: 'Trouvez le style de tatouage qui vous correspond',
            services_label: 'Services', see_profile: 'Voir le Profil', no_rating: 'Pas encore de note',
            ready_title: 'Prêt pour un Tatouage?', ready_sub: 'Réservez maintenant! En studio atau à domicile.',
            popular_badge: 'Populaire', see_detail: 'Détail',
            // Booking Form
            form_service: 'Service', form_package: 'Forfait (optionnel)', form_artist: 'Artiste',
            form_mode: 'Mode de Service', form_date: 'Date', form_time: 'Heure',
            form_address: 'Adresse Complète', form_address_note: 'Requis pour le service à domicile',
            form_ref: 'Télécharger la référence (optionnel)', form_notes: 'Notes / Référence de Design',
            form_submit: 'Créer la réservation',
            // Listings
            all_artists: 'Tous les Artistes Professionnels', artist_find: 'Trouvez votre artiste préféré',
            service_find: 'Trouver des services de tatouage', price_range: 'Fourchette de prix',
            experience: 'Expérience', years: 'Ans', expertise: 'Expertise',
            // Navbar Orders
            view_all: 'Tout voir', active_label: 'Actif', unpaid_label: 'Non payé',
            total_label: 'Total', total_bookings: 'Total réservations',
            manage_orders: 'Gérer Commandes', no_orders_yet: 'Aucune commande',
            // Booking Detail
            title_booking_detail: 'Détail de la Réservation', back_to_orders: 'Retour aux Commandes',
            order_id: 'Commande', created_at: 'Créé',
            step_waiting_title: 'En Attente de Confirmation', step_waiting_sub: 'L\'artiste examinera bientôt votre commande',
            step_confirmed_title: 'Confirmée', step_confirmed_sub: 'Votre commande a été confirmée par l\'artiste',
            step_progress_title: 'En Cours', step_progress_sub: 'Votre tatouage est en cours de réalisation',
            step_done_title: 'Terminé', step_done_sub: 'Tatouage terminé et prêt à être évalué',
            cancelled_title: 'Commande Annulée',
            cancelled_sub: 'Cette commande a été annulée. Veuillez créer une nouvelle commande si vous souhaitez toujours un tatouage.',
            next_step: 'Prochaine étape:',
            next_step_pending: 'Attendez la confirmation de l\'artiste, puis effectuez le paiement pour sécuriser votre créneau.',
            next_step_pay: 'Effectuez le paiement maintenant pour sécuriser votre créneau.',
            next_step_confirmed: 'Venez à l\'heure prévue — ou attendez l\'artiste si vous avez choisi le service à domicile.',
            next_step_in_progress: 'Votre tatouage est en cours. Profitez du processus!',
            booking_info: 'Informations sur la Commande',
            label_service: 'Service', label_package: 'Forfait', label_artist: 'Artiste',
            label_mode: 'Mode de Service', label_date: 'Date', label_time: 'Heure',
            wita: 'WITA', mode_studio: 'Venir au Studio', mode_mobile: 'Service à Domicile',
            label_address: 'Adresse', label_notes: 'Notes / Demandes',
            label_reference: 'Référence de Design', click_enlarge: 'Cliquez pour agrandir',
            about_artist: 'À Propos de l\'Artiste', years_experience: 'ans d\'expérience',
            view_full_profile: 'Voir le Profil Complet',
            fee_details: 'Détails des Coûts', service_fee: 'Frais de Service',
            travel_fee: 'Frais de Déplacement', home_service_label: '(service à domicile)',
            total_pay: 'Total à Payer', payment_paid: 'Paiement Effectué',
            method_label: 'Méthode:', date_label_inline: 'Date:',
            cancelled_no_pay: 'Commande annulée — aucun paiement requis.',
            payment_pending: 'Votre paiement est en attente de confirmation.',
            payment_failed: 'Le paiement précédent a échoué. Veuillez réessayer.',
            continue_payment: 'Continuer le Paiement', pay_now: 'Payer Maintenant',
            secure_payment: 'Transaction sécurisée et cryptée',
            need_help: 'Besoin d\'Aide?',
            help_text: 'Des questions sur cette commande? Contactez-nous directement via WhatsApp.',
            chat_wa: 'Chat WhatsApp',
            your_review: 'Votre Avis', given_on: 'Donné le',
            give_review: 'Donner un Avis',
            review_prompt: 'Comment était votre expérience de tatouage? Votre avis compte beaucoup pour l\'artiste et les autres clients.',
            rating_question: 'Quelle note donneriez-vous?',
            comment_label: 'Parlez-nous de votre expérience (optionnel)', send_review: 'Envoyer l\'Avis',
            // Payment Gateway
            pay_title: 'Choisir le Mode de Paiement', pay_subtitle: 'Choisissez le mode de paiement qui vous convient',
            back_to_booking: 'Retour à la Commande', order_summary: 'Résumé de la Commande',
            pay_service: 'Service', pay_artist: 'Artiste', pay_date: 'Date',
            pay_group_domestic: 'Paiement Domestique (Indonésie)',
            pay_sub_bank: 'Compte Virtuel Bancaire', pay_sub_ewallet: 'Portefeuille Électronique', pay_sub_retail: 'Magasin de Proximité',
            pm_bca_va: 'Compte Virtuel BCA', pm_bca_va_desc: 'Payer via m-BCA / KlikBCA',
            pm_mandiri_va: 'Compte Virtuel Mandiri', pm_mandiri_va_desc: "Payer via Livin' / Mandiri Online",
            pm_bni_va: 'Compte Virtuel BNI', pm_bni_va_desc: 'Payer via BNI Mobile / iBank',
            pm_bri_va: 'Compte Virtuel BRI', pm_bri_va_desc: 'Payer via BRImo / Internet Banking',
            pm_permata_va: 'Compte Virtuel Permata', pm_permata_va_desc: 'Payer via PermataMobile / Net',
            pm_cimb_va: 'CIMB Niaga VA', pm_cimb_va_desc: 'Payer via OCTO Mobile / CIMB Clicks',
            pm_gopay: 'GoPay', pm_gopay_desc: 'Payer depuis l\'app GoJek',
            pm_shopeepay: 'ShopeePay', pm_shopeepay_desc: 'Payer depuis l\'app Shopee',
            pm_dana: 'DANA', pm_dana_desc: 'Payer depuis l\'app DANA',
            pm_ovo: 'OVO', pm_ovo_desc: 'Payer depuis l\'app OVO',
            pm_linkaja: 'LinkAja', pm_linkaja_desc: 'Payer depuis l\'app LinkAja',
            pm_indomaret: 'Indomaret', pm_indomaret_desc: 'Payer à la caisse Indomaret la plus proche',
            pm_alfamart: 'Alfamart', pm_alfamart_desc: 'Payer à la caisse Alfamart la plus proche',
            pay_sub_card: 'Carte de Crédit / Débit',
            pay_group_intl: 'Paiement International',
            pay_group_intl_sub: 'Pour les clients internationaux — traité manuellement par l\'artiste',
            pm_card: 'Carte de Crédit / Débit',
            pm_card_desc: 'Visa, Mastercard, JCB, American Express — traité manuellement',
            pay_instr_card_method: 'Mode de Paiement',
            pay_instr_link: 'Lien de Paiement',
            pay_open_link: 'Ouvrir le Lien',
            pay_instr_fee_note: 'Inclut les frais de traitement de la carte',
            pay_card_edc: 'Machine EDC au Studio',
            pay_card_link: 'Lien de Paiement',
            pay_card_manual: 'Confirmation Manuelle via WhatsApp',
            back_btn: 'Annuler',
            pay_trust: 'Transactions sécurisées et cryptées. Les paiements sont traités en interne.',
            // Instructions de paiement (page de transfert)
            pay_instr_subtitle: 'Effectuez le paiement sous 24 heures',
            pay_change_method: 'Changer de mode de paiement',
            pay_instr_bank: 'Banque Destinataire',
            pay_instr_account: 'Numéro de Compte',
            pay_instr_name: 'Nom du Titulaire',
            pay_instr_amount: 'Montant du Transfert',
            pay_instr_provider: 'Application',
            pay_instr_number: 'Numéro Destinataire',
            pay_instr_store: 'Payer chez',
            pay_instr_code: 'Code de Paiement',
            pay_instr_steps_title: 'Comment Payer',
            pay_instr_details: 'Détails du Paiement',
            pay_method_eyebrow: 'Mode de Paiement',
            pay_hero_eyebrow: 'PAIEMENT SÉCURISÉ & CRYPTÉ',
            pay_group_domestic_sub: 'Banques, e-wallets et magasins de proximité en Indonésie',
            pay_copy: 'Copier',
            pay_trust_title: 'Transaction 100% Sécurisée',
            pay_help_title: 'Besoin d\'Aide?',
            pay_help_desc: 'Notre équipe est disponible 24h/24 et 7j/7.',
            pay_i_paid: 'J\'ai payé',
            pay_i_paid_note: 'Cliquez sur le bouton ci-dessus après avoir terminé le paiement. Votre réservation sera confirmée automatiquement.',
            pay_confirm_msg: 'Confirmez-vous avoir effectué le paiement?',
            pay_processing: 'Traitement...',
            pay_copy_success: 'Copié!',
            view_pay_methods: 'Voir la Passerelle de Paiement',
            pay_no_methods_title: 'Aucun Mode de Paiement Disponible',
            pay_no_methods_desc: 'Cet artiste n\'a pas encore activé le paiement en ligne. Veuillez contacter l\'artiste pour d\'autres modes de paiement.'
        },
        'RUB': {
            home: 'Главная', services: 'Услуги', artists: 'Мастера', info: 'Инфо', booking: 'Бронь',
            about_us: 'О нас', how_it_works: 'Бронирование', contact: 'Контакт',
            popular_title: 'Популярные Услуги', popular_sub: 'Самые востребованные и рекомендуемые',
            all_services: 'Все Услуги', starts_from: 'От', intl: 'Международный',
            est_kurs: 'Международная оценка курса', booking_btn: 'Продолжить бронирование',
            more_services: 'Все услуги', artist_title: 'Наши Мастера',
            artist_sub: 'Познакомьтесь с мастерами на Бали',
            available_studio: 'Студия', available_mobile: 'Выезд на дом',
            footer_desc: 'Тату-студия премиум-класса на Бали. Выезд по всему острову.',
            login: 'Вход', register: 'Регистрация', my_orders: 'Мои заказы', new_booking: 'Новая бронь',
            logout: 'Выйти', contact_wa: 'Связаться через WA', pricing: 'Услуги и цены',
            navigation: 'Навигация', our_contact: 'Контакты', design_custom: 'Свой дизайн',
            studio_location: 'Адрес студии', home_service: 'Выезд на дом',
            back_to_home: 'На главную', select_artist: 'Выбрать мастера',
            booking_now: 'Бронировать', see_artist: 'Мастера',
            hero_badge: 'Премиум Тату Студия Бали',
            hero_subtitle: 'Воплотите вечное искусство на своем теле. Профессиональные мастера, премиум студия или выезд к вам.',
            stats_artists: 'Профи Мастера', stats_services: 'Тату Услуги', stats_satisfied: 'Довольные клиенты',
            step_title: 'Как это работает', step_sub: 'Легко и быстро, премиальный результат',
            step_1_title: 'Выбор мастера', step_1_desc: 'Посмотрите портфолио и выберите свой дизайн',
            step_2_title: 'Выбор режима', step_2_desc: 'В студии или выезд к вам на дом',
            step_3_title: 'Бронирование', step_3_desc: 'Выберите удобное время',
            step_4_title: 'Начинаем!', step_4_desc: 'Получите татуировку вашей мечты!',
            choose_mode_title: 'Выберите свой путь', choose_mode_sub: 'Два варианта, один идеальный результат',
            mode_studio_title: 'Тату в студии', mode_studio_desc: 'Приходите в нашу уютную и стерильную премиум-студию.',
            feat_ac: 'Премиум студия с AC', feat_sterile: 'Стерильное оборудование', feat_consult: 'Личная консультация', feat_free: 'Напитки и закуски бесплатно',
            mode_mobile_desc: 'Не хотите выходить? Наши мастера приедут к вам на виллу или в отель.',
            feat_home: 'Мастер приедет к вам', feat_mobile_gear: 'Полный набор оборудования', feat_all_bali: 'Работаем по всему Бали', feat_privacy: 'Приватность и комфорт',
            cat_title: 'Категории услуг', cat_sub: 'Найдите стиль тату под ваш характер',
            services_label: 'Услуги', see_profile: 'Профиль', no_rating: 'Нет рейтинга',
            ready_title: 'Готовы к тату?', ready_sub: 'Забронируйте сейчас! В студии или на дому.',
            popular_badge: 'Популярно', see_detail: 'Детали',
            // Booking Form
            form_service: 'Услуга', form_package: 'Пакет (опционально)', form_artist: 'Мастер',
            form_mode: 'Режим услуги', form_date: 'Дата', form_time: 'Время',
            form_address: 'Полный адрес', form_address_note: 'Обязательно для выезда на дом',
            form_ref: 'Загрузить референс (опционально)', form_notes: 'Заметки / Референс дизайна',
            form_submit: 'Забронировать',
            // Listings
            all_artists: 'Все профессиональные мастера', artist_find: 'Найдите своего мастера',
            service_find: 'Найти тату услуги', price_range: 'Ценовой диапазон',
            experience: 'Опыт', years: 'Лет', expertise: 'Экспертиза',
            // Navbar Orders
            view_all: 'Все заказы', active_label: 'Активные', unpaid_label: 'Не оплачено',
            total_label: 'Всего', total_bookings: 'Всего заказов',
            manage_orders: 'Управление', no_orders_yet: 'Нет заказов',
            // Booking Detail
            title_booking_detail: 'Детали Заказа', back_to_orders: 'Назад к Заказам',
            order_id: 'Заказ', created_at: 'Создан',
            step_waiting_title: 'Ожидание Подтверждения', step_waiting_sub: 'Мастер скоро проверит ваш заказ',
            step_confirmed_title: 'Подтверждено', step_confirmed_sub: 'Ваш заказ подтверждён мастером',
            step_progress_title: 'В Работе', step_progress_sub: 'Мастер работает над вашей татуировкой',
            step_done_title: 'Готово', step_done_sub: 'Татуировка готова, можно оставить отзыв',
            cancelled_title: 'Заказ Отменён',
            cancelled_sub: 'Этот заказ был отменён. Пожалуйста, создайте новый заказ, если вы всё ещё хотите тату.',
            next_step: 'Следующий шаг:',
            next_step_pending: 'Дождитесь подтверждения мастера, затем оплатите, чтобы закрепить время.',
            next_step_pay: 'Оплатите сейчас, чтобы закрепить ваше время.',
            next_step_confirmed: 'Приходите в назначенное время — или ждите мастера, если выбран выезд.',
            next_step_in_progress: 'Татуировка в процессе. Наслаждайтесь процессом!',
            booking_info: 'Информация о Заказе',
            label_service: 'Услуга', label_package: 'Пакет', label_artist: 'Мастер',
            label_mode: 'Режим Услуги', label_date: 'Дата', label_time: 'Время',
            wita: 'WITA', mode_studio: 'В Студии', mode_mobile: 'Выезд на Дом',
            label_address: 'Адрес', label_notes: 'Заметки / Пожелания',
            label_reference: 'Референс Дизайна', click_enlarge: 'Нажмите для увеличения',
            about_artist: 'О Мастере', years_experience: 'лет опыта',
            view_full_profile: 'Полный Профиль',
            fee_details: 'Детали Стоимости', service_fee: 'Стоимость Услуги',
            travel_fee: 'Стоимость Выезда', home_service_label: '(выезд на дом)',
            total_pay: 'Итого к Оплате', payment_paid: 'Оплачено',
            method_label: 'Метод:', date_label_inline: 'Дата:',
            cancelled_no_pay: 'Заказ отменён — оплата не требуется.',
            payment_pending: 'Ваш платёж ожидает подтверждения.',
            payment_failed: 'Предыдущая оплата не удалась. Попробуйте снова.',
            continue_payment: 'Продолжить Оплату', pay_now: 'Оплатить Сейчас',
            secure_payment: 'Безопасная и зашифрованная транзакция',
            need_help: 'Нужна Помощь?',
            help_text: 'Есть вопросы по этому заказу? Свяжитесь с нами напрямую через WhatsApp.',
            chat_wa: 'Чат WhatsApp',
            your_review: 'Ваш Отзыв', given_on: 'Оставлен',
            give_review: 'Оставить Отзыв',
            review_prompt: 'Как прошло ваше тату? Ваш отзыв очень важен для мастера и других клиентов.',
            rating_question: 'Какую оценку вы поставите?',
            comment_label: 'Расскажите о вашем опыте (опционально)', send_review: 'Отправить Отзыв',
            // Payment Gateway
            pay_title: 'Выберите Способ Оплаты', pay_subtitle: 'Выберите удобный для вас способ оплаты',
            back_to_booking: 'Назад к Заказу', order_summary: 'Сводка Заказа',
            pay_service: 'Услуга', pay_artist: 'Мастер', pay_date: 'Дата',
            pay_group_domestic: 'Внутренняя Оплата (Индонезия)',
            pay_sub_bank: 'Виртуальный Счёт Банка', pay_sub_ewallet: 'Электронный Кошелёк', pay_sub_retail: 'Минимаркет',
            pm_bca_va: 'Виртуальный Счёт BCA', pm_bca_va_desc: 'Оплата через m-BCA / KlikBCA',
            pm_mandiri_va: 'Виртуальный Счёт Mandiri', pm_mandiri_va_desc: "Оплата через Livin' / Mandiri Online",
            pm_bni_va: 'Виртуальный Счёт BNI', pm_bni_va_desc: 'Оплата через BNI Mobile / iBank',
            pm_bri_va: 'Виртуальный Счёт BRI', pm_bri_va_desc: 'Оплата через BRImo / Интернет-Банк',
            pm_permata_va: 'Виртуальный Счёт Permata', pm_permata_va_desc: 'Оплата через PermataMobile / Net',
            pm_cimb_va: 'CIMB Niaga VA', pm_cimb_va_desc: 'Оплата через OCTO Mobile / CIMB Clicks',
            pm_gopay: 'GoPay', pm_gopay_desc: 'Оплата из приложения GoJek',
            pm_shopeepay: 'ShopeePay', pm_shopeepay_desc: 'Оплата из приложения Shopee',
            pm_dana: 'DANA', pm_dana_desc: 'Оплата из приложения DANA',
            pm_ovo: 'OVO', pm_ovo_desc: 'Оплата из приложения OVO',
            pm_linkaja: 'LinkAja', pm_linkaja_desc: 'Оплата из приложения LinkAja',
            pm_indomaret: 'Indomaret', pm_indomaret_desc: 'Оплата на кассе ближайшего Indomaret',
            pm_alfamart: 'Alfamart', pm_alfamart_desc: 'Оплата на кассе ближайшего Alfamart',
            pay_sub_card: 'Кредитная / Дебетовая Карта',
            pay_group_intl: 'Международная Оплата',
            pay_group_intl_sub: 'Для иностранных клиентов — обрабатывается мастером вручную',
            pm_card: 'Кредитная / Дебетовая Карта',
            pm_card_desc: 'Visa, Mastercard, JCB, American Express — обрабатывается вручную',
            pay_instr_card_method: 'Способ Оплаты',
            pay_instr_link: 'Ссылка на Оплату',
            pay_open_link: 'Открыть Ссылку',
            pay_instr_fee_note: 'Включает комиссию за обработку карты',
            pay_card_edc: 'EDC Терминал в Студии',
            pay_card_link: 'Ссылка на Оплату',
            pay_card_manual: 'Подтверждение вручную через WhatsApp',
            back_btn: 'Отмена',
            pay_trust: 'Транзакции защищены и зашифрованы. Платежи обрабатываются внутри системы.',
            // Инструкции по оплате (страница перевода)
            pay_instr_subtitle: 'Завершите оплату в течение 24 часов',
            pay_change_method: 'Сменить способ оплаты',
            pay_instr_bank: 'Банк Получателя',
            pay_instr_account: 'Номер Счёта',
            pay_instr_name: 'Имя Получателя',
            pay_instr_amount: 'Сумма Перевода',
            pay_instr_provider: 'Приложение',
            pay_instr_number: 'Номер Получателя',
            pay_instr_store: 'Оплатить в',
            pay_instr_code: 'Код Оплаты',
            pay_instr_steps_title: 'Как Оплатить',
            pay_instr_details: 'Детали Оплаты',
            pay_method_eyebrow: 'Способ Оплаты',
            pay_hero_eyebrow: 'БЕЗОПАСНАЯ И ЗАШИФРОВАННАЯ ОПЛАТА',
            pay_group_domestic_sub: 'Банки, электронные кошельки и минимаркеты в Индонезии',
            pay_copy: 'Копировать',
            pay_trust_title: '100% Безопасная Транзакция',
            pay_help_title: 'Нужна Помощь?',
            pay_help_desc: 'Наша команда готова помочь 24/7.',
            pay_i_paid: 'Я оплатил',
            pay_i_paid_note: 'Нажмите кнопку выше после завершения оплаты. Ваш заказ будет подтверждён автоматически.',
            pay_confirm_msg: 'Подтвердить, что вы завершили оплату?',
            pay_processing: 'Обработка...',
            pay_copy_success: 'Скопировано!',
            view_pay_methods: 'Посмотреть Платёжный Шлюз',
            pay_no_methods_title: 'Способы Оплаты Недоступны',
            pay_no_methods_desc: 'Этот мастер ещё не включил онлайн-оплату. Пожалуйста, свяжитесь с мастером для других способов оплаты.'
        }
    }
};

function setPriceChipExpanded(chip, expanded) {
    if (!chip) return;

    chip.classList.toggle('is-expanded', expanded);
    chip.setAttribute('aria-expanded', expanded ? 'true' : 'false');

    chip.closest('.luxury-service-card')?.classList.toggle('chip-elevated', expanded);
    chip.closest('.lc-pricing-panel')?.classList.toggle('chip-elevated', expanded);
    chip.closest('.service-item')?.classList.toggle('chip-elevated', expanded);
    chip.closest('.dp-international')?.classList.toggle('chip-elevated', expanded);
}

function collapseAllPriceChips(exceptChip = null) {
    document.querySelectorAll('.region-price-chip.is-expanded').forEach((chip) => {
        if (chip !== exceptChip) {
            setPriceChipExpanded(chip, false);
        }
    });
}

function setTranslatedContent(el, text) {
    if (!el || !text) return;

    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = text;
        return;
    }

    if (!el.children.length) {
        el.textContent = text;
        return;
    }

    const children = Array.from(el.children);
    const decorativeOnly = children.every((child) => ['I', 'SVG', 'IMG'].includes(child.tagName));
    if (!decorativeOnly) return;

    const textNode = Array.from(el.childNodes).find(
        (node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim()
    );

    if (textNode) {
        textNode.textContent = ` ${text}`;
    } else {
        el.append(document.createTextNode(` ${text}`));
    }
}

/* =====================================================================
   Price formatting — convert IDR value to active region currency
   ===================================================================== */
function formatPrice(idrValue, code) {
    if (idrValue === null || idrValue === undefined || isNaN(idrValue)) return '';
    const rate = GLOBAL_CONFIG.exchangeRates[code];
    if (!rate) return '';
    const symbol = GLOBAL_CONFIG.currencySymbols[code] || code + ' ';
    const converted = Number(idrValue) / rate;

    if (code === 'IDR') {
        // 1,234,567 style tanpa desimal
        return symbol + Math.round(converted).toLocaleString('id-ID');
    }
    // Semua mata uang lain: 2 desimal
    return symbol + converted.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function updateRegionPrices(region) {
    if (!region) return;
    document.querySelectorAll('[data-region-price]').forEach((el) => {
        const raw = el.getAttribute('data-region-price');
        const value = parseFloat(raw);
        if (isNaN(value)) return;
        el.textContent = formatPrice(value, region);
    });
}

function updateHtmlLang(region) {
    if (!region) return;
    const lang = GLOBAL_CONFIG.htmlLangMap[region] || 'en';
    document.documentElement.setAttribute('lang', lang);
}

function updateUIPersona(region) {
    if (!region) return;

    document.body.classList.add('persona-updating');
    localStorage.setItem('bt_region', region);

    const langMap = { 'IDR': 'IDR', 'EUR': 'EUR', 'RUB': 'RUB', 'USD': 'USD', 'AUD': 'USD', 'SGD': 'USD' };
    const lang = langMap[region] || 'USD';
    const t = GLOBAL_CONFIG.translations[lang];

    // Update harga SEGERA (tidak di dalam setTimeout) supaya tidak ada delay
    updateRegionPrices(region);
    updateHtmlLang(region);

    setTimeout(() => {
        document.querySelectorAll('[data-t]').forEach(el => {
            const key = el.getAttribute('data-t');
            if (t[key]) {
                setTranslatedContent(el, t[key]);
            }
        });

        // Special handling for Radio Labels (Mode Selector)
        document.querySelectorAll('.mode-option').forEach(opt => {
            const label = opt.querySelector('.mode-label .mode-title');
            const input = opt.querySelector('input');
            if (label && input) {
                if (input.value === 'studio') label.innerText = t['available_studio'];
                else if (input.value === 'mobile') label.innerText = t['available_mobile'];
            }
        });

        // 2. Currency Chip Switching — show ONLY the selected region's price
        const chipRegion = region; // e.g. 'IDR', 'USD', 'AUD', 'SGD', 'EUR', 'RUB'
        document.querySelectorAll('.region-price-chip').forEach(chip => {
            const chipCurrency = chip.getAttribute('data-currency');
            if (chipCurrency === chipRegion) {
                chip.classList.add('region-price-active');
                chip.classList.remove('region-price-hidden');
            } else {
                chip.classList.remove('region-price-active');
                chip.classList.add('region-price-hidden');
            }
        });

        const regionNames = {
            'IDR': '🇮🇩 Indonesia', 'USD': '🇺🇸 English', 'EUR': '🇪🇺 French',
            'AUD': '🇦🇺 English', 'SGD': '🇸🇬 Singapore', 'RUB': '🇷🇺 Russian'
        };
        const label = document.getElementById('current-region-label');
        if (label) label.innerText = regionNames[region];

        document.querySelectorAll('.region-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-region') === region);
        });

        document.body.classList.remove('persona-updating');
    }, 350);
}

/* =====================================================================
   Live exchange rates — fetch from API and update config
   ===================================================================== */
function fetchLiveRates() {
    var controller = new AbortController();
    var timeout = setTimeout(function () { controller.abort(); }, 5000);

    fetch('/api/v1/rates/', { signal: controller.signal })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data && data.rates) {
                GLOBAL_CONFIG.exchangeRates = data.rates;
                GLOBAL_CONFIG.ratesSource = 'live';
                updateRegionPrices(GLOBAL_CONFIG.currentRegion);
                updatePriceTooltips();
            }
        })
        .catch(function () {
            GLOBAL_CONFIG.ratesSource = 'fallback';
        })
        .finally(function () { clearTimeout(timeout); });
}

/* =====================================================================
   Price tooltip — hover over any IDR price to see converted value
   ===================================================================== */
var priceTooltipEl = null;

function getPriceTooltip() {
    if (!priceTooltipEl) {
        priceTooltipEl = document.createElement('div');
        priceTooltipEl.className = 'currency-tooltip';
        priceTooltipEl.setAttribute('role', 'tooltip');
        document.body.appendChild(priceTooltipEl);
    }
    return priceTooltipEl;
}

function updatePriceTooltips() {
    var region = GLOBAL_CONFIG.currentRegion;
    var tip = getPriceTooltip();
    if (!tip) return;
    var prices = document.querySelectorAll('[data-region-price]');
    var len = prices.length;
    for (var i = 0; i < len; i++) {
        var el = prices[i];
        var raw = el.getAttribute('data-region-price');
        var val = parseFloat(raw);
        if (isNaN(val)) continue;
        el.setAttribute('data-tooltip-converted', formatPrice(val, region));
    }
    var activeTip = document.querySelector('.currency-tooltip.is-visible');
    if (activeTip) {
        var target = document.querySelector('[data-tooltip-hovered]');
        if (target) {
            var text = target.getAttribute('data-tooltip-converted');
            if (text) {
                activeTip.textContent = text + ' ' + region;
            }
        }
    }
}

function showPriceTooltip(e, el) {
    var tip = getPriceTooltip();
    if (!tip) return;
    var text = el.getAttribute('data-tooltip-converted');
    if (!text) {
        var raw = el.getAttribute('data-region-price');
        var val = parseFloat(raw);
        if (!isNaN(val)) {
            text = formatPrice(val, GLOBAL_CONFIG.currentRegion);
        }
    }
    tip.textContent = (text || '') + ' ' + GLOBAL_CONFIG.currentRegion;
    tip.classList.add('is-visible');
    var rect = el.getBoundingClientRect();
    var top = rect.top + window.scrollY - tip.offsetHeight - 8;
    var left = rect.left + window.scrollX + (rect.width / 2) - (tip.offsetWidth / 2);
    if (left < 8) left = 8;
    if (left + tip.offsetWidth > window.innerWidth - 8) {
        left = window.innerWidth - tip.offsetWidth - 8;
    }
    tip.style.top = top + 'px';
    tip.style.left = left + 'px';
    el.setAttribute('data-tooltip-hovered', '1');
}

function hidePriceTooltip(el) {
    var tip = getPriceTooltip();
    if (tip) {
        tip.classList.remove('is-visible');
    }
    if (el) {
        el.removeAttribute('data-tooltip-hovered');
    }
}

function hideLoadingScreen() {
    var loader = document.getElementById('loading-screen');
    if (!loader) return;
    if (loader.classList.contains('is-hidden')) return;
    if (window._lsTimer) { clearTimeout(window._lsTimer); window._lsTimer = null; }
    loader.classList.add('is-hidden');
    setTimeout(function () {
        loader.classList.add('is-removed');
    }, 550);
}

document.addEventListener('DOMContentLoaded', () => {
    const isBookingPage = document.body.classList.contains('booking-page-minimal-nav');

    var loader = document.getElementById('loading-screen');
    if (loader && !loader.classList.contains('is-hidden')) {
        setTimeout(hideLoadingScreen, 800);
    }

    if (!isBookingPage) {
        AOS.init({ duration: 800, once: true, offset: 100 });
        updateUIPersona(GLOBAL_CONFIG.currentRegion);
        fetchLiveRates();
    }

    window.addEventListener('scroll', () => {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 50) navbar.classList.add('navbar-shrink');
        else navbar.classList.remove('navbar-shrink');
    });

    document.addEventListener('click', (e) => {
        const regionBtn = e.target.closest('.region-btn');
        const priceChip = e.target.closest('.price-chip');

        if (regionBtn) {
            e.preventDefault();
            collapseAllPriceChips();
            updateUIPersona(regionBtn.getAttribute('data-region'));
        } else if (priceChip && priceChip.classList.contains('region-price-chip')) {
            e.preventDefault();
            collapseAllPriceChips();
            updateUIPersona(priceChip.getAttribute('data-currency'));
        } else {
            collapseAllPriceChips();
        }
    });

    document.addEventListener('keydown', (e) => {
        const activeChip = document.activeElement?.closest('.region-price-chip');
        if (!activeChip) {
            if (e.key === 'Escape') collapseAllPriceChips();
            return;
        }

        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const willExpand = !activeChip.classList.contains('is-expanded');
            collapseAllPriceChips(activeChip);
            setPriceChipExpanded(activeChip, willExpand);
        } else if (e.key === 'Escape') {
            setPriceChipExpanded(activeChip, false);
            activeChip.blur();
        }
    });

    window.addEventListener('resize', () => {
        if (!window.matchMedia('(max-width: 768px)').matches) {
            collapseAllPriceChips();
        }
    });

    document.addEventListener('mouseover', (e) => {
        const chip = e.target.closest('.region-price-chip');
        if (!chip) return;
        if (window.matchMedia('(max-width: 768px)').matches) return;
        chip.closest('.luxury-service-card')?.classList.add('chip-elevated');
        chip.closest('.lc-pricing-panel')?.classList.add('chip-elevated');
        chip.closest('.service-item')?.classList.add('chip-elevated');
        chip.closest('.dp-international')?.classList.add('chip-elevated');
    });

    document.addEventListener('mouseout', (e) => {
        const chip = e.target.closest('.region-price-chip');
        if (!chip) return;
        if (chip.classList.contains('is-expanded')) return;
        ['.luxury-service-card', '.lc-pricing-panel', '.service-item', '.dp-international'].forEach((sel) => {
            const host = chip.closest(sel);
            if (host && !host.querySelector('.region-price-chip.is-expanded')) {
                host.classList.remove('chip-elevated');
            }
        });
    });

    /* ===== Price tooltip mouse events ===== */
    document.addEventListener('mouseover', function (e) {
        var priceEl = e.target.closest('[data-region-price]');
        if (!priceEl) return;
        if (priceEl.closest('.region-price-chip')) return;
        showPriceTooltip(e, priceEl);
    });

    document.addEventListener('mouseout', function (e) {
        var priceEl = e.target.closest('[data-region-price]');
        if (!priceEl) return;
        if (priceEl.closest('.region-price-chip')) return;
        var related = e.relatedTarget;
        if (related && (related === priceEl || priceEl.contains(related))) return;
        hidePriceTooltip(priceEl);
    });

    // Handle dynamic form elements (skip on booking page — handles its own UI)
    if (!isBookingPage) {
        const observer = new MutationObserver(function () {
            updateUIPersona(localStorage.getItem('bt_region'));
        });
        var form = document.querySelector('form');
        if (form) observer.observe(form, { childList: true, subtree: true });
    }
});

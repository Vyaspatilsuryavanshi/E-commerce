from decimal import Decimal
from django.core.management.base import BaseCommand
from store.models import Department, Category, Brand, Product, ProductVariant, ProductReview, StoreLocation


class Command(BaseCommand):
    help = 'Seeds complete catalog for Clothing, Skincare, Makeup, Variants, Reviews, and Store Locations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding AURA LUXE departments and products..."))

        # 1. DEPARTMENTS
        clothing_dept, _ = Department.objects.get_or_create(
            slug='clothing',
            defaults={
                'name': 'Clothing',
                'tagline': 'Timeless silhouettes crafted from mulberry silk, cashmere, and fine wool.',
                'description': 'Elevate your wardrobe with bespoke tailoring, ethereal evening gowns, and minimalist luxury staples.',
                'icon': '👗',
                'order': 1,
            }
        )

        skincare_dept, _ = Department.objects.get_or_create(
            slug='skincare',
            defaults={
                'name': 'Skincare',
                'tagline': 'Bio-fermented botanicals backed by clinical dermatological science.',
                'description': 'Experience potent barrier-repairing elixirs, active multi-molecular serums, and radiant SPF rituals.',
                'icon': '✨',
                'order': 2,
            }
        )

        makeup_dept, _ = Department.objects.get_or_create(
            slug='makeup',
            defaults={
                'name': 'Makeup',
                'tagline': 'Skin-first luxury cosmetics with featherlight luminous pigment.',
                'description': 'Velvety matte pigments, dewy cheek balms, and lip lacquers formulated with nourishing botanical oils.',
                'icon': '💄',
                'order': 3,
            }
        )

        # 2. CATEGORIES
        # Clothing Categories
        cat_dresses, _ = Category.objects.get_or_create(department=clothing_dept, slug='dresses', defaults={'name': 'Dresses & Gowns', 'order': 1})
        cat_blazers, _ = Category.objects.get_or_create(department=clothing_dept, slug='blazers', defaults={'name': 'Tailored Blazers & Coats', 'order': 2})
        cat_knitwear, _ = Category.objects.get_or_create(department=clothing_dept, slug='knitwear', defaults={'name': 'Cashmere & Knitwear', 'order': 3})
        cat_silk, _ = Category.objects.get_or_create(department=clothing_dept, slug='silk-tops', defaults={'name': 'Silk Tops & Blouses', 'order': 4})

        # Skincare Categories
        cat_serums, _ = Category.objects.get_or_create(department=skincare_dept, slug='serums', defaults={'name': 'Serums & Elixirs', 'order': 1})
        cat_moisturizers, _ = Category.objects.get_or_create(department=skincare_dept, slug='moisturizers', defaults={'name': 'Creams & Moisturizers', 'order': 2})
        cat_cleansers, _ = Category.objects.get_or_create(department=skincare_dept, slug='cleansers', defaults={'name': 'Cleansers & Essences', 'order': 3})
        cat_sunscreen, _ = Category.objects.get_or_create(department=skincare_dept, slug='sunscreen', defaults={'name': 'Mineral Sunscreens', 'order': 4})

        # Makeup Categories
        cat_lips, _ = Category.objects.get_or_create(department=makeup_dept, slug='lips', defaults={'name': 'Lipsticks & Oils', 'order': 1})
        cat_complexion, _ = Category.objects.get_or_create(department=makeup_dept, slug='complexion', defaults={'name': 'Foundations & Tinted Serums', 'order': 2})
        cat_eyes, _ = Category.objects.get_or_create(department=makeup_dept, slug='eyes', defaults={'name': 'Eyeshadows & Mascaras', 'order': 3})
        cat_cheeks, _ = Category.objects.get_or_create(department=makeup_dept, slug='cheeks', defaults={'name': 'Blushes & Highlighters', 'order': 4})

        # 3. BRANDS
        brand_aura, _ = Brand.objects.get_or_create(name='Aura Atelier', slug='aura-atelier', defaults={'origin_country': 'France', 'is_featured': True})
        brand_lumina, _ = Brand.objects.get_or_create(name='Lumina Botanical', slug='lumina-botanical', defaults={'origin_country': 'Switzerland', 'is_featured': True})
        brand_velvet, _ = Brand.objects.get_or_create(name='Velvet Luxe', slug='velvet-luxe', defaults={'origin_country': 'Italy', 'is_featured': True})
        brand_maison, _ = Brand.objects.get_or_create(name='Maison de Soie', slug='maison-de-soie', defaults={'origin_country': 'United Kingdom', 'is_featured': True})
        brand_rose, _ = Brand.objects.get_or_create(name='Rosé Lab Clean Beauty', slug='rose-lab', defaults={'origin_country': 'South Korea', 'is_featured': True})

        # 4. STORE LOCATIONS (Global Hubs for Geolocation Store Locator)
        stores_data = [
            {
                'name': 'AURA LUXE Flagship - New York SoHo',
                'address': '482 Broome Street',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10013',
                'country': 'United States',
                'latitude': 40.7223,
                'longitude': -74.0018,
                'phone': '+1 (212) 555-0198',
            },
            {
                'name': 'AURA LUXE Beverly Hills Boutique',
                'address': '9600 Wilshire Boulevard',
                'city': 'Beverly Hills',
                'state': 'CA',
                'postal_code': '90212',
                'country': 'United States',
                'latitude': 34.0669,
                'longitude': -118.4038,
                'phone': '+1 (310) 555-0842',
            },
            {
                'name': 'AURA LUXE London Mayfair',
                'address': '32 Old Bond Street',
                'city': 'London',
                'state': 'England',
                'postal_code': 'W1S 4AP',
                'country': 'United Kingdom',
                'latitude': 51.5098,
                'longitude': -0.1416,
                'phone': '+44 20 7946 0912',
            },
            {
                'name': 'AURA LUXE Paris Atelier',
                'address': '18 Rue de la Paix',
                'city': 'Paris',
                'state': 'Île-de-France',
                'postal_code': '75002',
                'country': 'France',
                'latitude': 48.8698,
                'longitude': 2.3308,
                'phone': '+33 1 42 68 55 00',
            },
            {
                'name': 'AURA LUXE Luxury Boutique - Mumbai',
                'address': 'Pali Hill, Bandra West',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400050',
                'country': 'India',
                'latitude': 19.0600,
                'longitude': 72.8267,
                'phone': '+91 22 2640 1199',
            },
        ]
        for s in stores_data:
            StoreLocation.objects.get_or_create(name=s['name'], defaults=s)

        # 5. PRODUCTS (Clothing, Skincare, Makeup)
        products_data = [
            # --- CLOTHING ---
            {
                'department': clothing_dept,
                'category': cat_dresses,
                'brand': brand_aura,
                'name': 'Elysian Noir Bias-Cut Mulberry Silk Slip Gown',
                'sku': 'AL-CLO-001',
                'short_description': '100% Grade 6A mulberry silk with an architectural cowl neckline and liquid drape.',
                'description': 'Sculpted to contour effortlessly along natural curves, the Elysian Noir Slip Dress is cut on the bias from heavyweight 22-momme pure mulberry silk. Finished with delicate hand-rolled hems and adjustable micro-straps.',
                'details': '• 100% Pure Mulberry Silk (22 Momme)\n• Bias-cut for fluid movement\n• French seams with hand-finished edges\n• Dry clean only',
                'ingredients': '100% Certified Organic Mulberry Silk.',
                'price': Decimal('28500.00'),
                'compare_at_price': Decimal('35000.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#1E293B',
                'visual_tags': 'black, noir, silk, slip, dress, evening gown, elegant, cowl neck',
                'stock': 40,
                'rating': Decimal('4.95'),
                'review_count': 38,
                'is_featured': True,
                'is_bestseller': True,
                'variants': [
                    ('size', 'XS', Decimal('0.00'), '#1E293B'),
                    ('size', 'S', Decimal('0.00'), '#1E293B'),
                    ('size', 'M', Decimal('0.00'), '#1E293B'),
                    ('size', 'L', Decimal('0.00'), '#1E293B'),
                ]
            },
            {
                'department': clothing_dept,
                'category': cat_blazers,
                'brand': brand_velvet,
                'name': 'Milano Structured Wool-Blend Double-Breasted Blazer',
                'sku': 'AL-CLO-002',
                'short_description': 'Sharp peak lapels with structured shoulders tailored in fine Italian wool.',
                'description': 'A masterclass in modern power dressing. Features horn buttons, cupro lining, and a cinched yet relaxed silhouette that effortlessly bridges boardroom authority with evening chic.',
                'details': '• 85% Virgin Wool, 15% Cashmere\n• Full Bemberg Cupro breathable lining\n• Functional surgeon cuffs\n• Internal passport pocket',
                'ingredients': '85% Virgin Wool, 15% Cashmere; 100% Cupro lining.',
                'price': Decimal('34000.00'),
                'compare_at_price': Decimal('42000.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1584273143981-41c073dfe8f8?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#334155',
                'visual_tags': 'grey, slate, wool, blazer, jacket, tailored, double-breasted, coat',
                'stock': 25,
                'rating': Decimal('4.88'),
                'review_count': 24,
                'is_featured': True,
                'is_trending': True,
                'variants': [
                    ('size', '36 (US 4)', Decimal('0.00'), '#334155'),
                    ('size', '38 (US 6)', Decimal('0.00'), '#334155'),
                    ('size', '40 (US 8)', Decimal('0.00'), '#334155'),
                    ('size', '42 (US 10)', Decimal('0.00'), '#334155'),
                ]
            },
            {
                'department': clothing_dept,
                'category': cat_dresses,
                'brand': brand_maison,
                'name': 'Crimson Riviera Satin Halter Evening Maxi',
                'sku': 'AL-CLO-003',
                'short_description': 'High-shine liquid crimson satin with an open back and fluid train.',
                'description': 'Turn heads at galas and dinners. Cut from lustrous hammered satin in an intense ruby crimson hue with a dramatic halter tie and open back.',
                'details': '• Heavyweight fluid hammered satin\n• Cascading floor-length hem\n• Concealed side zip closure',
                'ingredients': '100% Silk-Touch Lustrous Viscose Satin.',
                'price': Decimal('26000.00'),
                'compare_at_price': Decimal('31000.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1539008835657-9e8e9680c956?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#991B1B',
                'visual_tags': 'red, crimson, ruby, satin, dress, halter, evening, formal, gown',
                'stock': 28,
                'rating': Decimal('4.92'),
                'review_count': 19,
                'is_trending': True,
                'variants': [
                    ('size', 'XS', Decimal('0.00'), '#991B1B'),
                    ('size', 'S', Decimal('0.00'), '#991B1B'),
                    ('size', 'M', Decimal('0.00'), '#991B1B'),
                ]
            },
            {
                'department': clothing_dept,
                'category': cat_knitwear,
                'brand': brand_aura,
                'name': 'Cloud-Soft Mongolian Cashmere Roll-Neck Sweater',
                'sku': 'AL-CLO-004',
                'short_description': 'Ultra-fine 2-ply Grade A Mongolian cashmere in warm sand ivory.',
                'description': 'Spun from pure combed cashmere fibers for featherweight warmth. Features ribbed trims, relaxed raglan sleeves, and a sumptuous fold-over collar.',
                'details': '• 100% Grade A Mongolian Cashmere\n• 2-ply yarn for pilling resistance\n• Hand wash cold or dry clean',
                'ingredients': '100% Sustainable Cashmere Wool.',
                'price': Decimal('22500.00'),
                'compare_at_price': Decimal('27500.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#D97706',
                'visual_tags': 'beige, sand, ivory, knit, sweater, cashmere, warm, winter, cream',
                'stock': 35,
                'rating': Decimal('4.85'),
                'review_count': 29,
                'variants': [
                    ('size', 'S', Decimal('0.00'), '#D97706'),
                    ('size', 'M', Decimal('0.00'), '#D97706'),
                    ('size', 'L', Decimal('0.00'), '#D97706'),
                ]
            },

            # --- SKINCARE ---
            {
                'department': skincare_dept,
                'category': cat_serums,
                'brand': brand_lumina,
                'name': 'Cellular Glow Multi-Molecular Hyaluronic & B5 Serum',
                'sku': 'AL-SKI-001',
                'short_description': '5 molecular weights of hyaluronic acid infused with botanical provitamin B5.',
                'description': 'Penetrates deep into dermal layers to flood dehydrated skin with instant bounce and cellular moisture. Clinically proven to increase epidermal hydration by 210% within 1 hour.',
                'details': '• Dermatologist tested & hypoallergenic\n• Oil-free, fragrance-free, vegan\n• Fast absorbing velvet texture',
                'ingredients': 'Aqua, Multi-Molecular Sodium Hyaluronate, Panthenol (B5), Centella Asiatica Extract, Polyglutamic Acid, Tremella Fuciformis (Snow Mushroom) Extract, Sodium PCA.',
                'price': Decimal('7800.00'),
                'compare_at_price': Decimal('9500.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1608248597359-216694380756?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#38BDF8',
                'visual_tags': 'blue, serum, hyaluronic, hydration, skincare, clear, moisture, glow',
                'stock': 90,
                'rating': Decimal('4.97'),
                'review_count': 64,
                'is_featured': True,
                'is_bestseller': True,
                'variants': [
                    ('volume', '30ml / 1.0 fl oz', Decimal('0.00'), ''),
                    ('volume', '50ml / 1.7 fl oz (Value Size)', Decimal('32.00'), ''),
                ]
            },
            {
                'department': skincare_dept,
                'category': cat_serums,
                'brand': brand_rose,
                'name': 'Phyto-Retinol Midnight Renewal Repair Elixir',
                'sku': 'AL-SKI-002',
                'short_description': 'Clean bakuchiol and encapsulated granactive retinoid in cold-pressed squalane.',
                'description': 'Target fine lines, hyperpigmentation, and texture overnight without peeling or irritation. Restores skin barrier integrity and awakens a rested, lit-from-within complexion.',
                'details': '• 2% Granactive Retinoid + 1% Ayurvedic Bakuchiol\n• Rosehip Seed & Blue Tansy infusion\n• Apply 3-4 drops nightly on cleansed face',
                'ingredients': 'Squalane, Bakuchiol, Dimethyl Isosorbide, Hydroxypinacolone Retinoate, Rosa Canina (Rosehip) Seed Oil, Tanacetum Annuum (Blue Tansy) Flower Oil, Tocopherol.',
                'price': Decimal('8800.00'),
                'compare_at_price': Decimal('11000.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1617897903246-719242758050?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#10B981',
                'visual_tags': 'green, botanical, oil, retinol, elixir, dropper, repair, night serum',
                'stock': 55,
                'rating': Decimal('4.90'),
                'review_count': 42,
                'is_trending': True,
                'variants': [
                    ('volume', '30ml / 1.0 fl oz', Decimal('0.00'), ''),
                ]
            },
            {
                'department': skincare_dept,
                'category': cat_moisturizers,
                'brand': brand_lumina,
                'name': 'Barrier Shield Ceramide & Peptide Rich Velvet Cream',
                'sku': 'AL-SKI-003',
                'short_description': 'Patented 3:1:1 physiological lipid ratio with copper tripeptide-1.',
                'description': 'A cocooning cloud-rich cream that instantly calms redness, locks in moisture for 72 hours, and fortifies compromised skin barriers against environmental pollutants.',
                'details': '• Essential Ceramides (EOP, NP, AP)\n• Free from synthetic fragrance and parabens\n• Ideal for dry, sensitive, or reactive skin',
                'ingredients': 'Aqua, Butyrospermum Parkii (Shea) Butter, Ceramide NP, Ceramide AP, Ceramide EOP, Phytosphingosine, Copper Tripeptide-1, Niacinamide, Squalane, Cholesterol.',
                'price': Decimal('7200.00'),
                'compare_at_price': Decimal('8500.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#FDE047',
                'visual_tags': 'cream, moisturizer, jar, white, ceramide, barrier repair, gold',
                'stock': 65,
                'rating': Decimal('4.89'),
                'review_count': 51,
                'variants': [
                    ('volume', '50ml / 1.7 oz Jar', Decimal('0.00'), ''),
                    ('volume', '100ml / 3.4 oz Luxe Tub', Decimal('45.00'), ''),
                ]
            },
            {
                'department': skincare_dept,
                'category': cat_sunscreen,
                'brand': brand_rose,
                'name': 'Luminous Veil Invisible Mineral Fluid Sunscreen SPF 50+',
                'sku': 'AL-SKI-004',
                'short_description': '100% non-nano zinc oxide with zero white cast and skin-perfecting primer finish.',
                'description': 'The sunscreen that feels like a weightless serum. Defends against UVA/UVB rays, blue light, and pollution while imparting a dewy, glass-skin radiant sheen.',
                'details': '• Broad Spectrum SPF 50+ PA++++\n• Reef safe, water-resistant for 40 minutes\n• Works seamlessly under makeup without pilling',
                'ingredients': 'Zinc Oxide 18.5%, Camellia Sinensis (Green Tea) Leaf Extract, Niacinamide 3%, Bisabolol, Hyaluronic Acid, Vitamin E.',
                'price': Decimal('4800.00'),
                'compare_at_price': None,
                'primary_image_url': 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#F472B6',
                'visual_tags': 'pink, sunscreen, spf 50, mineral, fluid, dewy, sun care, blush',
                'stock': 80,
                'rating': Decimal('4.93'),
                'review_count': 33,
                'variants': [
                    ('volume', '50ml / 1.7 fl oz', Decimal('0.00'), ''),
                ]
            },

            # --- MAKEUP ---
            {
                'department': makeup_dept,
                'category': cat_lips,
                'brand': brand_velvet,
                'name': 'Velour Rouge Ultra-Hydrating Satin Lipstick',
                'sku': 'AL-MAK-001',
                'short_description': 'One-swipe saturated pigment enveloped in cold-pressed Camellia oil.',
                'description': 'A bespoke lipstick housed in a weighted magnetic brass bullet. Blends intense color saturation with the cushiony comfort of a nourishing balm that wears for 10 hours without feathering.',
                'details': '• Magnetic click cap with engraved monogram\n• Enriched with Vitamin E & Meadowfoam seed oil\n• Featherweight cushion feel with semi-matte satin sheen',
                'ingredients': 'Dimethicone, Polyglyceryl-2 Triisostearate, Camellia Japonica Seed Oil, Limnanthes Alba (Meadowfoam) Seed Oil, Synthetic Wax, Silica, CI 15850, CI 77491.',
                'price': Decimal('4200.00'),
                'compare_at_price': Decimal('4800.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#BE123C',
                'visual_tags': 'red, lipstick, rouge, ruby, crimson, satin, matte, makeup, lips',
                'stock': 70,
                'rating': Decimal('4.96'),
                'review_count': 78,
                'is_featured': True,
                'is_bestseller': True,
                'variants': [
                    ('shade', '01 Ruby Sovereign', Decimal('0.00'), '#991B1B'),
                    ('shade', '02 Velvet Berry', Decimal('0.00'), '#881337'),
                    ('shade', '03 Cashmere Nude', Decimal('0.00'), '#B45309'),
                    ('shade', '04 Terracotta Rose', Decimal('0.00'), '#BE123C'),
                ]
            },
            {
                'department': makeup_dept,
                'category': cat_complexion,
                'brand': brand_aura,
                'name': 'Lumière Second-Skin Luminous Serum Foundation',
                'sku': 'AL-MAK-002',
                'short_description': 'Medium buildable coverage with 82% skincare serum base and micro-pearls.',
                'description': 'Blur imperfections while allowing your natural skin luminosity to shine through. Features adaptive self-setting polymers that resist heat, humidity, and transferring for 16 hours.',
                'details': '• 82% Skincare serum base with Peptides & Niacinamide\n• Natural satin-glow radiant finish\n• Non-comedogenic & breathable',
                'ingredients': 'Aqua, Cyclopentasiloxane, Glycerin, Niacinamide, Polyglyceryl-4 Isostearate, Acetyl Tetrapeptide-5, Diamond Powder, Mica, Iron Oxides (CI 77491, CI 77492, CI 77499).',
                'price': Decimal('6400.00'),
                'compare_at_price': Decimal('7500.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#D97706',
                'visual_tags': 'foundation, complexion, skin tint, nude, beige, glow, serum, liquid',
                'stock': 60,
                'rating': Decimal('4.87'),
                'review_count': 45,
                'is_featured': True,
                'variants': [
                    ('shade', '10N Porcelain Ivory', Decimal('0.00'), '#FEF3C7'),
                    ('shade', '20W Warm Sand', Decimal('0.00'), '#FDE68A'),
                    ('shade', '30N Golden Honey', Decimal('0.00'), '#D97706'),
                    ('shade', '40W Rich Amber', Decimal('0.00'), '#92400E'),
                    ('shade', '50C Deep Espresso', Decimal('0.00'), '#451A03'),
                ]
            },
            {
                'department': makeup_dept,
                'category': cat_eyes,
                'brand': brand_velvet,
                'name': 'Nocturne 12-Pan Gilded Eyeshadow Palette',
                'sku': 'AL-MAK-003',
                'short_description': 'Buttery velvet mattes, multidimensional metallics, and molten duochrome foils.',
                'description': 'From decadent champagne neutrals to smoldering smoked bronze and rich burgundy, each pan is micro-milled to glide like silk without fallout.',
                'details': '• 6 Velveteen Mattes, 4 Metallic Foils, 2 Duochrome Toppers\n• Mirrored faux-leather luxury compact\n• Vegan and cruelty-free formula',
                'ingredients': 'Mica, Talc, Zinc Stearate, Caprylic/Capric Triglyceride, Synthetic Fluorphlogopite, Tin Oxide, Titanium Dioxide, Carmine.',
                'price': Decimal('7600.00'),
                'compare_at_price': Decimal('9000.00'),
                'primary_image_url': 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#B45309',
                'visual_tags': 'palette, eyeshadow, bronze, gold, metallic, glitter, eyes, smoky, warm',
                'stock': 45,
                'rating': Decimal('4.94'),
                'review_count': 57,
                'is_trending': True,
                'variants': [
                    ('shade', 'Gilded Sunset (Complete Palette)', Decimal('0.00'), '#B45309'),
                ]
            },
            {
                'department': makeup_dept,
                'category': cat_lips,
                'brand': brand_rose,
                'name': 'Glace Nectar Lip Hydration Oil & Plumper',
                'sku': 'AL-MAK-004',
                'short_description': 'High-lacquer mirror shine infused with botanical peptides and cherry seed oil.',
                'description': 'Drench your lips in non-sticky, glass-like shine. Botanical Maxi-Lip peptides visibly enhance lip volume and smoothness with a sheer juicy tint.',
                'details': '• Custom jumbo doe-foot applicator\n• Non-sticky comfort glaze texture\n• Subtle natural vanilla-mint aroma',
                'ingredients': 'Hydrogenated Polyisobutene, Prunus Avium (Sweet Cherry) Seed Oil, Palmitoyl Tripeptide-1, Jojoba Seed Oil, Mentha Piperita Oil.',
                'price': Decimal('3400.00'),
                'compare_at_price': None,
                'primary_image_url': 'https://images.unsplash.com/photo-1625093742435-6fa192b6fb10?auto=format&fit=crop&w=1000&q=80',
                'secondary_image_url': 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=1000&q=80',
                'dominant_color_hex': '#F43F5E',
                'visual_tags': 'lip oil, gloss, pink, rose, shine, shimmer, lips, plumping, juicy',
                'stock': 85,
                'rating': Decimal('4.91'),
                'review_count': 39,
                'variants': [
                    ('shade', 'Rose Quartz (Sheer Pink)', Decimal('0.00'), '#FB7185'),
                    ('shade', 'Cherry Nectar (Deep Berry)', Decimal('0.00'), '#BE123C'),
                    ('shade', 'Golden Honey (Sparkling Amber)', Decimal('0.00'), '#FBBF24'),
                ]
            },
        ]

        for p_data in products_data:
            variants = p_data.pop('variants', [])
            product, created = Product.objects.get_or_create(
                sku=p_data['sku'],
                defaults=p_data
            )

            # Create variants
            for v_type, v_name, v_price, v_hex in variants:
                ProductVariant.objects.get_or_create(
                    product=product,
                    variant_type=v_type,
                    name=v_name,
                    defaults={
                        'additional_price': v_price,
                        'hex_color': v_hex,
                        'stock': 30,
                    }
                )

            # Create sample authentic reviews
            if created:
                reviews_sample = [
                    ('Genevieve V.', 5, 'Unmatched craftsmanship & luxury!', 'Worth every single penny. The presentation, quality, and feel are second to none.'),
                    ('Elena R.', 5, 'Stunning texture & results', 'The finish is absolutely mesmerizing. I have received compliments every time I wear this!'),
                    ('Camille B.', 5, 'My new everyday holy grail', 'Fast local delivery, impeccable packaging with custom tissue, and remarkable longevity.'),
                ]
                for author, stars, title, comment in reviews_sample:
                    ProductReview.objects.create(
                        product=product,
                        author_name=author,
                        rating=stars,
                        title=title,
                        comment=comment,
                        verified_buyer=False
                    )

        self.stdout.write(self.style.SUCCESS("[OK] Successfully seeded AURA LUXE catalog with clothing, skincare, makeup, variants, and store locations!"))

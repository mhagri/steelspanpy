# -*- coding: utf-8 -*-
"""
config.py
---------
Tüm kullanıcı girdilerini içeren yapılandırma modülü.
Geometri, yük, kesit ve deprem parametreleri burada tanımlanır.
"""

# ==============================================================================
# 1. GENEL AYARLAR
# ==============================================================================

# Başlangıç noktası [x, z]
SPOINT = [0, 0]

# Birim sistemi
# 5:kN-mm, 6:kN-m, 7:kgf-mm, 8:kgf-m, 9:N-mm, 10:N-m, 11:Ton-mm, 12:Ton-m
UNITS = 5


# ==============================================================================
# 2. GEOMETRİ
# ==============================================================================

GEOMETRY = {
    "span"          : 16000,   # mm
    "height"        : 2700,    # mm
    "ridge_height"  : 900,     # mm
    "num_axes"      : 6,       # aks aralık sayısı
    "axis_spacing"  : 3250,    # mm
}

# Çatı çaprazı maksimum bölme uzunluğu (mm)
MAX_BRACE_LENGTH = 2500

# Orta kolon ayarları
MID_COLUMNS = {
    "enabled"           : True,     # Orta kolon eklensin mi
    "count"             : 1,        # Eklenecek orta kolon adedi (her yarıya)
    "include_ridge"     : True,     # Mahya noktasına kolon eklensin mi
    "full_span"         : False,    # True: tüm açıklığı böl, False: her yarıyı ayrı böl
    "brace_divisions"   : 2,        # Orta kolonlarda çapraz bölme adedi
}

# Düşey çapraz ayarları
BRACE = {
    "type"          : "X",
    "pattern"       : [1, 0, 1, 0, 0, 1],
    "story_heights" : [0, 2700],   # ← bu önemli! h değeri
}


# ==============================================================================
# 3. KESİTLER
# ==============================================================================
# Format: [tip, isim, malzeme]
# Tipler: "I" (hadde profil), "CHS" (yuvarlak boru), "RHS" (dikdörtgen boru)

SECTIONS = {
    "column"        : ["I",   "HE400A",       "S275"],
    "beam"          : ["I",   "IPE450",        "S275"],
    "brace_v"       : ["CHS", "CHS139.9X5",   "S235"],
    "stability_v"   : ["CHS", "CHS139.9X5",   "S235"],
    "brace_r"       : ["CHS", "CHS88.9X5",    "S235"],
    "stability_r"   : ["CHS", "CHS88.9X4",    "S235"],
}

# Kullanılacak çelik malzemeler
STEEL_MATERIALS = ["S235", "S275", "S355"]


# ==============================================================================
# 4. YÜKLER
# ==============================================================================

LOADS = {
    "dead"  : 1.0,   # Sabit yük (kN/m2)
    "snow"  : 1.0,   # Kar yükü (kN/m2)
    "snow2" : 0.5,   # Tek taraf kar yükü (kN/m2)
}

# Yük tipleri (ETABS numaralandırması)
# 1:Dead, 2:SuperDead, 3:Live, 4:ReduceLive, 5:Quake,
# 6:Wind, 7:Snow, 8:Other, 10:Temperature, 11:Rooflive
LOAD_PATTERNS = {
    "DL" : 2,   # Düzeltilmiş sabit yük
    "S"  : 7,   # Kar
    "Ex" : 5,   # Deprem X
    "Ey" : 5,   # Deprem Y
}


# ==============================================================================
# 5. DEPREM
# ==============================================================================

SEISMIC = {
    "Sds"   : 0.563,    # Kısa periyot tasarım spektral ivme katsayısı
    "Sd1"   : 0.233,    # 1 sn periyot tasarım spektral ivme katsayısı
    "soil"  : "ZD",     # Zemin sınıfı
    "Rx"    : 5,        # X yönü taşıyıcı sistem katsayısı
    "Dx"    : 2,        # X yönü dayanım fazlalığı katsayısı
    "Ry"    : 5,        # Y yönü taşıyıcı sistem katsayısı
    "Dy"    : 2,        # Y yönü dayanım fazlalığı katsayısı
    "I"     : 1,        # Bina önem katsayısı
}

# -*- coding: utf-8 -*-
"""
geometry.py
-----------
Çerçeve geometrisini oluşturan yardımcı fonksiyonlar.
Nokta üretme, bölme ve çatı koordinatı hesaplama işlemleri burada yapılır.
"""

from .config import GEOMETRY, MID_COLUMNS


# ==============================================================================
# TEMEL YARDIMCI FONKSİYONLAR
# ==============================================================================

def split_number(start, end, num):
    """
    İki nokta arasını (num+1) eşit parçaya böler.
    Tüm noktaları (başlangıç ve bitiş dahil) döndürür.

    Parametreler:
        start (list): Başlangıç noktası [x, z]
        end   (list): Bitiş noktası [x, z]
        num   (int) : Araya eklenecek nokta sayısı

    Döndürür:
        list: [[x0,z0], [x1,z1], ..., [xn,zn]]
    """
    dx = (end[0] - start[0]) / (num + 1)
    dz = (end[1] - start[1]) / (num + 1)
    return [[start[0] + i * dx, start[1] + i * dz] for i in range(num + 2)]


def split_space(start, end, max_length):
    """
    İki nokta arasını maksimum uzunluğa göre böler.
    Segment sayısı uzunluk / max_length'e yuvarlanarak belirlenir.

    Parametreler:
        start      (list) : Başlangıç noktası [x, z]
        end        (list) : Bitiş noktası [x, z]
        max_length (float): İzin verilen maksimum segment uzunluğu (mm)

    Döndürür:
        list: [[x0,z0], [x1,z1], ..., [xn,zn]]
    """
    length = ((end[0] - start[0])**2 + (end[1] - start[1])**2) ** 0.5
    segments = max(1, round(length / max_length))
    dx = (end[0] - start[0]) / segments
    dz = (end[1] - start[1]) / segments
    return [[start[0] + i * dx, start[1] + i * dz] for i in range(segments + 1)]


def generate_pattern(zero_per_group, length):
    """
    Çapraz yerleşim örüntüsü üretir.
    Örnek: zero_per_group=2, length=7 → [1, 0, 0, 1, 0, 0, 1]

    Parametreler:
        zero_per_group (int): Her 1'den sonra kaç 0 geleceği
        length         (int): Toplam örüntü uzunluğu

    Döndürür:
        list: 0 ve 1'lerden oluşan liste
    """
    result = []
    while len(result) < length:
        result.append(1)
        for _ in range(zero_per_group):
            if len(result) < length:
                result.append(0)
    return result


# ==============================================================================
# ÇATI GEOMETRİSİ
# ==============================================================================

def generate_roof_points(spoint=None, span=None, height=None, ridge_height=None):
    """
    Çerçevenin 5 ana noktasını oluşturur.

        p1 ___p2___ p3
        |           |
        p0          p4

    p0: alt sol (temel)
    p1: sol kolon tepesi
    p2: mahya noktası
    p3: sağ kolon tepesi
    p4: alt sağ (temel)

    Parametreler:
        spoint       (list) : Başlangıç noktası [x, z]. None ise config'den alınır.
        span         (float): Açıklık (mm)
        height       (float): Kolon yüksekliği (mm)
        ridge_height (float): Mahya yüksekliği (mm)

    Döndürür:
        list: [p0, p1, p2, p3, p4]
    """
    from .config import SPOINT

    sp  = spoint       if spoint       is not None else SPOINT
    l   = span         if span         is not None else GEOMETRY["span"]
    h   = height       if height       is not None else GEOMETRY["height"]
    hm  = ridge_height if ridge_height is not None else GEOMETRY["ridge_height"]

    p0 = [sp[0],         sp[1]]
    p1 = [sp[0],         sp[1] + h]
    p2 = [sp[0] + l / 2, sp[1] + h + hm]
    p3 = [sp[0] + l,     sp[1] + h]
    p4 = [sp[0] + l,     sp[1]]

    return [p0, p1, p2, p3, p4]


def interpolate_z(x, p1, p2, p3):
    """
    Verilen x koordinatı için çatı eğrisindeki z yüksekliğini hesaplar.
    p1-p2 arası sol eğim, p2-p3 arası sağ eğim.

    Parametreler:
        x  (float): Yüksekliği hesaplanacak x koordinatı
        p1 (list) : Sol kolon tepesi [x, z]
        p2 (list) : Mahya noktası [x, z]
        p3 (list) : Sağ kolon tepesi [x, z]

    Döndürür:
        float: z yüksekliği
    """
    if x <= p2[0]:
        ratio = (x - p1[0]) / (p2[0] - p1[0]) if p2[0] != p1[0] else 0
        return p1[1] + ratio * (p2[1] - p1[1])
    else:
        ratio = (x - p2[0]) / (p3[0] - p2[0]) if p3[0] != p2[0] else 0
        return p2[1] + ratio * (p3[1] - p2[1])


# ==============================================================================
# ORTA KOLON NOKTALARI
# ==============================================================================

def get_mid_column_points(p1, p2, p3):
    """
    Orta kolon x-z koordinatlarını hesaplar.
    config.py'daki MID_COLUMNS ayarlarına göre çalışır.

    Parametreler:
        p1 (list): Sol kolon tepesi [x, z]
        p2 (list): Mahya noktası [x, z]
        p3 (list): Sağ kolon tepesi [x, z]

    Döndürür:
        list: Orta kolon noktaları [[x, z], ...]
    """
    num_divisions  = MID_COLUMNS["count"]
    include_ridge  = MID_COLUMNS["include_ridge"]
    full_span      = MID_COLUMNS["full_span"]

    if full_span:
        # Tüm açıklığı eşit böl, z'yi çatı eğrisinden hesapla
        dx = (p3[0] - p1[0]) / (num_divisions + 1)
        points = []
        for i in range(1, num_divisions + 1):
            x = p1[0] + i * dx
            z = interpolate_z(x, p1, p2, p3)
            points.append([x, z])

        if not include_ridge:
            points = [pt for pt in points if abs(pt[0] - p2[0]) > 1e-6]

    else:
        # Sol ve sağ yarıyı ayrı ayrı böl
        cols_left  = split_number(p1, p2, num_divisions)
        cols_right = split_number(p2, p3, num_divisions)

        inner_left  = cols_left[1:-1]
        inner_right = cols_right[1:-1]
        ridge_pt    = [p2] if include_ridge else []

        points = inner_left + ridge_pt + inner_right

    return points


# ==============================================================================
# GRİD BİLGİSİ
# ==============================================================================

def get_grid_config(geometry=None):
    """
    ETABS grid modelini oluşturmak için gereken parametreleri döndürür.

    Parametreler:
        geometry (dict): Geometri parametreleri. None ise config'den alınır.

    Döndürür:
        dict: ETABS NewGridOnly için gerekli parametreler
    """
    g = geometry if geometry is not None else GEOMETRY

    return {
        "NumberStorys"      : 2,
        "TypicalStoryHeight": g["ridge_height"] / 1000,
        "BottomStoryHeight" : g["height"] / 1000,
        "NumberLinesX"      : 3,
        "NumberLinesY"      : g["num_axes"] + 1,
        "SpacingX"          : g["span"] / 2000,
        "SpacingY"          : g["axis_spacing"] / 1000,
    }

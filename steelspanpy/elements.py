# -*- coding: utf-8 -*-
"""
elements.py
-----------
Yapısal elemanların ETABS'a eklenmesi.
Kolon, kiriş, düşey çapraz, stabilite ve çatı çaprazı fonksiyonları burada tanımlanır.
"""

from .config import GEOMETRY, SECTIONS, LOADS, BRACE, MID_COLUMNS
from .geometry import split_number, split_space, interpolate_z, get_mid_column_points


# ==============================================================================
# YARDIMCI
# ==============================================================================

def _sec(role):
    """Kesit adını kısa yoldan döndürür."""
    return SECTIONS[role][1]


# ==============================================================================
# ANA ÇERÇEVE (KOLON + KİRİŞ)
# ==============================================================================

def create_main_frame(SapModel, points, y=0, frame_index=0):
    """
    Bir aksın ana çerçeve elemanlarını (kolon + kiriş) oluşturur.
    points listesi: [p0, p1, p2, p3, p4]

    Sıra:
        i=0 → p0-p1 : Sol kolon
        i=1 → p1-p2 : Sol çatı kirişi
        i=2 → p2-p3 : Sağ çatı kirişi
        i=3 → p3-p4 : Sağ kolon

    Parametreler:
        SapModel    : ETABS SapModel nesnesi
        points      : [p0, p1, p2, p3, p4] koordinat listesi
        y           : Aksın Y koordinatı (mm)
        frame_index : İsim öneki için aks numarası
    """
    axel       = GEOMETRY["axis_spacing"]
    dead_load  = LOADS["dead"]
    snow_load  = LOADS["snow"]
    snow2_load = LOADS["snow2"]

    for i in range(len(points) - 1):
        start = points[i]
        end   = points[i + 1]
        name  = f"F{frame_index}_{i}"

        if i == 0 or i == 3:
            # Kolonlar
            SapModel.FrameObj.AddByCoord(
                start[0], y, start[1],
                end[0],   y, end[1],
                name, _sec("column")
            )
            SapModel.FrameObj.SetLoadDistributed(
                name, "Wx", 1, 7, 0, 1, 0.008, 0.008
            )

        elif i == 1 or i == 2:
            # Çatı kirişleri
            SapModel.FrameObj.AddByCoord(
                start[0], y, start[1],
                end[0],   y, end[1],
                name, _sec("beam")
            )
            # Sabit yük ve kar yükü (kN/mm'ye çevrilir)
            dl = dead_load  * axel * 1e-6
            sl = snow_load  * axel * 1e-6
            s2 = snow2_load * axel * 1e-6

            SapModel.FrameObj.SetLoadDistributed(name, "DL", 1, 10, 0, 1, dl, dl)
            SapModel.FrameObj.SetLoadDistributed(name, "S",  1, 10, 0, 1, sl, sl)

            if i == 1:
                # Sol kiriş: tam kar + rüzgar
                SapModel.FrameObj.SetLoadDistributed(name, "S2", 1, 10, 0, 1, sl, sl)
                SapModel.FrameObj.SetLoadDistributed(name, "Wx", 1,  2, 0, 1, 0.003, 0.003, "Local")
            else:
                # Sağ kiriş: azaltılmış kar + rüzgar
                SapModel.FrameObj.SetLoadDistributed(name, "S2", 1, 10, 0, 1, s2, s2)
                SapModel.FrameObj.SetLoadDistributed(name, "Wx", 1,  2, 0, 1, 0.004, 0.004, "Local")


def create_all_frames(SapModel, points):
    """
    Tüm akslar için ana çerçeveleri oluşturur.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        points   : [p0, p1, p2, p3, p4] koordinat listesi
    """
    num_axes   = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    height       = GEOMETRY["height"]
    span         = GEOMETRY["span"]

    print("Ana çerçeveler oluşturuluyor...")
    for i in range(num_axes + 1):
        y = i * axis_spacing
        create_main_frame(SapModel, points, y=y, frame_index=i)
            # Kolon başı kirişleri: sol ve sağ kolonları Y yönünde bağla
    
    for x in [0, span]:
        for i in range(num_axes):
            y1   = i * axis_spacing
            y2   = (i + 1) * axis_spacing
            name = f"CB_{int(x)}_{i}"
            SapModel.FrameObj.AddByCoord(
                x, y1, height,
                x, y2, height,
                name, _sec("beam")
            )
    print(f"  {num_axes + 1} aks için ana çerçeve tamamlandı.")


# ==============================================================================
# ORTA KOLONLAR
# ==============================================================================

def create_mid_columns(SapModel, p1, p2, p3):
    """
    Orta kolon noktalarını hesaplar ve ETABS'a ekler.
    Tüm akslar için kolon oluşturur.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        p1       : Sol kolon tepesi [x, z]
        p2       : Mahya noktası [x, z]
        p3       : Sağ kolon tepesi [x, z]

    Döndürür:
        list: Orta kolon noktaları [[x, z], ...]
    """
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]

    points = get_mid_column_points(p1, p2, p3)

    print("Orta kolonlar oluşturuluyor...")
    for i in range(num_axes + 1):
        y = i * axis_spacing
        for pt in points:
            x, z = pt
            name = f"MidCol_{int(x)}_{int(y)}"
            SapModel.FrameObj.AddByCoord(
                x, y, 0,
                x, y, z,
                name, _sec("column")
            )
    print(f"  {len(points)} orta kolon noktası, {num_axes + 1} aks için eklendi.")
    return points


# ==============================================================================
# DİKEY ÇAPRAZLAR
# ==============================================================================

def create_vertical_braces(SapModel, story_heights, y1=0, brace_type=None, x_coords=None):
    """
    Düşey çaprazları oluşturur. X, V veya K tipini destekler.

    Parametreler:
        SapModel      : ETABS SapModel nesnesi
        story_heights : Kat yükseklikleri listesi [z0, z1, ...]
        y1            : Başlangıç Y koordinatı (mm)
        brace_type    : "X", "V" veya "K". None ise config'den alınır.
        x_coords      : Çapraz eklenecek X koordinatları. None ise [0, span].
    """
    span   = GEOMETRY["span"]
    axel   = GEOMETRY["axis_spacing"]
    btype  = brace_type if brace_type is not None else BRACE["type"]
    xs     = x_coords   if x_coords   is not None else [0, span]
    y2     = y1 + axel

    for x in xs:
        for j in range(len(story_heights) - 1):
            z1 = story_heights[j]
            z2 = story_heights[j + 1]

            if btype == "X":
                SapModel.FrameObj.AddByCoord(
                    x, y1, z1, x, y2, z2, f"VB_X_{j}_x{int(x)}_y{int(y1)}_1", _sec("brace_v")
                )
                SapModel.FrameObj.AddByCoord(
                    x, y2, z1, x, y1, z2, f"VB_X_{j}_x{int(x)}_y{int(y1)}_2", _sec("brace_v")
                )

            elif btype == "V":
                mid_y = (y1 + y2) / 2
                SapModel.FrameObj.AddByCoord(
                    x, y1, z1, x, mid_y, z2, f"VB_V_{j}_x{int(x)}_y{int(y1)}_1", _sec("brace_v")
                )
                SapModel.FrameObj.AddByCoord(
                    x, y2, z1, x, mid_y, z2, f"VB_V_{j}_x{int(x)}_y{int(y1)}_2", _sec("brace_v")
                )

            elif btype == "K":
                mid_z = (z1 + z2) / 2
                SapModel.FrameObj.AddByCoord(
                    x, y1, z1, x, y2, mid_z, f"VB_K_{j}_x{int(x)}_y{int(y1)}_1", _sec("brace_v")
                )
                SapModel.FrameObj.AddByCoord(
                    x, y2, mid_z, x, y1, z2, f"VB_K_{j}_x{int(x)}_y{int(y1)}_2", _sec("brace_v")
                )

            else:
                raise ValueError(
                    f"Tanımsız çapraz tipi: '{btype}'. Geçerli tipler: 'X', 'V', 'K'"
                )


def create_all_vertical_braces(SapModel, story_heights):
    """
    Çapraz örüntüsüne göre tüm akslar için düşey çaprazları oluşturur.

    Parametreler:
        SapModel      : ETABS SapModel nesnesi
        story_heights : Kat yükseklikleri listesi
    """
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    pattern      = BRACE["pattern"]

    print("Düşey çaprazlar oluşturuluyor...")
    count = 0
    for i in range(num_axes):
        y = i * axis_spacing
        if pattern[i % len(pattern)] == 1:
            create_vertical_braces(SapModel, story_heights, y1=y)
            count += 1
    print(f"  {count} aks aralığına düşey çapraz eklendi.")


# ==============================================================================
# ORTA KOLON ÇAPRAZLARI
# ==============================================================================

def create_mid_braces(SapModel, mid_col_points, y1=0):
    """
    Orta kolonlar için düşey çapraz ve stabilite elemanları oluşturur.

    Parametreler:
        SapModel       : ETABS SapModel nesnesi
        mid_col_points : Orta kolon noktaları [[x, z], ...]
        y1             : Başlangıç Y koordinatı (mm)
    """
    brace_divs = MID_COLUMNS["brace_divisions"]

    for pt in mid_col_points:
        x, z_top = pt
        story_points  = split_number([x, 0], [x, z_top], brace_divs - 1)
        story_heights = [p[1] for p in story_points]

        create_vertical_braces(SapModel, story_heights, y1=y1, x_coords=[x])
        create_vertical_stability(SapModel, story_heights, x_coords=[x], y1=y1)


def create_all_mid_braces(SapModel, mid_col_points):
    """
    Çapraz örüntüsüne göre tüm akslar için orta kolon çaprazlarını oluşturur.

    Parametreler:
        SapModel       : ETABS SapModel nesnesi
        mid_col_points : Orta kolon noktaları [[x, z], ...]
    """
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    pattern      = BRACE["pattern"]

    print("Orta kolon çaprazları oluşturuluyor...")
    for i in range(num_axes):
        y = i * axis_spacing
        if pattern[i % len(pattern)] == 1:
            create_mid_braces(SapModel, mid_col_points, y1=y)
    print("  Orta kolon çaprazları tamamlandı.")


# ==============================================================================
# DİKEY STABİLİTE ELEMANLARI
# ==============================================================================

def create_vertical_stability(SapModel, story_heights, x_coords=None, y1=0):
    """
    Düşey stabilite elemanlarını (yatay bağlantı çubukları) oluşturur.
    Uç mafsallı (moment serbest) olarak tanımlanır.

    Parametreler:
        SapModel      : ETABS SapModel nesnesi
        story_heights : Kat yükseklikleri listesi
        x_coords      : Eleman eklenecek X koordinatları. None ise [0, span].
        y1            : Başlangıç Y koordinatı (mm)
    """
    span         = GEOMETRY["span"]
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    xs           = x_coords if x_coords is not None else [0, span]

    grid_y = [i * axis_spacing for i in range(num_axes + 1)]

    # Uç mafsalı tanımları (moment serbestliği)
    i_releases = [False, False, False, False, True, True]
    j_releases = [False, False, False, False, True, True]
    i_values   = [0.0] * 6
    j_values   = [0.0] * 6

    for x in xs:
        for i in range(len(grid_y) - 1):
            for j in range(len(story_heights) - 1):
                y_a = grid_y[i]
                y_b = grid_y[i + 1]
                z1  = story_heights[j]
                z2  = story_heights[j + 1]

                if z1 == 0:
                    continue

                name_bot = f"VS_bot_{j}_x{int(x)}_y{int(y_a)}"
                name_top = f"VS_top_{j}_x{int(x)}_y{int(y_a)}"

                SapModel.FrameObj.AddByCoord(
                    x, y_a, z1, x, y_b, z1, name_bot, _sec("stability_v")
                )
                SapModel.FrameObj.AddByCoord(
                    x, y_a, z2, x, y_b, z2, name_top, _sec("stability_v")
                )
                SapModel.FrameObj.SetReleases(
                    name_top, i_releases, j_releases, i_values, j_values
                )


def create_all_vertical_stability(SapModel, story_heights):
    """
    Tüm çerçeve için düşey stabilite elemanlarını oluşturur.

    Parametreler:
        SapModel      : ETABS SapModel nesnesi
        story_heights : Kat yükseklikleri listesi
    """
    print("Düşey stabilite elemanları oluşturuluyor...")
    create_vertical_stability(SapModel, story_heights)
    print("  Düşey stabilite elemanları tamamlandı.")


# ==============================================================================
# ÇATI ÇAPRAZLARI
# ==============================================================================

def create_roof_braces(SapModel, p1, p2, p3, mid_col_points=None):
    """
    Çatı çaprazlarını ve stabilite elemanlarını oluşturur.
    Çapraz örüntüsüne göre X çapraz veya uç+stabilite kombinasyonu kullanılır.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        p1       : Sol kolon tepesi [x, z]
        p2       : Mahya noktası [x, z]
        p3       : Sağ kolon tepesi [x, z]
    """
    from .config import MAX_BRACE_LENGTH

    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    pattern      = BRACE["pattern"]
    max_len      = MAX_BRACE_LENGTH

# Orta kolon noktalarını sol ve sağ olarak ayır
    left_cols  = sorted([pt for pt in (mid_col_points or []) if pt[0] < p2[0]], key=lambda pt: pt[0])
    right_cols = sorted([pt for pt in (mid_col_points or []) if pt[0] > p2[0]], key=lambda pt: pt[0])

    # Segmentleri orta kolonları da kapsayacak şekilde oluştur
    seg1 = [p1] + left_cols + [p2]
    seg2 = [p2] + right_cols + [p3]

    print("Çatı çaprazları oluşturuluyor...")
    for i in range(num_axes):
        y1 = i * axis_spacing
        y2 = (i + 1) * axis_spacing
        pat = pattern[i % len(pattern)]

        if pat == 1:
            # Tam X çapraz: tüm çatı boyunca
            all_pts = seg1 + seg2[1:]
            for j in range(len(all_pts) - 1):
                pt1 = all_pts[j]
                pt2 = all_pts[j + 1]
                SapModel.FrameObj.AddByCoord(
                    pt1[0], y1, pt1[1], pt2[0], y2, pt2[1],
                    f"RB_{i}_{j}_X1", _sec("brace_r")
                )
                SapModel.FrameObj.AddByCoord(
                    pt2[0], y1, pt2[1], pt1[0], y2, pt1[1],
                    f"RB_{i}_{j}_X2", _sec("brace_r")
                )

        else:
            # Çapraz yok: sadece uçlara X + aradaki segmentlere stabilite
            _add_end_braces_and_stability(SapModel, seg1, i, y1, y2, side="s1")
            _add_end_braces_and_stability(SapModel, seg2, i, y1, y2, side="s2")

    print("  Çatı çaprazları tamamlandı.")


def _add_end_braces_and_stability(SapModel, seg, i, y1, y2, side):
    """
    Bir çatı segmentinin başına ve sonuna X çapraz,
    aradaki noktalara stabilite elemanı ekler.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        seg      : Segment nokta listesi [[x,z], ...]
        i        : Aks indeksi (isim için)
        y1, y2   : Aks Y koordinatları
        side     : "s1" veya "s2" (isim için)
    """
    # Baş X çapraz
    pt1, pt2 = seg[0], seg[1]
    SapModel.FrameObj.AddByCoord(
        pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RB_{i}_{side}_start_X1", _sec("brace_r")
    )
    SapModel.FrameObj.AddByCoord(
        pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RB_{i}_{side}_start_X2", _sec("brace_r")
    )

    # Orta stabilite elemanları
    for j, pt in enumerate(seg[1:-1], start=1):
        SapModel.FrameObj.AddByCoord(
            pt[0], y1, pt[1], pt[0], y2, pt[1],
            f"RB_{i}_{side}_{j}_stab", _sec("stability_r")
        )

    # Son X çapraz
    pt1, pt2 = seg[-2], seg[-1]
    SapModel.FrameObj.AddByCoord(
        pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RB_{i}_{side}_end_X1", _sec("brace_r")
    )
    SapModel.FrameObj.AddByCoord(
        pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RB_{i}_{side}_end_X2", _sec("brace_r")
    )

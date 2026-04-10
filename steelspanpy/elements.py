# -*- coding: utf-8 -*-
"""
elements.py
-----------
Yapısal elemanların ETABS'a eklenmesi.
Kolon, kiriş, düşey çapraz, stabilite ve çatı çaprazı fonksiyonları burada tanımlanır.
"""

from .config import GEOMETRY, SECTIONS, LOADS, BRACE, MID_COLUMNS, MAX_BRACE_LENGTH
from .geometry import split_number, split_space, get_mid_column_points


# ==============================================================================
# YARDIMCI FONKSİYONLAR
# ==============================================================================

def _sec(role):
    """Kesit adını kısa yoldan döndürür."""
    return SECTIONS[role][1]


def _add_frame(SapModel, x1, y1, z1, x2, y2, z2, name, section):
    """Tek bir çubuk elemanı ekler — tekrar eden AddByCoord çağrısını kısaltır."""
    SapModel.FrameObj.AddByCoord(x1, y1, z1, x2, y2, z2, name, section)


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
    """
    axel       = GEOMETRY["axis_spacing"]
    dead_load  = LOADS["dead"]
    snow_load  = LOADS["snow"]
    snow2_load = LOADS["snow2"]

    dl = dead_load  * axel * 1e-6
    sl = snow_load  * axel * 1e-6
    s2 = snow2_load * axel * 1e-6

    for i in range(len(points) - 1):
        start = points[i]
        end   = points[i + 1]
        name  = f"F{frame_index}_{i}"

        if i == 0 or i == 3:
            _add_frame(SapModel, start[0], y, start[1], end[0], y, end[1], name, _sec("column"))
            SapModel.FrameObj.SetLoadDistributed(name, "Wx", 1, 7, 0, 1, 0.008, 0.008)

        elif i == 1 or i == 2:
            _add_frame(SapModel, start[0], y, start[1], end[0], y, end[1], name, _sec("beam"))
            SapModel.FrameObj.SetLoadDistributed(name, "DL", 1, 10, 0, 1, dl, dl)
            SapModel.FrameObj.SetLoadDistributed(name, "S",  1, 10, 0, 1, sl, sl)

            if i == 1:
                SapModel.FrameObj.SetLoadDistributed(name, "S2", 1, 10, 0, 1, sl, sl)
                SapModel.FrameObj.SetLoadDistributed(name, "Wx", 1,  2, 0, 1, 0.003, 0.003, "Local")
            else:
                SapModel.FrameObj.SetLoadDistributed(name, "S2", 1, 10, 0, 1, s2, s2)
                SapModel.FrameObj.SetLoadDistributed(name, "Wx", 1,  2, 0, 1, 0.004, 0.004, "Local")


def create_all_frames(SapModel, points):
    """
    Tüm akslar için ana çerçeveleri ve kolon başı kirişlerini oluşturur.
    """
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    height       = GEOMETRY["height"]
    span         = GEOMETRY["span"]

    print("Ana çerçeveler oluşturuluyor...")
    for i in range(num_axes + 1):
        create_main_frame(SapModel, points, y=i * axis_spacing, frame_index=i)

    # Kolon başı kirişleri: sol (x=0) ve sağ (x=span) kolonları Y yönünde bağla
    for x in [0, span]:
        for i in range(num_axes):
            y1 = i * axis_spacing
            y2 = (i + 1) * axis_spacing
            _add_frame(SapModel, x, y1, height, x, y2, height, f"CB_{int(x)}_{i}", _sec("beam"))

    print(f"  {num_axes + 1} aks için ana çerçeve ve kolon başı kirişler tamamlandı.")


# ==============================================================================
# ORTA KOLONLAR
# ==============================================================================

def create_mid_columns(SapModel, p1, p2, p3):
    """
    Orta kolon noktalarını hesaplar ve ETABS'a ekler.

    Döndürür:
        list: Orta kolon noktaları [[x, z], ...]
    """
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    col_points   = get_mid_column_points(p1, p2, p3)

    print("Orta kolonlar oluşturuluyor...")
    for i in range(num_axes + 1):
        y = i * axis_spacing
        for pt in col_points:
            x, z = pt
            _add_frame(SapModel, x, y, 0, x, y, z, f"MidCol_{int(x)}_{int(y)}", _sec("column"))

    print(f"  {len(col_points)} orta kolon noktası, {num_axes + 1} aks için eklendi.")
    return col_points


# ==============================================================================
# DİKEY ÇAPRAZLAR
# ==============================================================================

def create_vertical_braces(SapModel, story_heights, y1=0, brace_type=None, x_coords=None):
    """
    Düşey çaprazları oluşturur. X, V veya K tipini destekler.
    """
    span  = GEOMETRY["span"]
    axel  = GEOMETRY["axis_spacing"]
    btype = brace_type if brace_type is not None else BRACE["type"]
    xs    = x_coords   if x_coords   is not None else [0, span]
    y2    = y1 + axel

    for x in xs:
        for j in range(len(story_heights) - 1):
            z1  = story_heights[j]
            z2  = story_heights[j + 1]
            tag = f"{j}_x{int(x)}_y{int(y1)}"

            if btype == "X":
                _add_frame(SapModel, x, y1, z1, x, y2, z2, f"VB_X_{tag}_1", _sec("brace_v"))
                _add_frame(SapModel, x, y2, z1, x, y1, z2, f"VB_X_{tag}_2", _sec("brace_v"))
            elif btype == "V":
                mid_y = (y1 + y2) / 2
                _add_frame(SapModel, x, y1, z1, x, mid_y, z2, f"VB_V_{tag}_1", _sec("brace_v"))
                _add_frame(SapModel, x, y2, z1, x, mid_y, z2, f"VB_V_{tag}_2", _sec("brace_v"))
            elif btype == "K":
                mid_z = (z1 + z2) / 2
                _add_frame(SapModel, x, y1, z1, x, y2, mid_z, f"VB_K_{tag}_1", _sec("brace_v"))
                _add_frame(SapModel, x, y2, mid_z, x, y1, z2, f"VB_K_{tag}_2", _sec("brace_v"))
            else:
                raise ValueError(f"Tanımsız çapraz tipi: '{btype}'. Geçerli tipler: 'X', 'V', 'K'")


def create_all_vertical_braces(SapModel, story_heights):
    """Çapraz örüntüsüne göre tüm akslar için düşey çaprazları oluşturur."""
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    pattern      = BRACE["pattern"]

    print("Düşey çaprazlar oluşturuluyor...")
    count = 0
    for i in range(num_axes):
        if pattern[i % len(pattern)] == 1:
            create_vertical_braces(SapModel, story_heights, y1=i * axis_spacing)
            count += 1
    print(f"  {count} aks aralığına düşey çapraz eklendi.")


# ==============================================================================
# ORTA KOLON ÇAPRAZLARI
# ==============================================================================

def create_mid_braces(SapModel, mid_col_points, y1=0):
    """Orta kolonlar için düşey çapraz ve stabilite elemanları oluşturur."""
    brace_divs = MID_COLUMNS["brace_divisions"]

    for pt in mid_col_points:
        x, z_top      = pt
        story_points  = split_number([x, 0], [x, z_top], brace_divs - 1)
        story_heights = [p[1] for p in story_points]
        create_vertical_braces(SapModel, story_heights, y1=y1, x_coords=[x])
        create_vertical_stability(SapModel, story_heights, x_coords=[x], y1=y1)


def create_all_mid_braces(SapModel, mid_col_points):
    """Çapraz örüntüsüne göre tüm akslar için orta kolon çaprazlarını oluşturur."""
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    pattern      = BRACE["pattern"]

    print("Orta kolon çaprazları oluşturuluyor...")
    for i in range(num_axes):
        if pattern[i % len(pattern)] == 1:
            create_mid_braces(SapModel, mid_col_points, y1=i * axis_spacing)
    print("  Orta kolon çaprazları tamamlandı.")


# ==============================================================================
# DİKEY STABİLİTE ELEMANLARI
# ==============================================================================

def create_vertical_stability(SapModel, story_heights, x_coords=None, y1=0):
    """
    Düşey stabilite elemanlarını oluşturur.
    Uç mafsallı (moment serbest) olarak tanımlanır.
    """
    span         = GEOMETRY["span"]
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    xs           = x_coords if x_coords is not None else [0, span]
    grid_y       = [i * axis_spacing for i in range(num_axes + 1)]

    i_releases = [False, False, False, False, True, True]
    j_releases = [False, False, False, False, True, True]
    zero6      = [0.0] * 6

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

                _add_frame(SapModel, x, y_a, z1, x, y_b, z1, name_bot, _sec("stability_v"))
                _add_frame(SapModel, x, y_a, z2, x, y_b, z2, name_top, _sec("stability_v"))
                SapModel.FrameObj.SetReleases(name_top, i_releases, j_releases, zero6, zero6)


def create_all_vertical_stability(SapModel, story_heights):
    """Tüm çerçeve için düşey stabilite elemanlarını oluşturur."""
    print("Düşey stabilite elemanları oluşturuluyor...")
    create_vertical_stability(SapModel, story_heights)
    print("  Düşey stabilite elemanları tamamlandı.")


# ==============================================================================
# ÇATI ÇAPRAZLARI
# ==============================================================================

def _build_roof_seg(start, waypoints, end, max_len):
    """
    Başlangıç → ara noktalar → bitiş arasında segment listesi oluşturur.
    Her iki ara nokta arasındaki mesafe max_len'den büyükse ek bölme yapar.
    Bu sayede hem orta kolon aksları korunur hem de max uzunluk aşılmaz.
    """
    all_points = [start] + waypoints + [end]
    result = []
    for i in range(len(all_points) - 1):
        sub = split_space(all_points[i], all_points[i + 1], max_len)
        result += sub[:-1]
    result.append(all_points[-1])
    return result


def create_roof_braces(SapModel, p1, p2, p3, mid_col_points=None):
    """
    Çatı çaprazlarını ve stabilite elemanlarını oluşturur.

    Çapraz örüntüsüne (brace_pattern) göre:
        pat=1 → tüm çatı boyunca X çapraz
        pat=0 → sadece uç panellere X çapraz, aradakilere stabilite

    Orta kolon noktaları varsa segment sınırları olarak kullanılır.
    MAX_BRACE_LENGTH aşılırsa ek ara noktalar eklenir.
    """
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"]
    pattern      = BRACE["pattern"]
    max_len      = MAX_BRACE_LENGTH

    # Orta kolon noktalarını sol ve sağ yarıya göre ayır
    left_cols  = sorted([pt for pt in (mid_col_points or []) if pt[0] < p2[0]], key=lambda pt: pt[0])
    right_cols = sorted([pt for pt in (mid_col_points or []) if pt[0] > p2[0]], key=lambda pt: pt[0])

    # Segmentleri oluştur
    seg1 = _build_roof_seg(p1, left_cols, p2, max_len)
    seg2 = _build_roof_seg(p2, right_cols, p3, max_len)

    print("Çatı çaprazları oluşturuluyor...")
    for i in range(num_axes):
        y1  = i * axis_spacing
        y2  = (i + 1) * axis_spacing
        pat = pattern[i % len(pattern)]

        if pat == 1:
            all_pts = seg1 + seg2[1:]
            for j in range(len(all_pts) - 1):
                pt1, pt2 = all_pts[j], all_pts[j + 1]
                _add_frame(SapModel, pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RB_{i}_{j}_X1", _sec("brace_r"))
                _add_frame(SapModel, pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RB_{i}_{j}_X2", _sec("brace_r"))
        else:
            _add_end_braces_and_stability(SapModel, seg1, i, y1, y2, side="s1")
            _add_end_braces_and_stability(SapModel, seg2, i, y1, y2, side="s2")

    print("  Çatı çaprazları tamamlandı.")


def _add_end_braces_and_stability(SapModel, seg, i, y1, y2, side):
    """
    İlk ve son panele X çapraz, aradaki noktalara stabilite elemanı ekler.
    """
    if len(seg) < 2:
        return

    # İlk panel
    pt1, pt2 = seg[0], seg[1]
    _add_frame(SapModel, pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RB_{i}_{side}_start_X1", _sec("brace_r"))
    _add_frame(SapModel, pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RB_{i}_{side}_start_X2", _sec("brace_r"))

    # Orta noktalar: stabilite
    for j, pt in enumerate(seg[1:-1], start=1):
        _add_frame(SapModel, pt[0], y1, pt[1], pt[0], y2, pt[1], f"RB_{i}_{side}_{j}_stab", _sec("stability_r"))

    # Son panel (sadece 2'den fazla noktalıysa)
    if len(seg) > 2:
        pt1, pt2 = seg[-2], seg[-1]
        _add_frame(SapModel, pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RB_{i}_{side}_end_X1", _sec("brace_r"))
        _add_frame(SapModel, pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RB_{i}_{side}_end_X2", _sec("brace_r"))
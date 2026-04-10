# -*- coding: utf-8 -*-
"""
wind.py
-------
EN 1991-1-4 + Türkiye Ulusal Eki'ne göre rüzgar yükü hesabı ve ETABS'a yükleme.

Hesap adımları:
    1. Temel rüzgar hızı          : vb
    2. Ortalama rüzgar hızı       : vm(z)
    3. Türbülans yoğunluğu        : Iv(z)
    4. Pik hız basıncı            : qp(z)
    5. Basınç katsayıları         : cpe (duvar + çatı)
    6. Net yük                    : we = qp * cpe
    7. ETABS'a yükleme
"""

import math
from .config import GEOMETRY, WIND


# ==============================================================================
# ARAZI KATEGORİSİ PARAMETRELERİ
# EN 1991-1-4 Tablo 4.1
# ==============================================================================

TERRAIN_PARAMS = {
    "0"  : {"z0": 0.003, "z_min": 1,  "description": "Açık deniz"},
    "I"  : {"z0": 0.01,  "z_min": 1,  "description": "Göl veya düz arazi"},
    "II" : {"z0": 0.05,  "z_min": 2,  "description": "Düşük bitki örtüsü, izole engeller"},
    "III": {"z0": 0.3,   "z_min": 5,  "description": "Yerleşim alanları, ormanlar"},
    "IV" : {"z0": 1.0,   "z_min": 10, "description": "Kentsel alanlar"},
}

# Referans arazi pürüzlülüğü (Kategori II)
Z0_II = 0.05


# ==============================================================================
# ADIM 1: TEMEL RÜZGAR HIZI
# EN 1991-1-4 Mad. 4.2
# ==============================================================================

def calc_vb(wind=None):
    """
    Temel rüzgar hızını hesaplar.

    vb = c_dir * c_season * c_alt * vb0

    Türkiye NA'sında c_alt = 1.0 (yükseklik faktörü ayrıca uygulanmaz)

    Parametreler:
        wind : Rüzgar parametreleri sözlüğü. None ise config'den alınır.

    Döndürür:
        float: Temel rüzgar hızı (m/s)
    """
    w    = wind if wind is not None else WIND
    vb   = w["c_dir"] * w["c_season"] * w["c_alt"] * w["vb0"]
    return vb


# ==============================================================================
# ADIM 2: PÜRÜZLÜLÜK FAKTÖRÜ ve ORTALAMA RÜZGAR HIZI
# EN 1991-1-4 Mad. 4.3
# ==============================================================================

def calc_cr(z, terrain=None, wind=None):
    """
    Pürüzlülük faktörünü hesaplar.

    cr(z) = kr * ln(z/z0)          z_min <= z <= 200 m
    cr(z) = cr(z_min)              z < z_min

    Parametreler:
        z       : Referans yükseklik (m)
        terrain : Arazi kategorisi. None ise config'den alınır.
        wind    : Rüzgar parametreleri. None ise config'den alınır.

    Döndürür:
        float: Pürüzlülük faktörü
    """
    w   = wind    if wind    is not None else WIND
    tc  = terrain if terrain is not None else w["terrain"]
    tp  = TERRAIN_PARAMS[tc]
    z0  = tp["z0"]
    z_min = tp["z_min"]

    kr  = 0.19 * (z0 / Z0_II) ** 0.07  # Arazi faktörü

    z_eff = max(z, z_min)
    cr    = kr * math.log(z_eff / z0)
    return cr


def calc_c0(z):
    """
    Topoğrafya faktörü.
    Düz arazi için c0 = 1.0 (EN 1991-1-4 Mad. 4.3.3)
    Karmaşık topoğrafya için ayrıca hesaplanmalıdır.
    """
    return WIND.get("c0", 1.0)


def calc_vm(z, wind=None):
    """
    Ortalama rüzgar hızını hesaplar.

    vm(z) = cr(z) * c0(z) * vb

    Parametreler:
        z    : Referans yükseklik (m)
        wind : Rüzgar parametreleri. None ise config'den alınır.

    Döndürür:
        float: Ortalama rüzgar hızı (m/s)
    """
    vb = calc_vb(wind)
    cr = calc_cr(z, wind=wind)
    c0 = calc_c0(z)
    return cr * c0 * vb


# ==============================================================================
# ADIM 3: TÜRBÜLANS YOĞUNLUĞU
# EN 1991-1-4 Mad. 4.4
# ==============================================================================

def calc_Iv(z, wind=None):
    """
    Türbülans yoğunluğunu hesaplar.

    Iv(z) = sigma_v / vm(z) = kI / (c0 * ln(z/z0))

    Parametreler:
        z    : Referans yükseklik (m)
        wind : Rüzgar parametreleri. None ise config'den alınır.

    Döndürür:
        float: Türbülans yoğunluğu
    """
    w   = wind if wind is not None else WIND
    tc  = w["terrain"]
    tp  = TERRAIN_PARAMS[tc]
    z0  = tp["z0"]
    z_min = tp["z_min"]
    kI  = w.get("kI", 1.0)  # Türbülans faktörü (NA'da genellikle 1.0)
    c0  = calc_c0(z)

    z_eff = max(z, z_min)
    Iv    = kI / (c0 * math.log(z_eff / z0))
    return Iv


# ==============================================================================
# ADIM 4: PİK HIZ BASINCI
# EN 1991-1-4 Mad. 4.5
# ==============================================================================

def calc_qp(z, wind=None):
    """
    Pik hız basıncını hesaplar.

    qp(z) = [1 + 7*Iv(z)] * 0.5 * rho * vm(z)²    (kN/m²)

    Parametreler:
        z    : Referans yükseklik (m)
        wind : Rüzgar parametreleri. None ise config'den alınır.

    Döndürür:
        float: Pik hız basıncı (kN/m²)
    """
    w   = wind if wind is not None else WIND
    rho = w.get("rho", 1.25)  # kg/m³
    vm  = calc_vm(z, wind)
    Iv  = calc_Iv(z, wind)

    qp  = (1 + 7 * Iv) * 0.5 * rho * vm**2 / 1000  # N/m² → kN/m²
    return qp


# ==============================================================================
# ADIM 5: DIŞ BASINÇ KATSAYILARI (cpe)
# ==============================================================================

def calc_cpe_walls(h, b, d):
    """
    Duvar dış basınç katsayılarını hesaplar.
    EN 1991-1-4 Mad. 7.2.2, Tablo 7.1

    Bölgeler: A, B, C (rüzgar altı), D (rüzgar üstü), E (rüzgar arkası)

    Parametreler:
        h : Bina yüksekliği (m)
        b : Rüzgara dik genişlik (m)
        d : Rüzgar yönünde derinlik (m)

    Döndürür:
        dict: Her bölge için cpe,10 değerleri
    """
    h_d = h / d
    e   = min(b, 2 * h)

    # Bölge genişlikleri
    e_A = min(0.2 * e, d)
    e_B = min(0.8 * e, d) - e_A
    e_C = max(d - e, 0)

    # cpe,10 interpolasyonu h/d oranına göre
    if h_d <= 0.25:
        cpe_A, cpe_B, cpe_C = -1.2, -0.8, -0.5
        cpe_D, cpe_E        =  0.7, -0.3
    elif h_d <= 1.0:
        # Lineer interpolasyon 0.25 ile 1.0 arasında
        t = (h_d - 0.25) / 0.75
        cpe_A = -1.2 + t * (-1.2 - (-1.2))  # sabit
        cpe_B = -0.8
        cpe_C = -0.5
        cpe_D =  0.7 + t * (0.8 - 0.7)
        cpe_E = -0.3 + t * (-0.5 - (-0.3))
    elif h_d <= 5.0:
        t = (h_d - 1.0) / 4.0
        cpe_A = -1.2
        cpe_B = -0.8
        cpe_C = -0.5
        cpe_D =  0.8 + t * (0.8 - 0.8)
        cpe_E = -0.5 + t * (-0.7 - (-0.5))
    else:
        cpe_A, cpe_B, cpe_C = -1.2, -0.8, -0.5
        cpe_D, cpe_E        =  0.8, -0.7

    return {
        "A": cpe_A, "B": cpe_B, "C": cpe_C,
        "D": cpe_D, "E": cpe_E,
        "e_A": e_A, "e_B": e_B, "e_C": e_C, "e": e
    }


def calc_cpe_roof(alpha_deg, h, b, d):
    """
    Eğimli çatı dış basınç katsayılarını hesaplar.
    EN 1991-1-4 Mad. 7.2.5, Tablo 7.4a/b

    Parametreler:
        alpha_deg : Çatı eğim açısı (derece)
        h         : Bina yüksekliği (m)
        b         : Rüzgara dik genişlik (m)
        d         : Rüzgar yönünde derinlik (m)

    Döndürür:
        dict: F, G, H, I, J bölgeleri için cpe,10 değerleri (rüzgar altı ve üstü)
    """
    e = min(b, 2 * h)

    # Tablo 7.4a — Rüzgar altı (windward) eğim
    # alpha: -5, 5, 15, 30, 45, 60, 75 için cpe,10 değerleri
    # F, G, H bölgeleri
    if alpha_deg <= 5:
        F_w, G_w, H_w = -1.7, -1.2, -0.6
        F_l, G_l, H_l =  0.0,  0.0,  0.0
    elif alpha_deg <= 15:
        t = (alpha_deg - 5) / 10
        F_w = -1.7 + t * (-0.9 - (-1.7))
        G_w = -1.2 + t * (-0.8 - (-1.2))
        H_w = -0.6 + t * (-0.3 - (-0.6))
        F_l =  0.0 + t * (0.2 - 0.0)
        G_l =  0.0 + t * (0.2 - 0.0)
        H_l =  0.0 + t * (0.2 - 0.0)
    elif alpha_deg <= 30:
        t = (alpha_deg - 15) / 15
        F_w = -0.9 + t * (-0.5 - (-0.9))
        G_w = -0.8 + t * (-0.5 - (-0.8))
        H_w = -0.3 + t * (-0.2 - (-0.3))
        F_l =  0.2 + t * (0.7 - 0.2)
        G_l =  0.2 + t * (0.7 - 0.2)
        H_l =  0.2 + t * (0.4 - 0.2)
    elif alpha_deg <= 45:
        t = (alpha_deg - 30) / 15
        F_w = -0.5 + t * (-0.3 - (-0.5))
        G_w = -0.5 + t * (-0.3 - (-0.5))
        H_w = -0.2 + t * (-0.2 - (-0.2))
        F_l =  0.7 + t * (0.7 - 0.7)
        G_l =  0.7 + t * (0.7 - 0.7)
        H_l =  0.4 + t * (0.6 - 0.4)
    elif alpha_deg <= 60:
        t = (alpha_deg - 45) / 15
        F_w = -0.3 + t * (-0.3 - (-0.3))
        G_w = -0.3 + t * (-0.3 - (-0.3))
        H_w = -0.2 + t * (-0.2 - (-0.2))
        F_l =  0.7 + t * (0.7 - 0.7)
        G_l =  0.7 + t * (0.7 - 0.7)
        H_l =  0.6 + t * (0.7 - 0.6)
    else:
        F_w, G_w, H_w = -0.3, -0.3, -0.2
        F_l, G_l, H_l =  0.7,  0.7,  0.7

    # Tablo 7.4b — Rüzgar altı bölge I ve J (rüzgar arkası eğim)
    if alpha_deg <= 5:
        I_val, J_val = -0.6, -0.6
    elif alpha_deg <= 15:
        t = (alpha_deg - 5) / 10
        I_val = -0.6 + t * (-0.5 - (-0.6))
        J_val = -0.6 + t * (-0.3 - (-0.6))
    elif alpha_deg <= 30:
        t = (alpha_deg - 15) / 15
        I_val = -0.5 + t * (-0.4 - (-0.5))
        J_val = -0.3 + t * (-0.2 - (-0.3))
    else:
        I_val, J_val = -0.4, -0.2

    return {
        "F_windward": F_w, "G_windward": G_w, "H_windward": H_w,
        "F_leeward":  F_l, "G_leeward":  G_l, "H_leeward":  H_l,
        "I": I_val, "J": J_val,
        "e": e,
        "e_F": min(e/4, d/10),   # Bölge F genişliği
        "e_G": min(e/4, d/10),   # Bölge G genişliği
    }


# ==============================================================================
# ADIM 6 + 7: NET YÜK HESABI VE ETABS'A YÜKLEME
# ==============================================================================

def get_wind_pressures(wind=None):
    """
    Tüm rüzgar yükü hesabını yapar ve her yüzey için net basıncı döndürür.

    Parametreler:
        wind : Rüzgar parametreleri. None ise config'den alınır.

    Döndürür:
        dict: Hesap sonuçları ve yüzey basınçları
    """
    w = wind if wind is not None else WIND

    # Geometri (m cinsinden)
    h = GEOMETRY["height"]       / 1000   # kolon yüksekliği
    hm = GEOMETRY["ridge_height"] / 1000  # mahya yüksekliği
    span = GEOMETRY["span"]      / 1000   # açıklık (d)
    axel = GEOMETRY["axis_spacing"] / 1000
    num_axes = GEOMETRY["num_axes"]
    b = axel * num_axes                   # bina genişliği (b)
    d = span                              # bina derinliği (d)
    h_ridge = h + hm                      # mahya yüksekliği

    # Çatı eğim açısı
    alpha_deg = math.degrees(math.atan(hm / (span / 2)))

    # Referans yüksekliği (EN 1991-1-4 Mad. 7.2.2)
    z_ref = h_ridge

    # Pik hız basıncı
    qp = calc_qp(z_ref, wind)

    # Duvar katsayıları
    cpe_w = calc_cpe_walls(h_ridge, b, d)

    # Çatı katsayıları
    cpe_r = calc_cpe_roof(alpha_deg, h_ridge, b, d)

    # İç basınç katsayısı (EN 1991-1-4 Mad. 7.2.9)
    # Genel bina için cpi = +0.2 veya -0.3 (elverişsiz durum)
    cpi_pos = +0.2
    cpi_neg = -0.3

    # Net duvar basınçları (kN/m²)
    # we = qp * (cpe - cpi)  →  elverişsiz kombinasyon
    walls = {
        "D_suction": qp * (cpe_w["D"] - cpi_neg),   # Rüzgar üstü duvar (emme)
        "E_suction": qp * (cpe_w["E"] - cpi_pos),   # Rüzgar arkası duvar
        "A_suction": qp * (cpe_w["A"] - cpi_pos),   # Yan duvar A
        "B_suction": qp * (cpe_w["B"] - cpi_pos),   # Yan duvar B
    }

    # Net çatı basınçları (kN/m²)
    roof = {
        "H_windward_min": qp * (cpe_r["H_windward"] - cpi_pos),
        "H_windward_max": qp * (cpe_r["H_windward"] - cpi_neg),
        "H_leeward":      qp * (cpe_r["H_leeward"]  - cpi_neg),
        "I":              qp * (cpe_r["I"]           - cpi_pos),
    }

    return {
        "alpha_deg" : round(alpha_deg, 2),
        "z_ref"     : round(z_ref, 2),
        "vb"        : round(calc_vb(wind), 2),
        "vm"        : round(calc_vm(z_ref, wind), 2),
        "Iv"        : round(calc_Iv(z_ref, wind), 3),
        "qp"        : round(qp, 3),
        "cpe_walls" : cpe_w,
        "cpe_roof"  : cpe_r,
        "walls"     : {k: round(v, 3) for k, v in walls.items()},
        "roof"      : {k: round(v, 3) for k, v in roof.items()},
    }


def apply_wind_loads(SapModel, wind_load_name_x="Wx", wind_load_name_y="Wy", wind=None):
    """
    Hesaplanan rüzgar yüklerini ETABS'a uygular.

    Kolon yüzeylerine duvar basıncı, çatı kirişlerine çatı basıncı eklenir.
    X ve Y yönleri için ayrı ayrı uygulanır.

    Parametreler:
        SapModel         : ETABS SapModel nesnesi
        wind_load_name_x : X yönü rüzgar yük deseni adı
        wind_load_name_y : Y yönü rüzgar yük deseni adı
        wind             : Rüzgar parametreleri. None ise config'den alınır.
    """
    w       = wind if wind is not None else WIND
    results = get_wind_pressures(wind)
    qp      = results["qp"]

    # Geometri
    num_axes     = GEOMETRY["num_axes"]
    axis_spacing = GEOMETRY["axis_spacing"] / 1000  # m
    span         = GEOMETRY["span"]         / 1000  # m
    height       = GEOMETRY["height"]       / 1000  # m
    hm           = GEOMETRY["ridge_height"] / 1000  # m

    cpe_w = results["cpe_walls"]
    cpe_r = results["cpe_roof"]

    # iç basınç kombinasyonları
    cpi = w.get("cpi", -0.3)  # Elverişsiz iç basınç

    print("Rüzgar yükleri uygulanıyor...")
    print(f"  qp = {results['qp']} kN/m²")
    print(f"  Çatı açısı = {results['alpha_deg']}°")

    # ------------------------------------------------------------------
    # X YÖNÜ RÜZGARI: Rüzgar span (X) yönünde eser
    # Rüzgar üstü duvar (x=0) → D bölgesi
    # Rüzgar arkası duvar (x=span) → E bölgesi
    # ------------------------------------------------------------------

    # D bölgesi (rüzgar üstü, x=0 kolonları)
    p_D = qp * (cpe_w["D"] - cpi) / 1000 * axis_spacing  # kN/m → kN/mm * axel(m) → kN/m
    # E bölgesi (rüzgar arkası, x=span kolonları)
    p_E = qp * (cpe_w["E"] - cpi) / 1000 * axis_spacing

    # Çatı yükü X yönü — H bölgesi (kN/m kirişe)
    p_roof_Hx = qp * (cpe_r["H_windward"] - cpi) / 1000 * axis_spacing

    # Kolonlara X yönü rüzgar yükü uygula
    for i in range(num_axes + 1):
        y = i * axis_spacing * 1000  # mm'ye çevir

        # Sol kolon (x=0) — D bölgesi (pozitif basınç, içe doğru)
        name_left  = f"F{i}_0"
        # Sağ kolon (x=span) — E bölgesi (negatif basınç, dışa doğru)
        name_right = f"F{i}_3"

        try:
            # Global X yönünde uniform yük (kN/m → kN/mm)
            SapModel.FrameObj.SetLoadDistributed(
                name_left, wind_load_name_x, 1, 1, 0, 1,
                abs(p_D) * 1e-3, abs(p_D) * 1e-3
            )
            SapModel.FrameObj.SetLoadDistributed(
                name_right, wind_load_name_x, 1, 1, 0, 1,
                abs(p_E) * 1e-3, abs(p_E) * 1e-3
            )
        except Exception:
            pass  # Eleman yoksa atla

    # Çatı kirişlerine X yönü rüzgar yükü (lokal 2 ekseni, dike dik)
    for i in range(num_axes + 1):
        name_left_beam  = f"F{i}_1"
        name_right_beam = f"F{i}_2"
        try:
            SapModel.FrameObj.SetLoadDistributed(
                name_left_beam, wind_load_name_x, 1, 2, 0, 1,
                abs(p_roof_Hx) * 1e-3, abs(p_roof_Hx) * 1e-3, "Local"
            )
            SapModel.FrameObj.SetLoadDistributed(
                name_right_beam, wind_load_name_x, 1, 2, 0, 1,
                abs(p_roof_Hx) * 1e-3, abs(p_roof_Hx) * 1e-3, "Local"
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Y YÖNÜ RÜZGARI: Rüzgar aks (Y) yönünde eser
    # Kolon başı kirişlerine duvar basıncı uygulanır
    # ------------------------------------------------------------------

    p_Dy = qp * (cpe_w["D"] - cpi) / 1000 * span   # kN/m (açıklık boyunca)
    p_Ey = qp * (cpe_w["E"] - cpi) / 1000 * span

    # Kolon başı kirişleri (CB_) — Y yönü rüzgar
    for i in range(num_axes):
        name_left_cb  = f"CB_0_{i}"
        name_right_cb = f"CB_{int(span * 1000)}_{i}"
        try:
            SapModel.FrameObj.SetLoadDistributed(
                name_left_cb, wind_load_name_y, 1, 2, 0, 1,
                abs(p_Dy) * 1e-3, abs(p_Dy) * 1e-3
            )
            SapModel.FrameObj.SetLoadDistributed(
                name_right_cb, wind_load_name_y, 1, 2, 0, 1,
                abs(p_Ey) * 1e-3, abs(p_Ey) * 1e-3
            )
        except Exception:
            pass

    print("  Rüzgar yükleri uygulandı.")
    print(f"  D bölgesi (rüzgar üstü) : {results['walls']['D_suction']:.3f} kN/m²")
    print(f"  E bölgesi (rüzgar arkası): {results['walls']['E_suction']:.3f} kN/m²")
    return results


def print_wind_summary(wind=None):
    """
    Rüzgar yükü hesabını terminale yazdırır — kontrol amacıyla.
    """
    r = get_wind_pressures(wind)
    print("\n" + "=" * 50)
    print("  EN 1991-1-4 Rüzgar Yükü Özeti")
    print("=" * 50)
    print(f"  Temel rüzgar hızı  vb  = {r['vb']} m/s")
    print(f"  Ort. rüzgar hızı   vm  = {r['vm']} m/s")
    print(f"  Türbülans yoğ.     Iv  = {r['Iv']}")
    print(f"  Pik hız basıncı    qp  = {r['qp']} kN/m²")
    print(f"  Çatı eğim açısı    α   = {r['alpha_deg']}°")
    print(f"\n  Duvar Basınçları (kN/m²):")
    for k, v in r["walls"].items():
        print(f"    {k:20s}: {v:.3f}")
    print(f"\n  Çatı Basınçları (kN/m²):")
    for k, v in r["roof"].items():
        print(f"    {k:20s}: {v:.3f}")
    print("=" * 50)

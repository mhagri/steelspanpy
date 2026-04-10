# -*- coding: utf-8 -*-
"""
loads.py
--------
Yük desenleri, yük kombinasyonları ve kütle kaynağı tanımlama işlemleri.
TBDY 2018 yük kombinasyonları esas alınmıştır.
"""

from .config import LOAD_PATTERNS


# ==============================================================================
# YÜK DESENLERİ
# ==============================================================================

def setup_load_patterns(SapModel):
    """
    ETABS'taki varsayılan yük desenlerini yeniden adlandırır
    ve config'deki ek yük desenlerini ekler.

    Parametreler:
        SapModel : ETABS SapModel nesnesi

    Döndürür:
        dict: Yük türlerine göre ayrılmış yük deseni listeleri
              {"dead", "live", "snow", "wind", "quake", "temp", "roof"}
    """
    # Varsayılan ETABS yüklerini yeniden adlandır
    SapModel.LoadPatterns.ChangeName("Dead", "SW")
    SapModel.LoadCases.ChangeName("Dead", "SW")
    SapModel.LoadPatterns.ChangeName("Live", "LL")
    SapModel.LoadCases.ChangeName("Live", "LL")

    # Yük gruplarını başlat
    groups = {
        "dead"  : ["SW"],
        "live"  : ["LL"],
        "snow"  : [],
        "wind"  : [],
        "quake" : [],
        "temp"  : [],
        "roof"  : [],
    }

    # Config'deki yük desenlerini ekle ve grupla
    for name, load_type in LOAD_PATTERNS.items():
        SapModel.LoadPatterns.Add(name, load_type)
        _classify_load(name, load_type, groups)

    # Çatı yükleri = kar + diğer çatı yükleri
    groups["roof"] = groups["snow"] + groups["roof"]

    print("Yük desenleri tanımlandı:")
    for group, items in groups.items():
        if items:
            print(f"  {group:8s}: {', '.join(items)}")

    return groups


def _classify_load(name, load_type, groups):
    """
    Yük tipine göre ilgili gruba ekler.

    ETABS yük tipi numaraları:
        1,2 → Dead/SuperDead
        3   → Live
        4,11→ ReduceLive/RoofLive
        5   → Quake
        6   → Wind
        7   → Snow
        10  → Temperature
    """
    if load_type in (1, 2):
        groups["dead"].append(name)
    elif load_type == 3:
        groups["live"].append(name)
    elif load_type in (4, 11):
        groups["roof"].append(name)
    elif load_type == 5:
        groups["quake"].append(name)
    elif load_type == 6:
        groups["wind"].append(name)
    elif load_type == 7:
        groups["snow"].append(name)
    elif load_type == 10:
        groups["temp"].append(name)


# ==============================================================================
# KÜTLE KAYNAĞI
# ==============================================================================

def setup_mass_source(SapModel, groups):
    """
    Deprem kütlesi kaynağını tanımlar.
    Kar yükleri 0.8, sabit ve hareketli yükler 1.0 katsayısıyla dahil edilir.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        groups   : setup_load_patterns'dan dönen yük grubu sözlüğü
    """
    snow_loads = groups["snow"]
    dead_loads = groups["dead"]
    live_loads = groups["live"]

    mass_src = {}
    for s in snow_loads:
        mass_src[s] = 0.8
    for d in dead_loads:
        mass_src[d] = 1.0
    if live_loads:
        mass_src[live_loads[0]] = 1.0

    SapModel.PropMaterial.SetMassSource(
        2,
        len(mass_src),
        list(mass_src.keys()),
        list(mass_src.values())
    )
    print(f"  Kütle kaynağı tanımlandı: {mass_src}")


# ==============================================================================
# YARDIMCI KOMBİNASYON FONKSİYONLARI
# ==============================================================================

def _add_combo(SapModel, name, cases):
    """
    Tek bir yük kombinasyonu oluşturur.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        name     : Kombinasyon adı
        cases    : [(yük_adı, case_type, katsayı), ...]
                   case_type: 0=LoadCase, 1=LoadCombo
    """
    SapModel.RespCombo.Add(name, 0)
    for load_name, case_type, factor in cases:
        SapModel.RespCombo.SetCaseList(name, case_type, load_name, factor)


def _add_temp_to_combo(SapModel, name, temp_loads):
    """
    Bir kombinasyona sıcaklık yükü ekler.

    Parametreler:
        SapModel   : ETABS SapModel nesnesi
        name       : Kombinasyon adı
        temp_loads : Sıcaklık yükü listesi
    """
    for t in temp_loads:
        SapModel.RespCombo.SetCaseList(name, 0, t, 1.0)


# ==============================================================================
# TEMEL KOMBİNASYONLAR
# ==============================================================================

def setup_base_combos(SapModel, groups):
    """
    G (sabit) ve Q (hareketli) temel kombinasyonlarını oluşturur.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        groups   : Yük grubu sözlüğü
    """
    # G = tüm sabit yükler
    SapModel.RespCombo.Add("G", 0)
    for g in groups["dead"]:
        SapModel.RespCombo.SetCaseList("G", 0, g, 1.0)

    # Q = tüm hareketli yükler
    SapModel.RespCombo.Add("Q", 0)
    for q in groups["live"]:
        SapModel.RespCombo.SetCaseList("Q", 0, q, 1.0)


# ==============================================================================
# DEPREM KOMBİNASYONLARI
# ==============================================================================

def setup_seismic_combos(SapModel, spect_cases):
    """
    Edx ve Edy deprem kombinasyonlarını oluşturur.
    %30 kuralı uygulanır.

    Parametreler:
        SapModel    : ETABS SapModel nesnesi
        spect_cases : Spektrum analiz durumları ["ERx", "ERy", "ERz"]
    """
    _add_combo(SapModel, "Edx", [(spect_cases[0], 0, 1.0), (spect_cases[1], 0, 0.3)])
    _add_combo(SapModel, "Edy", [(spect_cases[0], 0, 0.3), (spect_cases[1], 0, 1.0)])


# ==============================================================================
# TBDY 2018 YÜK KOMBİNASYONLARI
# ==============================================================================

def setup_all_combinations(SapModel, groups, spect_cases):
    """
    TBDY 2018'e göre tüm yük kombinasyonlarını oluşturur.

    Kombinasyon numaraları:
        1     → 1.4G
        2a    → 1.2G + 1.6S (her kar yükü için)
        2b    → 1.2G + 1.6Q + 0.5S
        3     → 1.2G + 1.6S + 0.8W
        4     → 1.2G + 1.0Q + 0.5S + 1.6W
        5     → 1.2G + 1.0Q + 0.2S + 1.0E
        6     → 0.9G + 1.6W
        7     → 0.9G + 1.0E
        D1-D3 → Kullanım (deplasman) kombinasyonları

    Parametreler:
        SapModel    : ETABS SapModel nesnesi
        groups      : Yük grubu sözlüğü
        spect_cases : Spektrum analiz durumları listesi
    """
    roof  = groups["roof"]
    wind  = groups["wind"]
    snow  = groups["snow"]
    temp  = groups["temp"]

    print("Yük kombinasyonları oluşturuluyor...")

    # Temel kombinasyonlar
    setup_base_combos(SapModel, groups)

    # Deprem kombinasyonları
    setup_seismic_combos(SapModel, spect_cases)

    # --- Kombinasyon 1: 1.4G ---
    _add_combo(SapModel, "1_1.4G", [("G", 1, 1.4)])

    # --- Kombinasyon 2a: 1.2G + 1.6S ---
    for r in roof:
        name = f"2a_1.2G+1.6{r}"
        _add_combo(SapModel, name, [("G", 1, 1.2), (r, 0, 1.6)])
        _add_temp_to_combo(SapModel, name, temp)

    # --- Kombinasyon 2b: 1.2G + 1.6Q + 0.5S ---
    if roof:
        for r in roof:
            name = f"2b_1.2G+1.6Q+0.5{r}"
            _add_combo(SapModel, name, [("G", 1, 1.2), ("Q", 1, 1.6), (r, 0, 0.5)])
            _add_temp_to_combo(SapModel, name, temp)
    else:
        name = "2b_1.2G+1.6Q"
        _add_combo(SapModel, name, [("G", 1, 1.2), ("Q", 1, 1.6)])
        _add_temp_to_combo(SapModel, name, temp)

    # --- Kombinasyon 3: 1.2G + 1.6S + 0.8W ---
    for r in roof:
        for w in wind:
            name = f"3_1.2G+1.6{r}+0.8{w}"
            _add_combo(SapModel, name, [("G", 1, 1.2), ("Q", 1, 1.0), (r, 0, 1.6), (w, 0, 0.8)])
            _add_temp_to_combo(SapModel, name, temp)

    # --- Kombinasyon 4: 1.2G + 1.0Q + 0.5S + 1.6W ---
    if roof:
        for w in wind:
            for r in roof:
                name = f"4_1.2G+1.0Q+0.5{r}+1.6{w}"
                _add_combo(SapModel, name, [("G", 1, 1.2), ("Q", 1, 1.0), (r, 0, 0.5), (w, 0, 1.6)])
                _add_temp_to_combo(SapModel, name, temp)
    else:
        for w in wind:
            name = f"4_1.2G+1.0Q+1.6{w}"
            _add_combo(SapModel, name, [("G", 1, 1.2), ("Q", 1, 1.0), (w, 0, 1.6)])
            _add_temp_to_combo(SapModel, name, temp)

    # --- Kombinasyon 5: 1.2G + 1.0Q + 0.2S + 1.0E ---
    for E in ["Edx", "Edy"]:
        if snow:
            for S in snow:
                name = f"5_1.2G+1.0Q+0.2{S}+1.0{E}"
                _add_combo(SapModel, name, [
                    ("G", 1, 1.2), ("Q", 1, 1.0),
                    (S, 0, 0.2), (E, 1, 1.0),
                    (spect_cases[2], 0, 0.3)
                ])
                _add_temp_to_combo(SapModel, name, temp)
        else:
            name = f"5_1.2G+1.0Q+1.0{E}"
            _add_combo(SapModel, name, [
                ("G", 1, 1.2), ("Q", 1, 1.0),
                (E, 1, 1.0), (spect_cases[2], 0, 0.3)
            ])
            _add_temp_to_combo(SapModel, name, temp)

    # --- Kombinasyon 6: 0.9G + 1.6W ---
    for w in wind:
        name = f"6_0.9G+1.6{w}"
        _add_combo(SapModel, name, [("G", 1, 0.9), (w, 0, 1.6)])
        _add_temp_to_combo(SapModel, name, temp)

    # --- Kombinasyon 7: 0.9G + 1.0E ---
    for E in ["Edx", "Edy"]:
        name = f"7_0.9G+1.0{E}"
        _add_combo(SapModel, name, [("G", 1, 0.9), (E, 1, 1.0), (spect_cases[2], 0, -0.3)])
        _add_temp_to_combo(SapModel, name, temp)

    # --- Deplasman kombinasyonları ---
    _add_combo(SapModel, "D1_G+Q", [("G", 1, 1.0), ("Q", 1, 1.0)])

    for S in snow:
        _add_combo(SapModel, f"D2_G+0.5{S}", [("G", 1, 1.0), (S, 0, 0.5)])

    for W in wind:
        _add_combo(SapModel, f"D3_G+1.0{W}", [("G", 1, 1.0), (W, 0, 1.0)])

    print(f"  Yük kombinasyonları tamamlandı.")

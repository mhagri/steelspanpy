# -*- coding: utf-8 -*-
"""
seismic.py
----------
Deprem hesabı ve tepki spektrumu fonksiyonları.
TBDY 2018 (Türkiye Bina Deprem Yönetmeliği) esas alınmıştır.
"""

import numpy as np
from config import SEISMIC


# ==============================================================================
# YARDIMCI: SAYI FORMATLAMA
# ==============================================================================

def _to_etabs_str(value):
    """
    Sayıyı ETABS'ın beklediği formata çevirir.
    Ondalık ayracı nokta yerine virgül kullanılır.

    Parametreler:
        value : Sayı veya string

    Döndürür:
        str: Virgüllü string → örn. "0,563"
    """
    return str(value).replace(".", ",")


# ==============================================================================
# TBDY 2018 OTOMATİK DEPREM YÜKLERİ
# ==============================================================================

def define_tsc2018(SapModel, name, grid_info, seismic=None):
    """
    TBDY 2018'e göre otomatik deprem yükü tanımlar.
    ETABS veritabanı tablosu üzerinden ayarlanır.

    Parametreler:
        SapModel   : ETABS SapModel nesnesi
        name       : Yük deseni adı → "Ex" veya "Ey"
        grid_info  : Grid bilgisi sözlüğü (kat sayısı için)
        seismic    : Deprem parametreleri sözlüğü. None ise config'den alınır.
    """
    s = seismic if seismic is not None else SEISMIC

    # X veya Y yönü belirleme
    if name == "Ex":
        x_dir, y_dir = "Yes", "No"
    elif name == "Ey":
        x_dir, y_dir = "No", "Yes"
    else:
        raise ValueError(f"Geçersiz deprem yükü adı: '{name}'. 'Ex' veya 'Ey' olmalı.")

    headers = [
        'Name', 'IsAuto',
        'XDir', 'XDirPlusE', 'XDirMinusE',
        'YDir', 'YDirPlusE', 'YDirMinusE',
        'EccRatio', 'TopStory', 'BotStory', 'OverStory',
        'OverDiaph', 'OverEcc', 'PeriodType', 'CtAndX',
        'UserT', 'Ss', 'S1', 'TL', 'SiteClass', 'R', 'D', 'I'
    ]

    values = [
        name, 'No',
        x_dir, 'No', 'No',
        y_dir, 'No', 'No',
        '0,05',
        f"Story{grid_info['NumberStorys']}",
        'Base', '', '', '',
        'Program Calculated', '0.08;0.75',
        '',
        _to_etabs_str(s["Sds"]),
        _to_etabs_str(s["Sd1"]),
        '6',
        s["soil"],
        str(s["Rx"] if name == "Ex" else s["Ry"]),
        _to_etabs_str(s["Dx"] if name == "Ex" else s["Dy"]),
        _to_etabs_str(s["I"]),
    ]

    SapModel.DatabaseTables.SetTableForEditingArray(
        "Load Pattern Definitions - Auto Seismic - TSC 2018",
        1, headers, 1, values
    )
    SapModel.DatabaseTables.ApplyEditedTables("True")
    print(f"  TBDY 2018 deprem yükü tanımlandı: {name}")


def define_all_seismic_loads(SapModel, quake_loads, grid_info, seismic=None):
    """
    Tüm deprem yüklerini ETABS'a tanımlar.

    Parametreler:
        SapModel    : ETABS SapModel nesnesi
        quake_loads : Deprem yükü adlarının listesi → ["Ex", "Ey"]
        grid_info   : Grid bilgisi sözlüğü
        seismic     : Deprem parametreleri sözlüğü. None ise config'den alınır.
    """
    s = seismic if seismic is not None else SEISMIC

    # Her deprem yönü için R ve D katsayılarını eşleştir
    rq_info = {
        0: {"Name": f"R{s['Rx']}D{s['Dx']}_X", "R": s["Rx"], "D": s["Dx"], "I": s["I"]},
        1: {"Name": f"R{s['Ry']}D{s['Dy']}_Y", "R": s["Ry"], "D": s["Dy"], "I": s["I"]},
    }

    print("Deprem yükleri tanımlanıyor...")
    for idx, ql in enumerate(quake_loads):
        define_tsc2018(SapModel, ql, grid_info, seismic)

    return rq_info


# ==============================================================================
# YATAY ELASTİK TASARIM SPEKTRUMU — Sae(T)
# ==============================================================================

def compute_sae(name, sds, sd1, r, d, i, T_max=5.0, dt=0.01):
    """
    TBDY 2018'e göre yatay elastik tasarım spektrumu hesaplar.

    Parametreler:
        name  : Spektrum adı
        sds   : Kısa periyot tasarım spektral ivme katsayısı
        sd1   : 1 sn periyot tasarım spektral ivme katsayısı
        r     : Taşıyıcı sistem katsayısı
        d     : Dayanım fazlalığı katsayısı
        i     : Bina önem katsayısı
        T_max : Maksimum periyot (s)
        dt    : Periyot adımı (s)

    Döndürür:
        list: ETABS tablo formatında [name, T, Sae, name, T, Sae, ...]
    """
    T_B = sd1 / sds
    T_A = 0.2 * T_B
    T_L = 6.0

    period = np.arange(0, T_max + dt, dt)
    values = []

    for T in period:
        if 0 <= T <= T_A:
            sae = ((0.4 + 0.6 * (T / T_A)) * sds) / (d + (r / i - d) * T / T_B)
        elif T_A < T <= T_B:
            sae = sds / (d + (r / i - d) * T / T_B)
        elif T_B < T <= T_L:
            sae = (sd1 / T) / (r / i)
        else:
            sae = (sd1 * (T_L / T**2)) / (r / i)

        values.extend([
            _to_etabs_str(name),
            _to_etabs_str(T),
            _to_etabs_str(sae)
        ])

    return values


# ==============================================================================
# DİKEY ELASTİK TASARIM SPEKTRUMU — Saed(T)
# ==============================================================================

def compute_saed(name, sds, sd1, dt=0.01):
    """
    TBDY 2018'e göre düşey elastik tasarım spektrumu hesaplar.

    Parametreler:
        name : Spektrum adı
        sds  : Kısa periyot tasarım spektral ivme katsayısı
        sd1  : 1 sn periyot tasarım spektral ivme katsayısı
        dt   : Periyot adımı (s)

    Döndürür:
        list: ETABS tablo formatında [name, T, Saed, ...]
    """
    T_B = (sd1 / sds) / 3
    T_A = (0.2 * T_B) / 3
    T_L = 3.0

    period = np.arange(0, T_L, dt)
    values = []

    for T in period:
        if 0 <= T <= T_A:
            saed = (0.32 + 0.48 * (T / T_A)) * sds
        elif T_A < T <= T_B:
            saed = 0.8 * sds
        else:
            saed = (0.8 * sds * T_B) / T

        values.extend([
            _to_etabs_str(name),
            _to_etabs_str(T),
            _to_etabs_str(saed)
        ])

    return values


# ==============================================================================
# ETABS'A SPEKTRUM TANIMLAMA
# ==============================================================================

def define_response_spectra(SapModel, rq_info, seismic=None):
    """
    Yatay ve düşey tepki spektrumlarını ETABS'a tanımlar.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        rq_info  : define_all_seismic_loads'dan dönen spektrum bilgisi
        seismic  : Deprem parametreleri. None ise config'den alınır.
    """
    s       = seismic if seismic is not None else SEISMIC
    headers = ("Name", "Period", "Value")

    print("Tepki spektrumları tanımlanıyor...")

    # Yatay spektrumlar (X ve Y yönleri)
    for key, info in rq_info.items():
        spectrum = compute_sae(
            info["Name"], s["Sds"], s["Sd1"],
            info["R"], info["D"], info["I"]
        )
        SapModel.DatabaseTables.SetTableForEditingArray(
            "Functions - Response Spectrum - User Defined",
            1, headers, 1, spectrum
        )
        SapModel.DatabaseTables.ApplyEditedTables("True")
        print(f"  Yatay spektrum tanımlandı: {info['Name']}")

    # Düşey spektrum
    v_spectrum = compute_saed("Vertical", s["Sds"], s["Sd1"])
    SapModel.DatabaseTables.SetTableForEditingArray(
        "Functions - Response Spectrum - User Defined",
        1, headers, 1, v_spectrum
    )
    SapModel.DatabaseTables.ApplyEditedTables("True")
    print("  Düşey spektrum tanımlandı: Vertical")

    return rq_info


def define_response_spectrum_cases(SapModel, rq_info):
    """
    ETABS'ta tepki spektrumu analiz durumlarını oluşturur.
    ERx, ERy (yatay) ve ERz (düşey) durumları eklenir.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        rq_info  : Spektrum bilgisi sözlüğü

    Döndürür:
        list: ["ERx", "ERy", "ERz"]
    """
    cases = [
        ("ERx", "U1", rq_info[0]["Name"]),
        ("ERy", "U2", rq_info[1]["Name"]),
        ("ERz", "U3", "Vertical"),
    ]

    print("Tepki spektrumu analiz durumları oluşturuluyor...")
    for case_name, direction, spectrum_name in cases:
        SapModel.LoadCases.ResponseSpectrum.SetCase(case_name)
        SapModel.LoadCases.ResponseSpectrum.SetLoads(
            case_name, 1,
            (direction,),
            (spectrum_name,),
            (9806.65,),
            ('Global',),
            (0.0,)
        )
        print(f"  {case_name} ({direction}) → {spectrum_name}")

    spect_cases = [c[0] for c in cases]
    return spect_cases

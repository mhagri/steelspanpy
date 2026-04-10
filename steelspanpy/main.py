# -*- coding: utf-8 -*-
"""
main.py
-------
Ana akış dosyası. Tüm modülleri bir araya getirir ve
ETABS modelini sırayla oluşturur.

Kullanım:
    python main.py
"""

from .config import GEOMETRY, UNITS, BRACE, MID_COLUMNS
from .geometry import generate_roof_points, get_grid_config
from .sections import define_materials, define_all_sections
from .loads import setup_load_patterns, setup_mass_source, setup_all_combinations
from .seismic import (define_all_seismic_loads, define_response_spectra,
                     define_response_spectrum_cases)
from .elements import (create_all_frames, create_mid_columns,
                      create_all_vertical_braces, create_all_mid_braces,
                      create_all_vertical_stability, create_roof_braces)
from .etabs_connect import (setup_model_path, connect_to_etabs,
                            initialize_model, run_and_save)


def main():
    print("=" * 55)
    print("       SteelSpanPy — ETABS Model Oluşturucu")
    print("=" * 55)

    # ------------------------------------------------------------------
    # 1. DOSYA YOLU
    # ------------------------------------------------------------------
    print("\n[1/8] Dosya yolu ayarlanıyor...")
    model_path = setup_model_path()

    # ------------------------------------------------------------------
    # 2. ETABS BAĞLANTISI
    # ------------------------------------------------------------------
    print("\n[2/8] ETABS'a bağlanılıyor...")
    etabs_obj, SapModel = connect_to_etabs(attach=False, program_path=None)

    # ------------------------------------------------------------------
    # 3. MODEL BAŞLATMA
    # ------------------------------------------------------------------
    print("\n[3/8] Model başlatılıyor...")
    grid_config = get_grid_config()
    initialize_model(SapModel, UNITS, grid_config)

    # ------------------------------------------------------------------
    # 4. YÜK DESENLERİ VE DEPREM
    # ------------------------------------------------------------------
    print("\n[4/8] Yükler ve deprem tanımlanıyor...")
    groups = setup_load_patterns(SapModel)
    setup_mass_source(SapModel, groups)

    rq_info = define_all_seismic_loads(
        SapModel, groups["quake"], grid_config
    )
    define_response_spectra(SapModel, rq_info)
    spect_cases = define_response_spectrum_cases(SapModel, rq_info)

    # ------------------------------------------------------------------
    # 5. YÜK KOMBİNASYONLARI
    # ------------------------------------------------------------------
    print("\n[5/8] Yük kombinasyonları oluşturuluyor...")
    setup_all_combinations(SapModel, groups, spect_cases)

    # ------------------------------------------------------------------
    # 6. MALZEME VE KESİTLER
    # ------------------------------------------------------------------
    print("\n[6/8] Malzeme ve kesitler tanımlanıyor...")
    define_materials(SapModel)
    define_all_sections(SapModel)

    # ------------------------------------------------------------------
    # 7. GEOMETRİ VE YAPISAL ELEMANLAR
    # ------------------------------------------------------------------
    print("\n[7/8] Yapısal elemanlar oluşturuluyor...")

    # Çatı noktaları
    points = generate_roof_points()
    p0, p1, p2, p3, p4 = points

    # Ana çerçeveler (kolon + kiriş)
    create_all_frames(SapModel, points)

    # Düşey çaprazlar
    create_all_vertical_braces(SapModel, BRACE["story_heights"])

    # Orta kolonlar
    mid_col_points = []
    if MID_COLUMNS["enabled"]:
        mid_col_points = create_mid_columns(SapModel, p1, p2, p3)
        create_all_mid_braces(SapModel, mid_col_points)

    # Düşey stabilite
    create_all_vertical_stability(SapModel, BRACE["story_heights"])

    # Çatı çaprazları
    create_roof_braces(SapModel, p1, p2, p3, mid_col_points)

    # ------------------------------------------------------------------
    # 8. ANALİZ VE KAYDET
    # ------------------------------------------------------------------
    print("\n[8/8] Analiz ve kayıt...")
    run_and_save(SapModel, model_path)

    print("\n" + "=" * 55)
    print("  Model başarıyla oluşturuldu!")
    print(f"  Konum: {model_path}")
    print("=" * 55)


if __name__ == "__main__":
    main()

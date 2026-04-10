# -*- coding: utf-8 -*-
"""
sections.py
-----------
Kesit ve malzeme tanımlama işlemleri.
ETABS'a profil ve malzeme eklemek için kullanılan fonksiyonlar burada tanımlanır.
"""

from config import SECTIONS, STEEL_MATERIALS


# ==============================================================================
# MALZEME TANIMLAMA
# ==============================================================================

def define_materials(SapModel, materials=None):
    """
    Çelik malzemeleri ETABS'a tanımlar.

    Parametreler:
        SapModel  : ETABS SapModel nesnesi
        materials : Malzeme isimlerinin listesi. None ise config'den alınır.
    """
    mat_list = materials if materials is not None else STEEL_MATERIALS

    for mat in mat_list:
        SapModel.PropMaterial.AddMaterial(
            "NAME", 1, "Europe", "EN 1993-1-1 per EN 10025-2", mat
        )

    print(f"  {len(mat_list)} malzeme tanımlandı: {', '.join(mat_list)}")


# ==============================================================================
# KESİT TANIMLAMA
# ==============================================================================

def define_section(SapModel, section_type, section_name, material):
    """
    Tek bir kesiti ETABS'a tanımlar.

    Parametreler:
        SapModel     : ETABS SapModel nesnesi
        section_type : Kesit tipi → "I", "CHS" veya "RHS"
        section_name : Kesit ismi → örn. "HE400A", "CHS139.9X5"
        material     : Malzeme ismi → örn. "S275"
    """
    if section_type == "I":
        # Hadde profil — ArcelorMittal kütüphanesinden içe aktar
        SapModel.PropFrame.ImportProp(
            section_name, material, "ArcelorMittal_Europe.xml", section_name
        )

    elif section_type == "CHS":
        # Yuvarlak içi boş profil
        # İsim formatı: CHS{dış çap}X{et kalınlığı} → örn. CHS139.9X5
        dims = section_name.replace("CHS", "").split("X")
        outer_diameter    = float(dims[0])
        wall_thickness    = float(dims[1])
        SapModel.PropFrame.SetPipe(
            section_name, material, outer_diameter, wall_thickness
        )

    elif section_type == "RHS":
        # Dikdörtgen içi boş profil
        # İsim formatı: RHS{genişlik}X{yükseklik} → örn. RHS100X50
        dims = section_name.replace("RHS", "").split("X")
        width  = float(dims[0])
        height = float(dims[1])
        SapModel.PropFrame.SetTube(
            section_name, material, width, height
        )

    else:
        raise ValueError(
            f"Tanımsız kesit tipi: '{section_type}'. "
            f"Geçerli tipler: 'I', 'CHS', 'RHS'"
        )


def define_all_sections(SapModel, sections=None):
    """
    config.py'daki tüm kesitleri ETABS'a tanımlar.

    Parametreler:
        SapModel : ETABS SapModel nesnesi
        sections : Kesit sözlüğü. None ise config'den alınır.
                   Format: {"isim": [tip, kesit_adı, malzeme], ...}
    """
    sec_dict = sections if sections is not None else SECTIONS

    for role, (sec_type, sec_name, material) in sec_dict.items():
        define_section(SapModel, sec_type, sec_name, material)
        print(f"  [{role:12s}] {sec_name} ({material}) tanımlandı")


# ==============================================================================
# KESİT BİLGİSİ SORGULAMA
# ==============================================================================

def get_section_name(role, sections=None):
    """
    Belirli bir rol için kesit adını döndürür.

    Parametreler:
        role     : Kesit rolü → "column", "beam", "brace_v" vb.
        sections : Kesit sözlüğü. None ise config'den alınır.

    Döndürür:
        str: Kesit ismi → örn. "HE400A"

    Örnek:
        get_section_name("column")  →  "HE400A"
    """
    sec_dict = sections if sections is not None else SECTIONS

    if role not in sec_dict:
        raise KeyError(
            f"Tanımsız kesit rolü: '{role}'. "
            f"Geçerli roller: {list(sec_dict.keys())}"
        )

    return sec_dict[role][1]


def get_section_info(role, sections=None):
    """
    Belirli bir rol için [tip, isim, malzeme] listesini döndürür.

    Parametreler:
        role     : Kesit rolü → "column", "beam" vb.
        sections : Kesit sözlüğü. None ise config'den alınır.

    Döndürür:
        list: [tip, isim, malzeme] → örn. ["I", "HE400A", "S275"]
    """
    sec_dict = sections if sections is not None else SECTIONS

    if role not in sec_dict:
        raise KeyError(
            f"Tanımsız kesit rolü: '{role}'. "
            f"Geçerli roller: {list(sec_dict.keys())}"
        )

    return sec_dict[role]

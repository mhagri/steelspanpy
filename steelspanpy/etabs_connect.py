# -*- coding: utf-8 -*-
"""
etabs_connect.py
----------------
ETABS bağlantısı, model başlatma ve dosya yönetimi işlemleri.
"""

import os
import sys
import comtypes.client


# ==============================================================================
# DOSYA YOLU AYARLAMA
# ==============================================================================

def setup_model_path(filename=None):
    """
    Model dosyasının kaydedileceği yolu kullanıcıdan alır.
    Klasör yoksa otomatik oluşturur.
    """
    if filename is None:
        filename = input("Dosya adı girin: ").strip()
        if not filename:
            print("Hata: Dosya adı boş olamaz.")
            sys.exit(-1)

    # Kayıt klasörünü sor
    print(f"\nModel '{filename}.edb' olarak kaydedilecek.")
    save_dir = input("Kayıt klasörünü girin (boş bırakırsanız masaüstü kullanılır): ").strip()

    if not save_dir:
        # Masaüstünü otomatik bul
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "OneDrive", "Masaüstü"),
            os.path.join(home, "OneDrive", "Desktop"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Masaüstü"),
        ]
        save_dir = next((p for p in candidates if os.path.exists(p)), home)

    model_dir = os.path.join(save_dir, filename)

    if not os.path.exists(model_dir):
        try:
            os.makedirs(model_dir)
            print(f"  Klasör oluşturuldu: {model_dir}")
        except OSError as e:
            print(f"Hata: Klasör oluşturulamadı → {e}")
            sys.exit(-1)

    model_path = os.path.join(model_dir, f"{filename}.edb")
    print(f"  Model yolu: {model_path}")
    return model_path


# ==============================================================================
# ETABS BAĞLANTISI
# ==============================================================================

def connect_to_etabs(attach=False, program_path=None):
    """
    ETABS'a bağlanır veya yeni bir oturum başlatır.

    Parametreler:
        attach       : True → çalışan ETABS'a bağlan
                       False → yeni ETABS oturumu aç
        program_path : ETABS.exe tam yolu. None ise en son sürüm kullanılır.
                       Yalnızca attach=False olduğunda geçerlidir.

    Döndürür:
        ETABS nesne çifti: (myETABSObject, SapModel)
    """
    try:
        helper = comtypes.client.CreateObject("CSiAPIv1.Helper")
        helper = helper.QueryInterface(comtypes.gen.CSiAPIv1.cHelper)
    except Exception as e:
        print(f"Hata: ETABS API yardımcısı oluşturulamadı → {e}")
        sys.exit(-1)

    if attach:
        # Çalışan ETABS oturumuna bağlan
        try:
            etabs_obj = helper.GetObject("CSI.ETABS.API.ETABSObject")
            print("  Çalışan ETABS oturumuna bağlanıldı.")
        except (OSError, comtypes.COMError):
            print("Hata: Çalışan bir ETABS oturumu bulunamadı.")
            sys.exit(-1)
    else:
        # Yeni ETABS oturumu aç
        if program_path:
            try:
                etabs_obj = helper.CreateObject(program_path)
                print(f"  ETABS açıldı: {program_path}")
            except (OSError, comtypes.COMError):
                print(f"Hata: ETABS şu yoldan açılamadı → {program_path}")
                sys.exit(-1)
        else:
            try:
                etabs_obj = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
                print("  ETABS en son sürüm ile açıldı.")
            except (OSError, comtypes.COMError):
                print("Hata: ETABS başlatılamadı. Kurulu olduğundan emin olun.")
                sys.exit(-1)

    # Uygulamayı başlat
    etabs_obj.ApplicationStart()
    sap_model = etabs_obj.SapModel
    print("  ETABS başarıyla başlatıldı.")

    return etabs_obj, sap_model


# ==============================================================================
# MODEL BAŞLATMA
# ==============================================================================

def initialize_model(SapModel, units, grid_config):
    """
    Yeni bir ETABS modeli başlatır ve grid yapısını oluşturur.

    Parametreler:
        SapModel    : ETABS SapModel nesnesi
        units       : Birim sistemi (örn. 5 = kN-mm)
        grid_config : get_grid_config()'dan dönen sözlük
    """
    SapModel.InitializeNewModel(units)

    SapModel.File.NewGridOnly(
        grid_config["NumberStorys"],
        grid_config["TypicalStoryHeight"],
        grid_config["BottomStoryHeight"],
        grid_config["NumberLinesX"],
        grid_config["NumberLinesY"],
        grid_config["SpacingX"],
        grid_config["SpacingY"],
    )
    print("  Model başlatıldı ve grid oluşturuldu.")


# ==============================================================================
# MODEL KAYDETME VE ANALIZ
# ==============================================================================

def run_and_save(SapModel, model_path):
    """
    Görünümü yeniler, analizi çalıştırır ve modeli kaydeder.

    Parametreler:
        SapModel   : ETABS SapModel nesnesi
        model_path : Kaydedilecek dosyanın tam yolu
    """
    print("Görünüm yenileniyor...")
    SapModel.View.RefreshView(0, False)

    print("Analiz çalıştırılıyor...")
    SapModel.Analyze.RunAnalysis()

    print(f"Model kaydediliyor → {model_path}")
    SapModel.File.Save(model_path)
    print("  Model başarıyla kaydedildi.")


def save_model(SapModel, model_path):
    """
    Modeli kaydeder (analiz çalıştırmadan).

    Parametreler:
        SapModel   : ETABS SapModel nesnesi
        model_path : Kaydedilecek dosyanın tam yolu
    """
    SapModel.File.Save(model_path)
    print(f"  Model kaydedildi → {model_path}")


# ==============================================================================
# ETABS KAPATMA
# ==============================================================================

def close_etabs(etabs_obj, save=False):
    """
    ETABS oturumunu kapatır.

    Parametreler:
        etabs_obj : ETABS ana nesnesi
        save      : True → kapatmadan önce kaydet
    """
    etabs_obj.ApplicationExit(save)
    print("  ETABS kapatıldı.")

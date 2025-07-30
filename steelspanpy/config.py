# GİRDİLER-1
spoint = [0, 0]  #Başlangıç noktası
eUnits = 5  #5:kN-mm, 6:kN-m, 7:kgf-mm, 8:kgf-m 9:N-mm, 10:N-m, 11:Ton-mm, 12:Ton-m

l       = 63000     #Açıklık
h       = 17270     #Yükseklik
hm      = 3200      #Mahya yYüksekliği
axe     = 10         #Aks aralık sayısı
axel    = 9000      #Aks genişliği

story   = [0, h/3, 2*h/3, h]  #Çapraz için yükseklikler
#zero_per_group = 2
#brace_pattern = generate_pattern(zero_per_group,axe)
brace_pattern = [1, 0, 0, 1, 0, 0, 1, 0, 0, 1]  #Çapraz yerleşimi: bir dolu, iki boş vb.
brace_type = "X" #Düşey çapraz tipi X V K

maks_length=3500 #Çatı çaprazı maksimum genişlik

add_mid_columns = True  #Orta kolon ekle
full_span = True        #True:Full açıklığı böl, False:Çatı kirişleri ayrı ayrı böl
mid_col_div= 2          #Eklenecek orta kolon adedi
include_p2_column=False #Mahyaya kolon ekle
mid_brace_div=3         #Orta kolonlara çapraz ekle

# GIRDILER-2
Sds     = 1.571
Sd1     = 0.537
Soil    = "ZC"
Rx      = 8
Dx      = 3
Ry      = 5
Dy      = 2
I       = 1

Dead_load   = 1     #kN/m2
Snow_load   = 1     #kN/m2
Snow2_load  = 0.5   #kN/m2

# GİRDİLER-3
column      = ["I", "HE700A" , "S275"]
beam        = ["I", "HE500A" , "S275"]
brace_v     = ["CHS" , "CHS193.7X8", "S235"]
stability_v = ["CHS" , "CHS139.9X5", "S235"]
brace_r     = ["CHS" , "CHS88.9X5", "S235"]
stability_r = ["CHS" , "CHS88.9X4", "S235"]

# GIRDILER-4
LoadType = {
    "DL": 2,
    "S": 7,
    "S2":7,
    #"S3":7,
    "Wx": 6,
    "Wy": 6,
    #"W-x":6,
    #"W-y":6,
    # "R":4,
    #"T":10,
    # "Lr":11,
    "Ex": 5,
    "Ey": 5,
}

# """
# Load Patterns
# LoadPattern Type Enumeration
# LoadType={
#     "Dead":1,
#     "SuperDead":2,
#     "Live":3,
#     "ReduceLive":4,
#     "Quake":5,
#     "Wind":6,
#     "Snow":7,
#     "Other":8,
#     "Temperature":10,
#     "Rooflive":11,
#     "Notional":12,
#     "PatternLive":13,
#     "Construction":39,
#     "PrestressTransfer":59,
#     "PatternAuto":60,
#     "QuakeDrift":61,
#     }
# """

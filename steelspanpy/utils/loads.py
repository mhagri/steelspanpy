from .spectrum import Sae, Saed

def TCS2018(SapModel, name, sds, sd1, soil, r, d, i, Grid):
    xdir = 'Yes' if name == 'Ex' else 'No'
    ydir = 'Yes' if name == 'Ey' else 'No'

    top_story = Grid['Storys'][-1]  # Son katın adı (örneğin "Story5")

    funchead = [
        'Name', 'IsAuto',
        'XDir', 'XDirPlusE', 'XDirMinusE',
        'YDir', 'YDirPlusE', 'YDirMinusE',
        'EccRatio', 'TopStory', 'BotStory', 'OverStory',
        'OverDiaph', 'OverEcc', 'PeriodType', 'CtAndX',
        'UserT', 'Ss', 'S1', 'TL', 'SiteClass', 'R', 'D', 'I'
    ]

    values = [[
        name, 'No',
        xdir, 'No', 'No',
        ydir, 'No', 'No',
        '0,05', top_story, 'Base', '',
        '', '', 'Program Calculated', '0.08;0.75',
        '', f"{sds:.3f}".replace('.', ','), f"{sd1:.3f}".replace('.', ','), '6', soil,
        str(r), f"{d:.3f}".replace('.', ','), f"{i:.3f}".replace('.', ',')
    ]]

    SapModel.DatabaseTables.SetTableForEditingArray(
        "Load Pattern Definitions - Auto Seismic - TSC 2018", 1, funchead, 1, values
    )
    
    SapModel.DatabaseTables.ApplyEditedTables("True")

def rename_default_patterns(SapModel):
    SapModel.LoadPatterns.ChangeName("Dead", "SW")
    SapModel.LoadCases.ChangeName("Dead", "SW")
    SapModel.LoadPatterns.ChangeName("Live", "LL")
    SapModel.LoadCases.ChangeName("Live", "LL")


def classify_load_patterns(SapModel, LoadType):
    dead, snow, wind, quake, temp, roof, live = ["SW"], [], [], [], [], [], ["LL"]

    for key, value in LoadType.items():
        SapModel.LoadPatterns.Add(key, value)
        if value == 7:
            snow.append(key)
        elif value == 6:
            wind.append(key)
        elif value == 5:
            quake.append(key)
        elif value == 10:
            temp.append(key)
        elif value in [4, 11]:
            roof.append(key)
        elif value in [1, 2]:
            dead.append(key)
        elif value == 3:
            live.append(key)

    roof = snow + roof
    return dead, snow, wind, quake, temp, roof, live

def set_mass_source(SapModel, dead, snow, live):
    MassSrc = dict(zip(snow + dead + live,
                       [0.8] * len(snow) + [1.0] * len(dead) + [1.0] * len(live)))
    SapModel.PropMaterial.SetMassSource(2, len(MassSrc), list(MassSrc.keys()), list(MassSrc.values()))


def create_H_spectrum_functions(SapModel, Direction, Sds, Sd1, R, D, I):

    Name = f"R{R}D{D}_{Direction}"
    headers = ("Name", "Period", "Value")

    spectrum_data = Sae(Name, Sds, Sd1, R, D, I)
    SapModel.DatabaseTables.SetTableForEditingArray(
        "Functions - Response Spectrum - User Defined", 1, headers, 1, spectrum_data
    )
    SapModel.DatabaseTables.ApplyEditedTables("True")
    SapModel.LoadCases.ResponseSpectrum.SetCase(f"ER{Direction}")
    
    if Direction == "X":
        Load_Name = "U1"
    elif Direction == "Y":
        Load_Name = "U2"
                                        
    SapModel.LoadCases.ResponseSpectrum.SetLoads(f"ER{Direction}", 1, (Load_Name,), (Name,), (9806.65,), ('Global',), (0.0,))

def create_V_spectrum_functions(SapModel, Sds, Sd1):
    headers = ("Name", "Period", "Value")
    spectrum_data = Saed("Vertical", Sds, Sd1)
    SapModel.DatabaseTables.SetTableForEditingArray("Functions - Response Spectrum - User Defined", 1, headers, 1, spectrum_data)
    SapModel.DatabaseTables.ApplyEditedTables("True")
    SapModel.LoadCases.ResponseSpectrum.SetCase("ERz")
    SapModel.LoadCases.ResponseSpectrum.SetLoads("ERz", 1, ('U3',), ("Vertical",), (9806.65,), ('Global',), (0.0,))




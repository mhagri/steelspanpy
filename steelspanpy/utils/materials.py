class MaterialManager:
    def __init__(self, SapModel):
        self.SapModel = SapModel

    def add_steel_material(self, name="S355"):
        self.SapModel.PropMaterial.AddMaterial(
            name, 1, "Europe", "EN 1993-1-1 per EN 10025-2", name
        )

    def add_concrete_material(self, name="C30"):
        self.SapModel.PropMaterial.AddMaterial(
            name, 2, "Europe", "EN 1992-1-1 per EN 206-1", name
        )

    def define_steel_material(self, name="S355", fy=355e6, fu=510e6,
                               E=2.1e11, poisson=0.3, density=7850):
        self.SapModel.PropMaterial.SetMaterial(name, 1)  # Steel
        self.SapModel.PropMaterial.SetMPIsotropic(name, E, poisson, density)
        self.SapModel.PropMaterial.SetSteelYieldStress(name, fy)
        self.SapModel.PropMaterial.SetSteelUltimateStress(name, fu)

    def define_concrete_material(self, name="C30", fc=30e6,
                                 E=30e9, poisson=0.2, density=2500):
        self.SapModel.PropMaterial.SetMaterial(name, 2)  # Concrete
        self.SapModel.PropMaterial.SetMPIsotropic(name, E, poisson, density)
        self.SapModel.PropMaterial.SetOConcrete(
            name, fc, True, fc * 1.5, fc * 1.2, 0.002, 0.0035, 0
        )

    def list_materials(self):
        # Opsiyonel: tanımlı tüm malzemeleri döndürebilir
        table_key = "Materials"
        self.SapModel.DatabaseTables.SetOutputTableKey(table_key)
        success, table_exists, field_keys, data = self.SapModel.DatabaseTables.GetTableForDisplayArray()
        if success and table_exists:
            return data
        return []

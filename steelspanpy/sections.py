class SectionLibrary:
    def __init__(self, SapModel, xml_path="ArcelorMittal_Europe.xml"):
        self.SapModel = SapModel
        self.xml_path = xml_path

    def define(self, section_type, section_name, material):
        if section_type == "I":
            self.import_i_section(section_name, material)
        elif section_type == "CHS":
            self.set_pipe(section_name, material)
        elif section_type == "RHS":
            self.set_tube(section_name, material)
        else:
            print(f"Uyarı: '{section_type}' tipi tanınmadı.")

    def import_i_section(self, name, material):
        try:
            self.SapModel.PropFrame.ImportProp(name, material, self.xml_path, name)
        except:
            print(f"{name} zaten tanımlı olabilir.")

    def set_pipe(self, name, material):
        dims = name.replace("CHS", "").split("X")
        d, t = map(float, dims)
        self.SapModel.PropFrame.SetPipe(name, material, d, t)

    def set_tube(self, name, material):
        dims = name.replace("RHS", "").split("X")
        b, h = map(float, dims)
        self.SapModel.PropFrame.SetTube(name, material, b, h)

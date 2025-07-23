def interpolate_z(x, p1, p2, p3):
        if x <= p2[0]:
            ratio = (x - p1[0]) / (p2[0] - p1[0]) if p2[0] != p1[0] else 0
            return p1[1] + ratio * (p2[1] - p1[1])
        else:
            ratio = (x - p2[0]) / (p3[0] - p2[0]) if p3[0] != p2[0] else 0
            return p2[1] + ratio * (p3[1] - p2[1])


def split_number(start, end, num):
    dx = (end[0] - start[0]) / (num+1)
    dz = (end[1] - start[1]) / (num+1)
    points = [[start[0] + i * dx, start[1] + i * dz] for i in range(num + 2)]
    return points


def split_space(start, end, maks):
    length = ((end[0] - start[0])**2 + (end[1] - start[1])**2) ** 0.5
    segments = round(length / maks)
    dx = (end[0] - start[0]) / segments
    dz = (end[1] - start[1]) / segments
    points = [[start[0] + i * dx, start[1] + i * dz] for i in range(segments + 1)]
    return points


def generate_pattern(zero_per_group, length):
    result = []
    while len(result) < length:
        result.append(1)
        for _ in range(zero_per_group):
            if len(result) < length:
                result.append(0)
    return result


def generate_roof_points(spoint, l, h, hm):
    """
    Verilen başlangıç noktasından hareketle p0-p4 noktalarını oluşturur.
    p0: alt sol, p1: sol kolon tepesi, p2: mahya, p3: sağ kolon tepesi, p4: alt sağ
    """
    p0 = spoint
    p1 = [spoint[0], spoint[1] + h]
    p2 = [spoint[0] + l / 2, spoint[1] + h + hm]
    p3 = [spoint[0] + l, spoint[1] + h]
    p4 = [spoint[0] + l, spoint[1]]
    return [p0, p1, p2, p3, p4]


def section_define(SapModel, type_of_section, section, material):
    if type_of_section == "I":
        SapModel.PropFrame.ImportProp(section, material, "ArcelorMittal_Europe.xml", section)
    elif type_of_section == "CHS":
        dimentions = section.replace("CHS", "").split("X")
        SapModel.PropFrame.SetPipe(section, material, float(dimentions[0]), float(dimentions[1]))
    elif type_of_section == "RHS":
        dimentions = section.replace("RHS", "").split("X")
        SapModel.PropFrame.SetTube(section, material, float(dimentions[0]), float(dimentions[1]))        
    SapModel.FrameObj.SetSection("Name", section)

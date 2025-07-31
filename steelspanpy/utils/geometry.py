from .points import interpolate_z
from .points import split_number
from .points import split_space

def Grid(SapModel, hm, h, axe, l, axel):
    # Axes
    Grid = {"NumberStorys": 2,
        "TypicalStoryHeight": hm / 1000,
        "BottomStoryHeight": h / 1000,
        "NumberLinesX": 3,
        "NumberLinesY": axe + 1,
        "SpacingX": l / 2000,
        "SpacingY": axel / 1000,
        }
    
    # New GridOnly Model
    SapModel.File.NewGridOnly(Grid["NumberStorys"], Grid["TypicalStoryHeight"], Grid["BottomStoryHeight"],
                                Grid["NumberLinesX"], Grid["NumberLinesY"], Grid["SpacingX"], Grid["SpacingY"])


def first_hall(SapModel, points, l, h, hm, y=0, name_prefix="Name", column=None, beam=None):
    """
    Ana çerçeve elemanlarını oluşturur ve kolon ile kirişleri gruplara atar.
    """
    if column is None or beam is None:
        raise ValueError("Kolon ve Kiriş parametreleri verilmelidir.")
        
    for i in range(len(points) - 1):
        start = points[i]
        end = points[i + 1]
        
        obj_name = f"{name_prefix*4+i+1}"  # İsmi sen ver
        
        # Çubuğu oluştur
        if i == 0 or i == 3:
            SapModel.FrameObj.AddByCoord(start[0], y, start[1], end[0], y, end[1], obj_name, column[1])
            SapModel.FrameObj.SetLoadDistributed(obj_name, "Wx", 1, 7, 0, 1, 0.008, 0.008)
            
        elif i == 1 or i == 2:
            SapModel.FrameObj.AddByCoord(start[0], y, start[1], end[0], y, end[1], obj_name, beam[1])


def mid_columns(SapModel, p1, p2, p3, num_divisions, include_p2_column, full_span, y=0, axe=None, axel=None, column=None):
    
    """ Aks  arasına kolon ataması yapar """
    
    if full_span:
        # full span: p1-p3 arası eşit bölünsün, z interpolasyonu segmentlere göre yapılsın
        
        dx = (p3[0] - p1[0]) / (num_divisions + 1)
        points = []
        for i in range(1, num_divisions + 1):  # Dikkat! i=1'den başlayıp i=num_divisions dahil bitiriyoruz
            x = p1[0] + i * dx
            z = interpolate_z(x,)
            points.append([x, z])
        
        if not include_p2_column:
            points = [pt for pt in points if abs(pt[0] - p2[0]) > 1e-6]

    else:
        # eski yöntem: p1-p2 ve p2-p3 ayrı ayrı eşit bölünsün
        cols_p1_p2 = split_number(p1, p2, num_divisions)
        cols_p2_p3 = split_number(p2, p3, num_divisions)

        cols_p1_p2_inner = cols_p1_p2[1:-1]
        cols_p2_p3_inner = cols_p2_p3[1:-1]
        cols_p2 = [p2] if include_p2_column else []

        points = cols_p1_p2_inner + cols_p2 + cols_p2_p3_inner

    # kolonları oluştur
    for i in range(axe + 1):
        y_pos = i * axel
        for pt in points:
            x, z = pt
            SapModel.FrameObj.AddByCoord(x, y_pos, 0, x, y_pos, z, f"Col_{int(x)}_{y_pos}", column[1])

    return points


def mid_braces(SapModel, all_columns, num_divisions, y1=0, brace_type="X", axe=None, axel=None):
    """ Orta kolonların arasına çapraz oluşturur"""
    
    for pt in all_columns:
        x, z_top = pt
        story_points = split_number([x, 0], [x, z_top], num_divisions)
        story_heights = [pt[1] for pt in story_points]

        vertical_braces(SapModel, axel, story_heights,  y1=y1, x_coords=[x])
        vertical_stability(SapModel, axe, axel, story_heights, x_coords=[x])

                
def vertical_braces(SapModel, axelength, story_heights, x_coords, brace_type="X", y1=0, brace_v=None):
    y2 = y1 + axelength  # Bir sonraki aks mesafesi
    for x in x_coords:
        for j in range(len(story_heights) - 1):
            z1 = story_heights[j]
            z2 = story_heights[j + 1]
            
            if brace_type == "X":
                SapModel.FrameObj.AddByCoord(x, y1, z1, x, y2, z2, f"X_{j}_x{x}", brace_v[1])
                SapModel.FrameObj.AddByCoord(x, y2, z1, x, y1, z2, f"X_{j}_x{x}_2", brace_v[1])

            elif brace_type == "V":
                mid_y = (y1 + y2) / 2
                SapModel.FrameObj.AddByCoord(x, y1, z1, x, mid_y, z2, f"V_{j}_x{x}_1", brace_v[1])
                SapModel.FrameObj.AddByCoord(x, y2, z1, x, mid_y, z2, f"V_{j}_x{x}_2", brace_v[1])

            elif brace_type == "K":
                mid_z = (z1 + z2) / 2
                # Bu kod tüm katlara K çaprazı oluşturur
                SapModel.FrameObj.AddByCoord(x, y1, z1, x, y2, mid_z, f"K_{j}_1", brace_v[1])
                SapModel.FrameObj.AddByCoord(x, y2, mid_z, x, y1, z2, f"K_{j}_2", brace_v[1])
            
            else:
                print(f"Tanımsız çapraz tipi: {brace_type}")


def vertical_stability(SapModel, axes, axelength, story_heights, x_coords, stability_v=None, stability_r=None):
    grid_y = [i * axelength for i in range(axes+1)]

    for x in x_coords:
        for i in range(len(grid_y) - 1):
            for j in range(len(story_heights)-1):
                y1, y2 = grid_y[i], grid_y[i + 1]
                z1, z2 = story_heights[j], story_heights[j+1]
                if z1 == 0:
                    continue
                SapModel.FrameObj.AddByCoord(x, y1, z1, x, y2, z1, f"X_{i}_{j}_x{x}", stability_v[1])
                SapModel.FrameObj.AddByCoord(x, y1, z2, x, y2, z2, f"X_{i}_{j}_x{x}_2", stability_v[1])            
                iReleases = [False, False, False, False, True, True]
                jReleases = [False, False, False, False, True, True]
                iValues = [0] * 6
                jValues = [0] * 6
                SapModel.FrameObj.SetReleases(f"X_{i}_{j}_x{x}_2", iReleases, jReleases, iValues, jValues)
                
def roof_braces(SapModel, p1, p2, p3, axe, axel, brace_pattern, maks_length, brace_r=None, stability_r=None):
    seg1 = split_space(p1, p2, maks_length)
    seg2 = split_space(p2, p3, maks_length)

    for i in range(axe):
        y1 = i * axel
        y2 = (i + 1) * axel
        pattern = brace_pattern[i % len(brace_pattern)]

        if pattern == 1:
            # Her noktaya X çapraz (seg1 + seg2)
            all_points = seg1 + seg2[1:]
            for j in range(len(all_points) - 1):
                pt1 = all_points[j]
                pt2 = all_points[j + 1]
                SapModel.FrameObj.AddByCoord(pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RBR_{i}_{j}_X1", brace_r[1])
                SapModel.FrameObj.AddByCoord(pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RBR_{i}_{j}_X2", brace_r[1])

        else:
            # --- SEGMENT 1 (p1 → p2) ---
            pt1 = seg1[0]
            pt2 = seg1[1]
            SapModel.FrameObj.AddByCoord(pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RBR_{i}_s1_start_X1", brace_r[1])
            SapModel.FrameObj.AddByCoord(pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RBR_{i}_s1_start_X2", brace_r[1])

            for j, pt in enumerate(seg1[1:-1], start=1):
                SapModel.FrameObj.AddByCoord(pt[0], y1, pt[1], pt[0], y2, pt[1], f"RBR_{i}_s1_{j}_vert", stability_r[1])

            pt1 = seg1[-2]
            pt2 = seg1[-1]
            SapModel.FrameObj.AddByCoord(pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RBR_{i}_s1_end_X1", brace_r[1])
            SapModel.FrameObj.AddByCoord(pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RBR_{i}_s1_end_X2", brace_r[1])

            # --- SEGMENT 2 (p2 → p3) ---
            pt1 = seg2[0]
            pt2 = seg2[1]
            SapModel.FrameObj.AddByCoord(pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RBR_{i}_s2_start_X1", brace_r[1])
            SapModel.FrameObj.AddByCoord(pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RBR_{i}_s2_start_X2", brace_r[1])

            for j, pt in enumerate(seg2[1:-1], start=1):
                SapModel.FrameObj.AddByCoord(pt[0], y1, pt[1], pt[0], y2, pt[1], f"RBR_{i}_s2_{j}_vert", stability_r[1])

            pt1 = seg2[-2]
            pt2 = seg2[-1]
            SapModel.FrameObj.AddByCoord(pt1[0], y1, pt1[1], pt2[0], y2, pt2[1], f"RBR_{i}_s2_end_X1", brace_r[1])
            SapModel.FrameObj.AddByCoord(pt2[0], y1, pt2[1], pt1[0], y2, pt1[1], f"RBR_{i}_s2_end_X2", brace_r[1])
 
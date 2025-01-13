import arcpy

#Environment
arcpy.env.overwriteOutput = True

versmalgrens = arcpy.GetParameterAsText(0) #Configure this input parameter datatype as: Feature Class, Feature Layer
versmaldgdb = arcpy.GetParameterAsText(1) #Configure this input parameter datatype as: Workspace
productsgdb = arcpy.GetParameterAsText(2) #Configure this input parameter datatype as: Workspace
arcpy.AddMessage(f"Starting CreateOpnameGrens script with:")
arcpy.AddMessage(f"Versmalgrens = {versmalgrens}")
arcpy.AddMessage(f"versmald.gdb = {versmaldgdb}")
arcpy.AddMessage(f"products.gdb = {productsgdb}")

def setupEmptyLayers(productsgdb):
    arcpy.AddMessage(f"Start setup of empty layers")
    crs_rd_nap = arcpy.SpatialReference(7415)
    dtb_object_vertices = arcpy.management.CreateFeatureclass(productsgdb,
                                                              "temp_all_dtb_object_vertices",
                                                              "POINT",
                                                              has_z="ENABLED",
                                                              spatial_reference=crs_rd_nap)
    dtb_buffer_total = arcpy.management.CreateFeatureclass(productsgdb,
                                                              "temp_total_buffers",
                                                              "POLYGON",
                                                              has_z="ENABLED",
                                                              spatial_reference=crs_rd_nap)
    arcpy.management.AddFields(dtb_object_vertices, [
                                                    ["DTB_ID", "TEXT"],
                                                    ["Z_VALUE", "DOUBLE"]
                                                    ])
    arcpy.management.AddFields(dtb_buffer_total, [
                                                    ["DTB_ID", "TEXT"]
                                                    ])
    arcpy.AddMessage(f"Created empty feature classes with fields DTB_ID and Z_VALUE")
    iterateDTBlayers(dtb_object_vertices, dtb_buffer_total, versmaldgdb)
    
def iterateDTBlayers(dtb_object_vertices, dtb_buffer_total, versmaldgdb):
    versmald_layer_path = fr"{versmaldgdb}\DTB_DATA"
    arcpy.env.workspace = versmald_layer_path
    dtb_layerlist = arcpy.ListFeatureClasses()
    arcpy.AddMessage(f"Starting iterating DTB layers for: {dtb_layerlist}")
    
    for dtb_layer in dtb_layerlist:
        #dtb_layer_file = fr"{versmald_layer_path}\{dtb_layer}"
        arcpy.AddMessage(f"Start versmalling for: {dtb_layer}")
        layer_desc = arcpy.Describe(dtb_layer)
        if layer_desc.shapeType == "Polygon":
            arcpy.AddMessage("This is a polygon feature class.")
            processPolygonLayer(dtb_layer, versmalgrens, versmaldgdb)
        elif layer_desc.shapeType == "Polyline":
            arcpy.AddMessage("This is a polyline feature class.")
            processLineLayer(dtb_object_vertices, dtb_buffer_total, dtb_layer, versmalgrens)
        elif layer_desc.shapeType == "Point":
            arcpy.AddMessage("This is a point feature class.")
            processPointLayer(dtb_object_vertices, dtb_buffer_total, dtb_layer, versmalgrens)
        else:
            arcpy.AddMessage(f"Error: Unknown shape type")
    arcpy.AddMessage("Finished iterating all layers")
    finalizeObjects(dtb_object_vertices, dtb_buffer_total, versmaldgdb, productsgdb)

def processPointLayer(dtb_object_vertices, dtb_buffer_total, dtb_layer, versmalgrens):
    point_outside_grens = arcpy.management.SelectLayerByLocation(dtb_layer,
                                                            "INTERSECT",
                                                            versmalgrens,
                                                            None,
                                                            "NEW_SELECTION",
                                                            "INVERT")
    point_outside_grens_count = int(arcpy.management.GetCount(point_outside_grens)[0])
    if point_outside_grens_count > 0:
        arcpy.AddMessage("Features found outside the versmalgrens")
        arcpy.AddMessage("Append these points to the total dtb objects")
        arcpy.management.Append(point_outside_grens, dtb_object_vertices, "NO_TEST")
        arcpy.AddMessage("Create square shaped buffer")
        square_buffer = arcpy.analysis.GraphicBuffer(point_outside_grens, f"in_memory\\{dtb_layer}_buffer", 1, "SQUARE")
        arcpy.AddMessage("Append these buffer to the total buffers fc")
        arcpy.management.Append(square_buffer, dtb_buffer_total, "NO_TEST")
    else:
        arcpy.AddMessage("No features outside the versmalgrens found")

def processLineLayer(dtb_object_vertices, dtb_buffer_total, dtb_layer, versmalgrens):
    line_outside_grens = arcpy.management.SelectLayerByLocation(dtb_layer,
                                                            "INTERSECT",
                                                            versmalgrens,
                                                            None,
                                                            "NEW_SELECTION",
                                                            "INVERT")
    line_outside_grens_count = int(arcpy.management.GetCount(line_outside_grens)[0])
    if line_outside_grens_count > 0:
        arcpy.AddMessage("Features found outside the versmalgrens")
        arcpy.AddMessage("Convert line to feature vertices")
        line_vertices = arcpy.management.FeatureVerticesToPoints(line_outside_grens, f"in_memory\\{dtb_layer}_lv")
        arcpy.AddMessage("Append these line vertices to the total dtb objects")
        arcpy.management.Append(line_vertices, dtb_object_vertices, "NO_TEST")
        arcpy.AddMessage("Create square shaped buffer")
        square_buffer = arcpy.analysis.GraphicBuffer(line_outside_grens, f"in_memory\\{dtb_layer}_buffer", 1, "SQUARE")
        arcpy.AddMessage("Append these buffers to the total buffer fc")
        arcpy.management.Append(square_buffer, dtb_buffer_total, "NO_TEST")
    else:
        arcpy.AddMessage("No features outside the versmalgrens found")
    
def processPolygonLayer(dtb_layer, versmalgrens, versmaldgdb):
    polygon_outside_grens = arcpy.management.SelectLayerByLocation(dtb_layer,
                                                            "INTERSECT",
                                                            versmalgrens,
                                                            None,
                                                            "NEW_SELECTION",
                                                            "INVERT")
    polygon_outside_grens_count = int(arcpy.management.GetCount(polygon_outside_grens)[0])
    if polygon_outside_grens_count > 0:
        arcpy.AddMessage("Features found outside the versmalgrens")
        arcpy.AddMessage("Converting polygon to opnamegrens")
        polygon_to_line = arcpy.management.FeatureToLine(polygon_outside_grens, f"in_memory\\{dtb_layer}_tolines")
        arcpy.AddMessage("Removing DTB_ID and changing type to OpnameGrens 21117")
        arcpy.management.CalculateField(polygon_to_line, "DTB_ID", '""', "PYTHON3")
        arcpy.management.CalculateField(polygon_to_line, "TYPE", '21117', "PYTHON3")
        extra_opnamegrens = polygon_to_line
        dtb_scheiding_lijnen = fr"{versmaldgdb}\DTB_DATA\DTB_SCHEIDING_LIJNEN"
        arcpy.management.Append(extra_opnamegrens, dtb_scheiding_lijnen, "NO_TEST")
    else:
        arcpy.AddMessage("No features outside the versmalgrens found")

def finalizeObjects(dtb_object_vertices, dtb_buffer_total, versmaldgdb, productsgdb):
    arcpy.AddMessage("Starting finalizing G.I.N.-vlakken and opgnamegrenzen")
    arcpy.Delete_management("in_memory")
    arcpy.AddMessage("Dissolve overlapping square buffers")
    buffer_dissolve = arcpy.management.Dissolve(dtb_buffer_total, fr"in_memory\\bfv_dislv", multi_part="SINGLE_PART")
    arcpy.AddMessage("Dissolve overlapping square buffers")
    buffer_vertices = arcpy.management.FeatureVerticesToPoints(buffer_dissolve, f"in_memory\\total_bv")
    arcpy.AddMessage("Extracting Z-coordinate of dtb_object point and line vertices to field")
    arcpy.management.CalculateGeometryAttributes(dtb_object_vertices, [["Z_VALUE", "POINT_Z"]])
    arcpy.AddMessage("Joining Z-coordinate from closest DTB_OBJECT to closest buffer vertex")
    z_value_join = arcpy.analysis.SpatialJoin(buffer_vertices, 
                                              dtb_object_vertices,
                                              "in_memory\\bufvertsspz",
                                              match_option="CLOSEST",
                                              join_operation="JOIN_ONE_TO_ONE",
                                              join_type="KEEP_ALL")
    arcpy.AddMessage("Converting buffer vertices field to Z-coordinate")
    z_buffer_vertices = arcpy.ddd.FeatureTo3DByAttribute(z_value_join, "in_memory\\temp_z_buffer_vrt", "Z_VALUE")
    arcpy.AddMessage("Create lines from buffer vertices")
    buffer_vertice_to_line = arcpy.management.PointsToLine(z_buffer_vertices,
                                                           fr"{productsgdb}\temp_vertices_to_line",
                                                           Line_Field="ORIG_FID")
    arcpy.AddMessage("Create polygon from lines")
    buffer_line_to_polygon = arcpy.management.FeatureToPolygon(buffer_vertice_to_line, fr"{productsgdb}\temp_line_to_polygon")
    arcpy.management.ClearWorkspaceCache()
    arcpy.Delete_management("in_memory")
    
    #Resulting GIN vlakken
    dtb_gin_vlak = buffer_line_to_polygon
    arcpy.AddMessage("Adding and filling NIVEAU and TYPE to GIN vlakken")
    arcpy.management.AddFields(dtb_gin_vlak,
                               [['NIVEAU', "LONG"],
                                ['TYPE', "LONG"]])
    arcpy.management.CalculateField(dtb_gin_vlak, 'NIVEAU', 0, "PYTHON3")
    arcpy.management.CalculateField(dtb_gin_vlak, 'TYPE', 30337, "PYTHON3")
    arcpy.AddMessage("Appending GIN vlakken to DTB_GROND_VLAKKEN")
    grondvlakpath = fr"{versmaldgdb}\DTB_DATA\DTB_GROND_VLAKKEN"
    arcpy.management.Append(dtb_gin_vlak, grondvlakpath, "NO_TEST")
    
    #Resulting OG lijnen
    dtb_og_lijn = buffer_vertice_to_line
    arcpy.AddMessage("Adding and filling NIVEAU and TYPE to OG lijnen")
    arcpy.management.AddFields(dtb_og_lijn,
                               [['NIVEAU', "LONG"],
                                ['TYPE', "LONG"]])
    arcpy.management.CalculateField(dtb_og_lijn, 'NIVEAU', 0, "PYTHON3")
    arcpy.management.CalculateField(dtb_og_lijn, 'TYPE', 21117, "PYTHON3")
    arcpy.AddMessage("Appending OG lijnen to DTB_SCHEIDING_LIJNEN")
    scheidlijnpath = fr"{versmaldgdb}\DTB_DATA\DTB_SCHEIDING_LIJNEN"
    arcpy.management.Append(dtb_og_lijn, scheidlijnpath, "NO_TEST")

setupEmptyLayers(productsgdb)
import arcpy

#Environment
arcpy.env.overwriteOutput = True

versmalgrens = arcpy.GetParameterAsText(0) #Configure this input parameter datatype as: Feature Class, Feature Layer
uitsnedeAOI = arcpy.GetParameterAsText(1) #Configure this input parameter datatype as: Feature Class, Feature Layer
versmaldgdb = arcpy.GetParameterAsText(2) #Configure this input parameter datatype as: Workspace 
dtb_vlak_uitgebreid = arcpy.GetParameterAsText(3) #Configure this input parameter datatype as: Feature Layer
arcpy.AddMessage(f"Starting CreateOpnameGrens script with:")
arcpy.AddMessage(f"Versmalgrens = {versmalgrens}")
arcpy.AddMessage(f"AOI = {uitsnedeAOI}")
arcpy.AddMessage(f"versmald.gdb = {versmaldgdb}")
arcpy.AddMessage(f"dtb_vlak_uitgebreid = {dtb_vlak_uitgebreid}")

arcpy.env.workspace = fr"{versmaldgdb}\DTB_DATA"
scheiding_lijnen_file = fr"{versmaldgdb}\DTB_DATA\DTB_SCHEIDING_LIJNEN"
scheiding_lijnen_layer = "DTB_SCHEIDING_LIJNEN"

def checkCurrentOG(scheiding_lijnen_layer):
    arcpy.AddMessage(f"Checking for existing OpnameGrens features")
    og_features = arcpy.management.SelectLayerByAttribute(scheiding_lijnen_layer, 
                                            "NEW_SELECTION",
                                            '"TYPE" = 21117')
    og_features_count = int(arcpy.management.GetCount(og_features)[0])
    if og_features_count > 0:
        arcpy.AddMessage(f"Existing OpnameGrens features found")
        arcpy.management.DeleteRows(og_features)
        arcpy.AddMessage(f"Existing OpnameGrens features deleted")
    else:
        arcpy.AddMessage(f"No existing OpnameGrens features found")
    createNewOG(versmalgrens, dtb_vlak_uitgebreid, uitsnedeAOI, scheiding_lijnen_layer)
    
def createNewOG(versmalgrens, dtb_vlak_uitgebreid, uitsnedeAOI, scheiding_lijnen_layer):
    
    arcpy.AddMessage(f"Start creating new OpnameGrens")
    
    dtb_vlak_clip = arcpy.analysis.Clip(dtb_vlak_uitgebreid,
                                        versmalgrens,
                                        "in_memory\\dtb_vlak_clip")
    arcpy.AddMessage(f"Clip dtb_vlakken_uitgebreid on versmalgrens")
    
    versmalgrens_dtbvlak_spjoin = arcpy.analysis.SpatialJoin(dtb_vlak_clip,
                                                             versmalgrens,
                                                             "in_memory\\grens_dtbvlak_spjoin",
                                                             "JOIN_ONE_TO_MANY")
    arcpy.AddMessage(f"Spatial join dtb_vlakken_clip on versmalgrens")

    grens_dtbvlak_dissolve = arcpy.analysis.PairwiseDissolve(versmalgrens_dtbvlak_spjoin,
                                                             "in_memory\\grens_dtbvlak_dissolve",
                                                             multi_part="SINGLE_PART")
    arcpy.AddMessage(f"Dissolve versmalgrens_dtbvlak_dissolve")
    
    grens_vlak_to_line = arcpy.management.PolygonToLine(grens_dtbvlak_dissolve,
                                                        "in_memory\\grens_polyline")
    arcpy.AddMessage(f"Convert grens vlak to grens polyline")
    
    grens_polyline_clip = arcpy.analysis.Clip(grens_vlak_to_line,
                                            uitsnedeAOI,
                                            "in_memory\\grens_line_clip")
    arcpy.AddMessage(f"Clipped grens polyline to AOI")
    
    grens_polyline_clip_sp = arcpy.management.MultipartToSinglepart(grens_polyline_clip,
                                                                    "in_memory\\new_opnamegrens_sp")
    arcpy.AddMessage(f"Multipart to Singlepart grens polyline")
    
    new_opnamegrens = grens_polyline_clip_sp
    arcpy.management.AddField(new_opnamegrens, field_name="TYPE", field_type="LONG")
    arcpy.AddMessage(f"Added field 'TYPE' to new OG")
    arcpy.management.CalculateField(new_opnamegrens, field="TYPE", expression="21117")
    arcpy.AddMessage(f"Populated new OG with TYPE=21117")
    
    arcpy.management.Append(new_opnamegrens,
                            scheiding_lijnen_layer, 
                            schema_type="NO_TEST")
    arcpy.AddMessage(f"Appended new OG to versmald.gdb DTB_SCHEIDING_LIJNEN")

checkCurrentOG(scheiding_lijnen_layer)
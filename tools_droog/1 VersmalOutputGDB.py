import arcpy

#interpreter C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3

#Environment
arcpy.env.overwriteOutput = True

#Parameters  
versmalgrens = arcpy.GetParameterAsText(0) #Configure this input parameter datatype as: Feature Class, Feature Layer
uitsnedeAOI = arcpy.GetParameterAsText(1) #Configure this input parameter datatype as: Feature Class, Feature Layer
outputgdb = arcpy.GetParameterAsText(2) #Configure this input parameter datatype as: Workspace
versmaldgdb = arcpy.GetParameterAsText(3) #Configure this input parameter datatype as: Workspace
arcpy.AddMessage(f"Starting versmal script with:")
arcpy.AddMessage(f"Versmalgrens = {versmalgrens}")
arcpy.AddMessage(f"AOI = {uitsnedeAOI}")
arcpy.AddMessage(f"output.gdb = {outputgdb}")
arcpy.AddMessage(f"versmald.gdb = {versmaldgdb}")

#Doorloop elke DTB layer in the output.gdb
def iterateDTBlayers(outputgdb):
    output_layer_path = fr"{outputgdb}\DTB_DATA"
    arcpy.env.workspace = output_layer_path
    output_dtb_layers = arcpy.ListFeatureClasses()
    arcpy.AddMessage(f"Starting iterating DTB layers for: {output_dtb_layers}")
    
    for dtb_layer in output_dtb_layers:
        dtb_layer_file = fr"{output_layer_path}\{dtb_layer}"
        arcpy.AddMessage(f"Start versmalling for: {dtb_layer}")
        checkDTBlayer(dtb_layer, dtb_layer_file)
        
def checkDTBlayer(dtb_layer, dtb_layer_file):
    #Check layer name
    dtb_layer_name = dtb_layer
    dtb_layer_count = int(arcpy.GetCount_management(dtb_layer_name)[0])
    
    #Activate versmalmethode liggend aan welke DTB layer het is
    if dtb_layer_count == 0:
        arcpy.AddMessage(f"No feature found in {dtb_layer}, simple versmalling procedure")
        versmalEmptyLayer(dtb_layer, dtb_layer_file, versmaldgdb)
    
    elif dtb_layer_name == 'DTB_SCHEIDING_LIJNEN':
        arcpy.AddMessage(f"Special versmalling procedure for DTB_SCHEIDING_LIJNEN")
        versmalScheidingLijnen(dtb_layer, dtb_layer_file, versmalgrens, uitsnedeAOI)
        
    elif dtb_layer_name == 'DTB_OVERIGE_VLAKKEN':
        arcpy.AddMessage(f"Special versmalling procedure for DTB_OVERIGE_VLAKKEN")
        versmalOverigeVlakken(dtb_layer, dtb_layer_file, versmalgrens)
    
    elif dtb_layer_name == 'DTB_OVERIGE_LIJNEN':
        arcpy.AddMessage(f"Special versmalling procedure for DTB_OVERIGE_LIJNEN")
        versmalOverigeLijnen(dtb_layer, dtb_layer_file, versmalgrens)
        
    else:
        arcpy.AddMessage(f"Standard versmalling procedure for {dtb_layer}")
        versmalDTBlayer(dtb_layer, dtb_layer_file, versmalgrens)

#Versmal empty layer
def versmalEmptyLayer(dtb_layer, dtb_layer_file, versmaldgdb):
    versmald_path = fr"{versmaldgdb}\DTB_DATA\{dtb_layer}"
    arcpy.AddMessage(f"Copying feature directly into versmald.gdb")
    arcpy.CopyFeatures_management(dtb_layer_file, versmald_path)

#Versmal standaard layer
def versmalDTBlayer(dtb_layer, dtb_layer_file, versmalgrens):
    dtb_layer_clip = arcpy.analysis.Clip(dtb_layer_file, versmalgrens, f"in_memory\\{dtb_layer}_clip")
    arcpy.AddMessage(f"Clip layer to versmalgrens")
    fixMultiparts(dtb_layer, dtb_layer_clip, versmaldgdb)

#Versmal DTB_SCHEIDING_LIJNEN
def versmalScheidingLijnen(dtb_layer, dtb_layer_file, versmalgrens, uitsnedeAOI):
    dtb_layer_clip = arcpy.analysis.Clip(dtb_layer_file, versmalgrens, f"in_memory\\{dtb_layer}_clip")
    grens_vertices = arcpy.management.FeatureVerticesToPoints(versmalgrens, "in_memory\\grens_vertices")
    split_dtb_layer = arcpy.management.SplitLineAtPoint(dtb_layer_clip, grens_vertices, "in_memory\\dtb_lijn_split", 0.001)
    segment_grens_overlap = arcpy.management.SelectLayerByLocation(split_dtb_layer,
                                                                   "SHARE_A_LINE_SEGMENT_WITH",
                                                                   versmalgrens,
                                                                   None,
                                                                   "NEW_SELECTION")
    segment_grens_overlap_count = int(arcpy.management.GetCount(segment_grens_overlap)[0])
    if segment_grens_overlap_count > 0:
        arcpy.management.DeleteRows(segment_grens_overlap)
        arcpy.AddMessage(f"Deleted splitted line segments that overlap opnamegrens")
    arcpy.management.DeleteField(split_dtb_layer, drop_field=["ORIG_SEQ"])
    arcpy.AddMessage(f"Dropped ORIG_SEQ field")
    final_dtb_layer = split_dtb_layer
    fixMultiparts(dtb_layer, final_dtb_layer, versmaldgdb)
    
#Versmal DTB_OVERIGE_VLAKKEN t.b.v. Duikervlak uitzondering
def versmalOverigeVlakken(dtb_layer, dtb_layer_file, versmalgrens):
    DTB_no_duikers = arcpy.management.SelectLayerByAttribute(dtb_layer, 
                                                                  "NEW_SELECTION",
                                                                  '"TYPE" <> 31004')
    no_duiker_count = int(arcpy.management.GetCount(DTB_no_duikers)[0])
    
    #ANDERE OVERIGE_VLAKKEN AANWEZIG (NIET-DUIKERS)
    if no_duiker_count > 0:
        arcpy.AddMessage(f"Non-duikers present in OVERIGE VLAKKEN")
        #Versmal niet-duikers
        DTB_no_duikers_clip = arcpy.analysis.Clip(DTB_no_duikers, versmalgrens, "in_memory\\no_duikers_clip")
        arcpy.AddMessage(f"Clip all features, except for duikers")
        #Voeg duikers toe in zijn geheel
        DTB_only_duikers = arcpy.management.SelectLayerByAttribute(dtb_layer, 
                                                                    "NEW_SELECTION",
                                                                    '"TYPE" = 31004')
        DTB_duiker_intersect_versmalgrens = arcpy.management.SelectLayerByLocation(DTB_only_duikers,
                                                                                    "intersect",
                                                                                    versmalgrens,
                                                                                    None,
                                                                                    "SUBSET_SELECTION")
        arcpy.Append_management(DTB_duiker_intersect_versmalgrens, DTB_no_duikers_clip, "NO_TEST")
        arcpy.AddMessage(f"Append duikers 'as a whole' to versmalling")
        DTB_OV_ready = DTB_no_duikers_clip
        fixMultiparts(dtb_layer, DTB_OV_ready, versmaldgdb)
        
    #ALLEEN DUIKERS IN OVERIGE_VLAKKEN AANWEZIG
    if no_duiker_count == 0:
        arcpy.AddMessage(f"Only duikers present in OVERIGE VLAKKEN")
        DTB_duikers_intersect_versmalgrens = arcpy.management.SelectLayerByLocation(dtb_layer,
                                                                                        "intersect",
                                                                                        versmalgrens,
                                                                                        None,
                                                                                        "SUBSET_SELECTION")
        arcpy.AddMessage(f"Append duikers 'as a whole' to versmalling")
        fixMultiparts(dtb_layer, DTB_duikers_intersect_versmalgrens, versmaldgdb)
        
#Versmal DTB_OVERIGE_LIJNEN t.b.v. Duikerlijn uitzondering
def versmalOverigeLijnen(dtb_layer, dtb_layer_file, versmalgrens):
    DTB_no_duikers = arcpy.management.SelectLayerByAttribute(dtb_layer, 
                                                                  "NEW_SELECTION",
                                                                  '"TYPE" <> 21002')
    no_duiker_count = int(arcpy.management.GetCount(DTB_no_duikers)[0])
    
    #ANDERE OVERIGE_LIJNEN AANWEZIG (NIET-DUIKERS)
    if no_duiker_count > 0:
        arcpy.AddMessage(f"Non-duikers present in OVERIGE LIJNEN")
        #Versmal niet-duikers
        DTB_no_duikers_clip = arcpy.analysis.Clip(DTB_no_duikers, versmalgrens, "in_memory\\no_dfds_clip")
        arcpy.AddMessage(f"Clip all features, except for duikers")
        #Voeg duikers toe in zijn geheel
        DTB_only_duikers = arcpy.management.SelectLayerByAttribute(dtb_layer, 
                                                                    "NEW_SELECTION",
                                                                    '"TYPE" = 21002')
        DTB_duiker_intersect_versmalgrens = arcpy.management.SelectLayerByLocation(DTB_only_duikers,
                                                                                    "intersect",
                                                                                    versmalgrens,
                                                                                    None,
                                                                                    "SUBSET_SELECTION")
        arcpy.Append_management(DTB_duiker_intersect_versmalgrens, DTB_no_duikers_clip, "NO_TEST")
        arcpy.AddMessage(f"Append duikers 'as a whole' to versmalling")
        DTB_OV_ready = DTB_no_duikers_clip
        fixMultiparts(dtb_layer, DTB_OV_ready, versmaldgdb)
        
    #ALLEEN DUIKERS IN OVERIGE_LIJNEN AANWEZIG
    if no_duiker_count == 0:
        arcpy.AddMessage(f"Only duikers present in OVERIGE LIJNEN")
        DTB_duikers_intersect_versmalgrens = arcpy.management.SelectLayerByLocation(dtb_layer,
                                                                                        "intersect",
                                                                                        versmalgrens,
                                                                                        None,
                                                                                        "SUBSET_SELECTION")
        arcpy.AddMessage(f"Append duikers 'as a whole' to versmalling")
        fixMultiparts(dtb_layer, DTB_duikers_intersect_versmalgrens, versmaldgdb)
        
#Fix multiparts en dubbele DTB_ID's
def fixMultiparts(dtb_layer, dtb_vermalde_layer, versmaldgdb):
    versmald_path = fr"{versmaldgdb}\DTB_DATA\{dtb_layer}"
    arcpy.management.MultipartToSinglepart(dtb_vermalde_layer, versmald_path)
    arcpy.AddMessage(f"Converting multiparts to singleparts")
    arcpy.management.CalculateField(versmald_path,
                                    field="DTB_ID",
                                    expression_type="PYTHON3",
                                    expression="RemoveDuplicates(!DTB_ID!)",
                                    code_block="""uniqueList = []
def RemoveDuplicates(inputValue):
    if inputValue in uniqueList:
        return ""
    else:
        uniqueList.append(inputValue)
        return inputValue""")
    arcpy.AddMessage(f"Removed duplicate DTB id's from formerly multipart features")
    arcpy.management.DeleteField(versmald_path, drop_field=["ORIG_FID"])
    arcpy.AddMessage(f"Dropped ORIG_FID field")
    arcpy.AddMessage(f"Finished versmalling for {dtb_layer}")

iterateDTBlayers(outputgdb)
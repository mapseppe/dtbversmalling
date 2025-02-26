import arcpy
import arcpy.management

#interpreter C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3

#Environment
arcpy.env.overwriteOutput = True

#Parameters
    #Input Parameters
mainfolder = arcpy.GetParameterAsText(0) #Configure this input parameter datatype as: Workspace
versmalgrens = arcpy.GetParameterAsText(1) #Configure this input parameter datatype as: Feature Class
outputgdb = arcpy.GetParameterAsText(2) #Configure this input parameter datatype as: Workspace
regio_kg_points = arcpy.GetParameterAsText(3) #Configure this input parameter datatype as: Feature Class
regio_kg_lines = arcpy.GetParameterAsText(4) #Configure this input parameter datatype as: Feature Class
regio_kg_polygons = arcpy.GetParameterAsText(5) #Configure this input parameter datatype as: Feature Class
    #Output layer Parameters - configure these as datatype=FeatureLayer Derived Output
usv_output = arcpy.GetParameterAsText(6)
cpb_output = arcpy.GetParameterAsText(7)
kgp_output = arcpy.GetParameterAsText(8)
kgl_output = arcpy.GetParameterAsText(9)
kgv_output = arcpy.GetParameterAsText(10)
aoi_output = arcpy.GetParameterAsText(11)
vgs_output = arcpy.GetParameterAsText(12)

arcpy.AddMessage(f"Starting create-workspace script with:")
arcpy.AddMessage(f"Main Folder = {mainfolder}")
arcpy.AddMessage(f"Versmalgrens = {versmalgrens}")
arcpy.AddMessage(f"output.gdb = {outputgdb}")

#Create workspace
def createWorkspace(mainfolder, versmalgrens, outputgdb, regio_kg_points, regio_kg_lines, regio_kg_polygons):
    
    #Create Folders and Geodatabases
    arcpy.AddMessage(f"Creating validatie folder")
    arcpy.management.CreateFolder(mainfolder, "validaties")
    arcpy.AddMessage(f"Creating products gdb")
    arcpy.management.CreateFileGDB(mainfolder, "products")
    arcpy.AddMessage(f"Creating versmald gdb")
    arcpy.management.CreateFileGDB(mainfolder, "versmald")
    productsgdb = rf"{mainfolder}\products.gdb"
    versmaldgdb = rf"{mainfolder}\versmald.gdb"
    sr = arcpy.SpatialReference("RD_New")
    arcpy.AddMessage(f"Creating DTB_DATA in versmald gdb")
    arcpy.management.CreateFeatureDataset(versmaldgdb, "DTB_DATA", sr)
    
    #Prepare input data
    AOI_feature = f"{outputgdb}\DTB_ADMIN\AOI"
    arcpy.AddMessage(f"Adding kg_objects_buiten_grens to productsgdb")
    arcpy.analysis.Clip(regio_kg_points, AOI_feature, rf"{productsgdb}\kg_points_buiten_grens")
    arcpy.analysis.Clip(regio_kg_lines, AOI_feature, rf"{productsgdb}\kg_lines_buiten_grens")
    arcpy.analysis.Clip(regio_kg_polygons, AOI_feature, rf"{productsgdb}\kg_polygons_buiten_grens")
    arcpy.AddMessage(f"Copying versmalgrens to productsgdb")
    versmalgrens_copy = arcpy.management.CopyFeatures(versmalgrens, rf"{productsgdb}\versmalgrens_kopie")
    
    #Analyse versmalgrens
    dtb_lyr_path = r"M:\Geo\GDR-publicatie\layerbieb\Topografie\dtb.lyr"
    dtb_lyr = arcpy.mp.LayerFile(dtb_lyr_path)
    dtb_lijn = dtb_lyr.listLayers("dtb_lijn")[0]
    dtb_vlak = dtb_lyr.listLayers("dtb_vlak_uitgebreid")[0]
    arcpy.AddMessage(f"Clipping versmalgrens to AOI")
    clip_versmalgrens = arcpy.analysis.Clip(versmalgrens_copy, AOI_feature, "in_memory\\vgclip")
        #Check for unsnapped vertices
    arcpy.AddMessage(f"Versmalgrens feature to vertices")
    vertices_versmalgrens = arcpy.management.FeatureVerticesToPoints(clip_versmalgrens, rf"{productsgdb}\unsnapped_vertices")
    arcpy.AddMessage(f"Selecting vertices unsnapped to dtb_vlak")
    vertices_no_vlak = arcpy.management.SelectLayerByLocation(vertices_versmalgrens,
                                                              "WITHIN_CLEMENTINI",
                                                              dtb_vlak,
                                                              None,
                                                              "NEW_SELECTION",
                                                              "INVERT")
    arcpy.AddMessage(f"Adding vertices unsnapped to dtb_lijn to selection")
    vertices_no_lines = arcpy.management.SelectLayerByLocation(vertices_no_vlak,
                                                              "INTERSECT",
                                                              dtb_lijn,
                                                              None,
                                                              "ADD_TO_SELECTION")
    arcpy.AddMessage(f"Save unsnapped vertices in products gdb")
    arcpy.management.DeleteRows(vertices_no_lines)
        #Check for crossed polygon-borders
    arcpy.AddMessage(f"Converting versmalgrens to line")
    versmalgrens_lines = arcpy.management.FeatureToLine(clip_versmalgrens, "in_memory\\vglinesz")
    arcpy.AddMessage(f"Splitting line versmalgrens on vertices")
    versmalgrens_lines_split = arcpy.management.SplitLine(versmalgrens_lines, rf"{productsgdb}\crossed_polygons_borders")
    arcpy.AddMessage(f"Select line pieces that go through dtb_vlak polygon borders")
    lines_crossed_polygon = arcpy.management.SelectLayerByLocation(versmalgrens_lines_split,
                                                              "CROSSED_BY_THE_OUTLINE_OF",
                                                              dtb_vlak,
                                                              None,
                                                              "NEW_SELECTION",
                                                              "INVERT")
    arcpy.AddMessage(f"Save crossed-polygon-borders in products gdb")
    arcpy.management.DeleteRows(lines_crossed_polygon)
    
    #Add layers to project
    arcpy.AddMessage(f"Adding layers to arcgis project")
    arcproject = arcpy.mp.ArcGISProject("CURRENT")
    arcmap = arcproject.activeMap
    arcpy.SetParameter(6, rf"{outputgdb}\DTB_ADMIN\AOI")
    arcpy.SetParameter(7, rf"{productsgdb}\versmalgrens_kopie")
    arcpy.SetParameter(8, rf"{productsgdb}\kg_points_buiten_grens")
    arcpy.SetParameter(9, rf"{productsgdb}\kg_lines_buiten_grens")
    arcpy.SetParameter(10, rf"{productsgdb}\kg_polygons_buiten_grens")
    arcpy.SetParameter(11, rf"{productsgdb}\unsnapped_vertices")
    arcpy.SetParameter(12, rf"{productsgdb}\crossed_polygons_borders")

createWorkspace(mainfolder, versmalgrens, outputgdb, regio_kg_points, regio_kg_lines, regio_kg_polygons)
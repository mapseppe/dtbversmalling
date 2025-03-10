import arcpy
import arcpy.management

#interpreter C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3

#Environment
arcpy.env.overwriteOutput = True
arcpy.env.outputZFlag = "Disabled"

#Parameters
grenslijn = arcpy.GetParameterAsText(0)
usv = arcpy.GetParameterAsText(1)
lcp = arcpy.GetParameterAsText(2)
arcpy.AddMessage(f"Starting vertexcheck script with: {grenslijn}")

def checkGrens(grenslijn):
    
    #Get DTB lyr
    #dtb_lyr_path = r"M:\Geo\GDR-publicatie\layerbieb\Topografie\dtb.lyr"
    dtb_lyr_path = r"\\ad.rws.nl\p-dfs01\appsdata\Geo\GDR-publicatie\layerbieb\Topografie\dtb.lyr"
    dtb_lyr = arcpy.mp.LayerFile(dtb_lyr_path)
    dtb_lijn = dtb_lyr.listLayers("dtb_lijn")[0]
    dtb_vlak = dtb_lyr.listLayers("dtb_vlak_uitgebreid")[0]
    
    #Processing extent +100 m buffer
    arcpy.AddMessage("Setting processing area")
    desc = arcpy.Describe(grenslijn)
    extent = desc.extent
    xmin = extent.XMin - 100
    ymin = extent.YMin - 100
    xmax = extent.XMax + 100
    ymax = extent.YMax + 100
    arcpy.env.extent = arcpy.Extent(xmin, ymin, xmax, ymax)
    
    #Check for unsnapped vertices
    arcpy.AddMessage(f"Grenslijn feature to vertices")
    vertices_versmalgrens = arcpy.management.FeatureVerticesToPoints(grenslijn, "in_memory\\Unsnapped_Vertices")
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
    arcpy.AddMessage(f"Splitting line versmalgrens on vertices")
    versmalgrens_lines_split = arcpy.management.SplitLine(grenslijn, "in_memory\\Polygon_Border_Crossings")
    arcpy.AddMessage(f"Select line pieces that go through dtb_vlak polygon borders")
    lines_crossed_polygon = arcpy.management.SelectLayerByLocation(versmalgrens_lines_split,
                                                              "CROSSED_BY_THE_OUTLINE_OF",
                                                              dtb_vlak,
                                                              None,
                                                              "NEW_SELECTION",
                                                              "INVERT")
    arcpy.management.DeleteRows(lines_crossed_polygon)
    
    #Add layers to project
    arcpy.SetParameter(1, "in_memory\\Unsnapped_Vertices")
    arcpy.SetParameter(2, "in_memory\\Polygon_Border_Crossings")

checkGrens(grenslijn)
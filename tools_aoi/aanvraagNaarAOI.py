import arcpy
import arcpy.management

arcpy.env.overwriteOutput = True
arcpy.env.outputZFlag = "Disabled"

#Input parameters
aanvraag_shape = arcpy.GetParameterAsText(0) #Configure this input parameter datatype as: Feature Layer
AOI_layer = arcpy.GetParameterAsText(1) #Configure this input parameter datatype as: Feature Class, Feature Layer

#dtb features
dtb_lyr_path = r"M:\Geo\GDR-publicatie\layerbieb\Topografie\dtb.lyr"
dtb_lyr = arcpy.mp.LayerFile(dtb_lyr_path)
dtb_lijn = dtb_lyr.listLayers("dtb_lijn")[0]
dtb_vlak = dtb_lyr.listLayers("dtb_vlak_uitgebreid")[0]

#Buffer 1500 met dissolve
arcpy.AddMessage("Defining processing area")
processing_area = arcpy.analysis.Buffer(aanvraag_shape, "in_memory\\pra", 1500, dissolve_option="ALL")

#Clip dtblijn en dtbvlak op buffer -- misschien sneller set processing extent??
arcpy.AddMessage("Clipping dtb_vlak and dtb_lijn")
dtblijn_clip = arcpy.analysis.Clip(dtb_lijn, processing_area, "in_memory\\dtblc")
dtbvlak_clip = arcpy.analysis.Clip(dtb_vlak, processing_area, "in_memory\\dtbvc")

#Dissolve dtbvlakclip
arcpy.AddMessage("Dissolving the dtb_vlak")
dtb_vlak_dslv = arcpy.management.Dissolve(dtbvlak_clip, "in_memory\\dtbvc324", multi_part="SINGLE_PART")

#SelectAtt cte = MD29 dtblijnclip
arcpy.AddMessage("Selecting KSMS in dtb_lijn")
dtblijn_ksms = arcpy.management.SelectLayerByAttribute(dtblijn_clip, "NEW_SELECTION", '"cte" = \'MD29\'')

#SplitPolygonByLine met dtblijn split op dtbvlak FeatureToPolygon
arcpy.AddMessage("Splitting dtb_vlak_dissolve based on KSMS lines")
dtb_vlak_ksms_split = arcpy.management.FeatureToPolygon([dtb_vlak_dslv, dtblijn_ksms], "in_memory\\d4da45tbv4")

#Check overlap van 'door-OG-en-KSMS-gesplitte-dtb_stukken' met aanvraagpolygoon
arcpy.AddMessage("Making new layer dtb_vlak pieces that overlap with aanvraag polygon")
dtb_split_in_aanvraag = arcpy.management.SelectLayerByLocation(dtb_vlak_ksms_split, "INTERSECT", aanvraag_shape)
aoi_part_1 = arcpy.management.CopyFeatures(dtb_split_in_aanvraag, "in_memory\\d4tbv344")
aoi_part_2 = arcpy.management.Append(aanvraag_shape, aoi_part_1, "NO_TEST")

#Uiteindelijke dissolve
aoi_dissolve = arcpy.management.Dissolve(aoi_part_2, "in_memory\\aoi2", multi_part="SINGLE_PART")
arcpy.AddMessage("Adding generated AOI to AOI layer")
arcpy.management.Append(aoi_dissolve, AOI_layer, "NO_TEST")
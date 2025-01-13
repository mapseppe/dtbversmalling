import arcpy

#Environment
arcpy.env.overwriteOutput = True

#Parameters  
laag_uitsnede = arcpy.GetParameterAsText(0) #Configure this input parameter datatype as: Feature Class, Feature Layer
laag_versmalling = arcpy.GetParameterAsText(1) #Configure this input parameter datatype as: Feature Class, Feature Layer
arcpy.AddMessage(f"Starting AppendSelectionToVersmalling script with:")
arcpy.AddMessage(f"Laag Uitsnede = {laag_uitsnede}")
arcpy.AddMessage(f"Laag Versmalling = {laag_versmalling}")

# Check if the layer has a selection
desc = arcpy.Describe(laag_uitsnede)
if hasattr(desc, "FIDSet") and desc.FIDSet:  # Check if FIDSet is not empty
    arcpy.AddMessage(f"Laag {laag_uitsnede} heeft een selectie")
    
    arcpy.management.Append(inputs=laag_uitsnede, target=laag_versmalling, schema_type="NO_TEST")
    arcpy.AddMessage(f"Selected features van {laag_uitsnede} toegevoegd aan {laag_versmalling}.")
else:
    arcpy.AddError(f"Laag {laag_uitsnede} heeft geen selectie. Selecteer eerst de features die je naar de versmalling laag wilt kopiëren.")
print """
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

*******   *******   *******   *******
*******   *******   *******   *******
**   **   **        **        **   **
**   **   **        **        **   **
**   **   **  ***   **        **   **
**   **   **   **   **        **   **
*******   *******   *******   *******
*******   *******   *******   *******

GIS Division
Information Technology
Douglas County, Kansas

MultiPage_AgUse_Script
Purpose: Creates ag use maps for every parcel in a specified table.
Version history: Created 2013
Modified January 2015 by Amy Roust

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

"""

from os import path, remove
from sys import argv
from time import sleep, strftime
import arcpy
import sys
import traceback
arcpy.env.overwriteOutput=True
arcpy.env.parallelProcessingFactor = "100%"
relpath = path.dirname(argv[0])
finallocation = r'\\dggissrv2\GISdata\Appraiser\AgUseMapReview'

## Changed from .csv to .txt since this script uses \n instead of commas after the input strings.
badpinslocation = r'\\dggissrv2\GISdata\Appraiser\AgUseMapReview\badpins.txt'

badpins = open(badpinslocation, 'a')
badpins.truncate()
badpins.write("Parcels not completely covered by ag use or soil type.\n")
badpins.close()

#Loop through table and create an ag map based on the row value
## Replace this with a da.SearchCursor and append the values to a list.
cursor = arcpy.SearchCursor(path.join(relpath, r'MultiPageAgUseLists.gdb\Township12_Batch1'))
for i in cursor:
    try:
        print "Start time: " + strftime("%Y-%m-%d %H:%M:%S") +"\n"
        PIN = "'" + i.getValue("JoinPin")+"'"
        NoQuotePIN = i.getValue("JoinPin")
        print "\tAnalyzing parcel PIN " + PIN + " ..."
        
        #Reference MXD and layers
        mxd = arcpy.mapping.MapDocument(relpath + r'\AgUse.mxd')
        df = arcpy.mapping.ListDataFrames(mxd, "agmap")[0]

        ParcelLayer = arcpy.mapping.ListLayers(mxd,  "Parcel")[0]
        AgUseLayer = arcpy.mapping.ListLayers(mxd,  "AgUse")[0]
        SoilLayer = arcpy.mapping.ListLayers(mxd,  "Soil")[0]  

        #Set definition query on Parcels using PIN
        for lyr in arcpy.mapping.ListLayers(mxd):
            if lyr.name == "Parcel":
                lyr.definitionQuery = "JOINPIN = " + PIN

        #Identity analysis creates the aguse from (Parcels, AgUse and Soil).
        #Add ACRES field and Calc based on shape.area)               
        arcpy.Identity_analysis(ParcelLayer, AgUseLayer, r'in_memory\aguse', "ALL", "1 Feet", "NO_RELATIONSHIPS")

        arcpy.Identity_analysis(r'in_memory\aguse', SoilLayer, r'in_memory\aguse_soil', "ALL", "1 Feet", "NO_RELATIONSHIPS")

        arcpy.AddField_management(r'in_memory\aguse_soil',"ACRES","DOUBLE","#","1","#","#","NULLABLE","NON_REQUIRED","#")

        arcpy.CalculateField_management(r'in_memory\aguse_soil',"ACRES","!shape.area@acres!","PYTHON_9.3","#")

        #Create Frequency table using (TYPE, MUSYM and Sum byACRES). Then Add Frequency table to mxd.
        arcpy.Frequency_analysis(r'in_memory\aguse_soil', r'in_memory\Freq',"TYPE;MUSYM","ACRES")

        Freq = arcpy.mapping.TableView(r'in_memory\Freq')

        arcpy.mapping.AddTableView(df,Freq)

        #Create Frequency table from first frequency table using (TYPE and Sum by ACRES).  Then Add Frequency table to mxd.
        arcpy.Frequency_analysis(r'in_memory\aguse_soil', r'in_memory\Freq1', "TYPE", "ACRES")
        Freq1 = arcpy.mapping.TableView(r'in_memory\Freq1')

        #Append PIN to error log if the parcel is not completely covered by ag use or soil layer.
        freqCursorFields = ["TYPE", "MUSYM"]
        freqCursor = arcpy.da.SearchCursor(r'in_memory\Freq', freqCursorFields)
        try:
            badpins = open(badpinslocation, 'a')
            for freqRow in freqCursor:
                if(str(freqRow[0]) == '' or str(freqRow[1]) == ''):
                    badpins.write(str(NoQuotePIN) + '\n')
                
                else:
                    pass
        except:
            pass
        finally:
            badpins.close()
        
        try:
            del freqCursor
            
        except:
            print 'freqCursor does not exist to delete.'    

        arcpy.mapping.AddTableView(df,Freq1)
        print "\t\tAnalysis Complete."

        #refresh table of contents before creating ddp
        arcpy.RefreshTOC()

#------------------------------------- TABLE 1 -----------------------------------------------------
        print "\n\tBuilding ag use by soil type table in map layout..."
                
        #Find both Frequency tables in the mxd and set them as variables
        FreqTable = arcpy.mapping.ListTableViews(mxd, "Freq*",df) [0]
        Freq1Table = arcpy.mapping.ListTableViews(mxd, "Freq1*",df) [0]

        #Add definition query to remove records in freq tables with blank values.
        for lyr in arcpy.mapping.ListTableViews(mxd):
            if lyr.name == "Freq":
                lyr.definitionQuery = "TYPE <> '' AND MUSYM <> ''"	

        for lyr in arcpy.mapping.ListTableViews(mxd):
            if lyr.name == "Freq1":
                lyr.definitionQuery = "TYPE <> ''"

        arcpy.RefreshTOC()

        #Reference page layout elements
        for elm in arcpy.mapping.ListLayoutElements(mxd):
          if elm.name == "NoGrowth": noGrowth = elm
          if elm.name == "horzLine": horzLine = elm
          if elm.name == "vertLine": vertLine = elm
          if elm.name == "cellTxt":  cellTxt = elm
          if elm.name == "headerTxt": headerTxt = elm
          if elm.name == "NoGrowth1": noGrowth1 = elm
          if elm.name == "horzLine1": horzLine1 = elm
          if elm.name == "vertLine1": vertLine1 = elm
          if elm.name == "cellTxt1":  cellTxt1 = elm
          if elm.name == "headerTxt1": headerTxt1 = elm

        #Clean-up before next page
        for elm in arcpy.mapping.ListLayoutElements(mxd, "GRAPHIC_ELEMENT", "*clone*"):
            try:
                elm.delete()
            except:
                pass
        for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "*clone*"):
            try:
                elm.delete()
            except:
                pass
            
        noGrowth.elementPositionX = -3
        cellTxt.elementPositionX = -3
        headerTxt.elementPositionX = -3
        horzLine.elementPositionX = -3
        vertLine.elementPositionX = -3

        #Reference DDP object and set appropriate page
        ddp = mxd.dataDrivenPages
        ddp.refresh()
        ddp.currentPageID = ddp.getPageIDFromName(PIN)

        #Graphic table variable values
        tableHeight = 3
        tableWidth = 2.4
        headerHeight = 0.2
        rowHeight = 0.15
        upperX = 8.1
        upperY = 7.2

        #Build selection set
        numRecords = int(arcpy.GetCount_management(FreqTable).getOutput(0))
        print "\t\tRecords in ag use by soil type table: " + str(numRecords)

        #Sort selection
        arcpy.Sort_management(FreqTable, r'in_memory\sort1', [["TYPE", "ASCENDING"]])

        #Add note if there are no records > 100%
        if numRecords == 0:
          noGrowth.elementPositionX = 3
          noGrowth.elementPositionY = 2
        else:
            #if number of rows exceeds page space, resize row height
            if ((tableHeight - headerHeight) / numRecords) < rowHeight:
                headerHeight = headerHeight * ((tableHeight - headerHeight) / numRecords) / rowHeight
                rowHeight = (tableHeight - headerHeight) / numRecords
            else:
                pass
            
        #Set and clone vertical line work
        vertLine.elementHeight = (headerHeight) + (rowHeight * numRecords)
        vertLine.elementPositionX = upperX
        vertLine.elementPositionY = upperY
        temp_vert = vertLine.clone("_clone")
        temp_vert.elementPositionX = upperX + .7
        temp_vert = vertLine.clone("_clone")
        temp_vert.elementPositionX = upperX + 1.6
        temp_vert = vertLine.clone("_clone")
        temp_vert.elementPositionX = upperX + 2.4
        
        #Set and clone horizontal line work
        horzLine.elementWidth = tableWidth
        horzLine.elementPositionX = upperX
        horzLine.elementPositionY = upperY
        horzLine.clone("_clone")
        horzLine.elementPositionY = upperY - headerHeight

        #print numRecords
        y = upperY - headerHeight
        for horz in range(1, numRecords+1):
            y = y - rowHeight
            temp_horz = horzLine.clone("_clone")
            temp_horz.elementPositionY = y

        #Set header text elements
        headerTxt.fontSize = headerHeight / 0.0155
        headerTxt.text = "TYPE"
        headerTxt.elementPositionX = upperX + .35
        headerTxt.elementPositionY = upperY - (headerHeight / 2)
        newFieldTxt = headerTxt.clone("_clone")
        newFieldTxt.text = "SOIL"
        newFieldTxt.elementPositionX = upperX + 1.15
        newFieldTxt1 = headerTxt.clone("_clone")
        newFieldTxt1.text = "ACRES"
        newFieldTxt1.elementPositionX = upperX + 2
        
        #Set and clone cell text elements
        cellTxt.fontSize = rowHeight / 0.0155

        y = upperY - headerHeight
        rows = arcpy.SearchCursor(r'in_memory\sort1')
        for row in rows:
            x = upperX + 0.05
            col1CellTxt = cellTxt.clone("_clone")
            col1CellTxt.text = row.getValue("TYPE")
            col1CellTxt.elementPositionX = x + .3
            col1CellTxt.elementPositionY = y
            col2CellTxt = cellTxt.clone("_clone")
            col2CellTxt.text = row.getValue("MUSYM")

            col2CellTxt.elementPositionX = x + 1.0
            col2CellTxt.elementPositionY = y
            col3CellTxt = cellTxt.clone("_clone")
            col3CellTxt.text = str(round(row.getValue("ACRES"),1))
            col3CellTxt.elementPositionX = x + 1.8
            col3CellTxt.elementPositionY = y

            y = y - rowHeight

        print "\t\tFinished creating table."

#------------------------------------- TABLE 2 -----------------------------------------------------
        
        print "\n\tBuilding ag use acreage summary table in map layout..."
        noGrowth1.elementPositionX = -3
        cellTxt1.elementPositionX = -3
        headerTxt1.elementPositionX = -3
        horzLine1.elementPositionX = -3
        vertLine1.elementPositionX = -3

        #Reference DDP object and set appropriate page
        ddp = mxd.dataDrivenPages
        ddp.refresh()
        ddp.currentPageID = ddp.getPageIDFromName(PIN)

        #Graphic table variable values
        tableHeight1 = 3
        tableWidth1 = 1.6
        headerHeight1 = 0.2
        rowHeight1 = 0.15
        upperX1 = 8.5
        upperY1 = 2

        #Build selection set
        numRecords1 = int(arcpy.GetCount_management(Freq1Table).getOutput(0))
        print "\t\tRecords found in ag use acreage summary table: " + str(numRecords1)

        #Sort selection
        sortFields = [["TYPE", "ASCENDING"]]
        arcpy.Sort_management(Freq1Table, r'in_memory\sort2', sortFields)

        #Add note if there are no Records > 100%
        if numRecords1 == 0:
          noGrowth1.elementPositionX = 3
          noGrowth1.elementPositionY = 2
        else:
          #if number of rows exceeds page space, resize row height
          if ((tableHeight1 - headerHeight1) / numRecords1) < rowHeight1:
            headerHeight1 = headerHeight1 * ((tableHeight1 - headerHeight1) / numRecords1) / rowHeight1
            rowHeight1 = (tableHeight1 - headerHeight1) / numRecords1
            
        #Set and clone vertical line work
        vertLine1.elementHeight = (headerHeight1) + (rowHeight1 * numRecords1)
        vertLine1.elementPositionX = upperX1
        vertLine1.elementPositionY = upperY1

        temp_vert1 = vertLine1.clone("_clone")
        temp_vert1.elementPositionX = upperX1 + .7
        temp_vert1 = vertLine1.clone("_clone")
        temp_vert1.elementPositionX = upperX1 + 1.6

        #Set and clone horizontal line work
        horzLine1.elementWidth = tableWidth1
        horzLine1.elementPositionX = upperX1
        horzLine1.elementPositionY = upperY1
        horzLine1.clone("_clone")
        horzLine1.elementPositionY = upperY1 - headerHeight1

        #print numRecords
        y1=upperY1 - headerHeight1
        for horz1 in range(1, numRecords1+1):
          y1 = y1 - rowHeight1
          temp_horz1 = horzLine1.clone("_clone")
          temp_horz1.elementPositionY = y1

        #Set header text elements
        headerTxt1.fontSize = headerHeight1 / 0.0155
        headerTxt1.text = "TYPE"
        headerTxt1.elementPositionX = upperX1 + .35
        headerTxt1.elementPositionY = upperY1 - (headerHeight1 / 2)

        newFieldTxt2 = headerTxt1.clone("_clone")
        newFieldTxt2.text = "ACRES"
        newFieldTxt2.elementPositionX = upperX1 + 1.15

        #Set and clone cell text elements
        cellTxt1.fontSize = rowHeight1 / 0.0155
        
        y1 = upperY1 - headerHeight1
        rows1 = arcpy.SearchCursor(r'in_memory\sort2')
        for row1 in rows1:
            x1 = upperX1 + 0.05
            col1CellTxt1 = cellTxt1.clone("_clone")
            col1CellTxt1.text = row1.getValue("TYPE")
            col1CellTxt1.elementPositionX = x1 + .3
            col1CellTxt1.elementPositionY = y1
            col2CellTxt1 = cellTxt1.clone("_clone")
            col2CellTxt1.text = str(round(row1.getValue("ACRES"), 1))
            col2CellTxt1.elementPositionX = x1 + 1.0
            col2CellTxt1.elementPositionY = y1
         
            y1 = y1 - rowHeight1
     
        print "\t\tFinished creating table."

#------------------------------------- JPG EXPORT -----------------------------------------------------

        print "\n\tExporting map to jpg..."
        
        finallocationwithPIN = path.join(finallocation, NoQuotePIN) + ".jpg"
        
        ## This conditional was previously looking for the
        ## PIN variable (only) as a file path.
        if path.exists(finallocationwithPIN):
            remove(finallocationwithPIN)
        else:
            pass
        
        arcpy.mapping.ExportToJPEG(mxd, finallocationwithPIN, resolution = 200)

        print "\t\tDone. \n\n\tParcel map " + NoQuotePIN + " is ready for review! \n\nCompletion time: " + strftime("%Y-%m-%d %H:%M:%S") + "\n\n******************************\n"

        arcpy.RefreshTOC()

        del mxd

        #Delete Layers from Memory
        arcpy.Delete_management("in_memory")
        del PIN
        del NoQuotePIN

        #i = cursor.next() ## for ... in ... syntax does this automatically.
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        print ''.join('' + line for line in lines)
        del exc_type, exc_value, exc_traceback
        sys.exc_clear()
        
del cursor

print "All of your maps are completed. Wow, that was easy!"

time.sleep(5)

print "This window will close automatically in 15 seconds. Bye now!"

time.sleep(15)


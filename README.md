# AgUse
Here is the ag use Python script that generates a separate map for each PIN in a geodatabase table. Currently, it works great until it gets into the 130s, then it errors out when it tries to export the map to a JPEG. (The function is after the JPG EXPORT comment, called arcpy.mapping.ExporttoJPEG) The first time I ran it, I got about 140 maps before the script stopped working, but subsequent re-runs have only gotten into the mid 130s before crashing. Maybe there is a limit to the ExporttoJPEG function? Anyway, I appreciate any suggestions. - Amy

# DT Changes 2015-02-21
Changed all references to the in_memory geodatabase
to raw strings. Previously, some of them included
a single slash, while others included a double slash
as a separator between the gdb and the feature class.

Changed all file path references to use backslashes ( \ )
instead of forward slashes ( / ).

Changed the way the badpins file is used. Instead of opening it once
and keeping it open until the script is completed in its entirety,
the badpins file is only opened to truncate it at the start of the
script and then again whenever there is data to be written to it.
Also made it a .txt file instead of a .csv file since there aren't
any commas used in the strings that are written to it.

Changed the check for the existence of a previous jpg to reference
a full path without quotes around the pin. Also made the same change
to the jpg export location.

Wrapped the operations for each row from the main SearchCursor in a
try/except block.

Added explicit "else" statements to several "if" statements.

Suggestions for future improvement:
There are three arcpy.refreshTOC() calls per row. That can't be great
for performance. Is the last one actually needed?

There are two times per row where the data driven pages object is
set, refreshed, and then has its current page ID value set. Could
one of those times be removed?

Change the first SearchCursor in the script from an arcpy.SearchCursor
to an arcpy.da.SearchCursor.

After changing the main cursor to an arcpy.da.SearchCursor, append
all of the rows from it to a list, then close the cursor. Then, loop
through the list elements instead of looping through the cursor. This
reduces the need for a stable connection to the database throughout
the entire script's execution and may result in a performance improvement.

I didn't understand everything that was going on with the table views
so I tried not to change anything that was directly related to them.
They look like good candiates for separating out some into distinct
functions though, especially since you already have them quasi-separated
with comments.
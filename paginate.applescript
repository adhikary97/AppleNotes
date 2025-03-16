on formatDateAsISO(theDate)
    -- Get components using AppleScript date commands
    set y to year of theDate
    set m to month of theDate as integer
    set d to day of theDate
    set h to hours of theDate
    set min to minutes of theDate
    set s to seconds of theDate as integer
    
    -- Pad with leading zeros if needed
    if m < 10 then set m to "0" & m
    if d < 10 then set d to "0" & d
    if h < 10 then set h to "0" & h
    if min < 10 then set min to "0" & min
    if s < 10 then set s to "0" & s
    
    return y & "-" & m & "-" & d & " " & h & ":" & min & ":" & s
end formatDateAsISO

tell application "Notes"
    -- Get all notes
    set allNotes to every note
    set noteCounter to 0
    
    -- Process each note
    repeat with theNote in allNotes
        set noteCounter to noteCounter + 1
        
        -- Format the dates
        set formattedCreationDate to my formatDateAsISO(creation date of theNote)
        set formattedModificationDate to my formatDateAsISO(modification date of theNote)
        
        log "------- Note " & noteCounter & " -------"
        log "Title: " & name of theNote
        log "ID: " & id of theNote
        log "Body: " & body of theNote
        log "Date Created: " & formattedCreationDate
        log "Date Updated: " & formattedModificationDate
        log "----------------"
    end repeat
    
    log "Processed " & noteCounter & " notes in total."
end tell
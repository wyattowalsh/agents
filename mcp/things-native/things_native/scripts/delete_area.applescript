on replaceText(findText, replacementText, sourceText)
    set savedDelimiters to AppleScript's text item delimiters
    try
        set AppleScript's text item delimiters to findText
        set pieces to every text item of sourceText
        set AppleScript's text item delimiters to replacementText
        set joinedText to pieces as text
        set AppleScript's text item delimiters to savedDelimiters
        return joinedText
    on error errorMessage number errorNumber
        set AppleScript's text item delimiters to savedDelimiters
        error errorMessage number errorNumber
    end try
end replaceText

on jsonString(sourceValue)
    set encoded to sourceValue as text
    set encoded to my replaceText("\\", "\\\\", encoded)
    set encoded to my replaceText("\"", "\\\"", encoded)
    set encoded to my replaceText(return, "\\r", encoded)
    set encoded to my replaceText(linefeed, "\\n", encoded)
    set encoded to my replaceText(tab, "\\t", encoded)
    return "\"" & encoded & "\""
end jsonString

on jsonArray(sourceValues)
    set encodedValues to {}
    repeat with stateValue in sourceValues
        set end of encodedValues to my jsonString(contents of stateValue)
    end repeat
    set savedDelimiters to AppleScript's text item delimiters
    set AppleScript's text item delimiters to ","
    set encodedText to encodedValues as text
    set AppleScript's text item delimiters to savedDelimiters
    return "[" & encodedText & "]"
end jsonArray

on run argv
    if (count of argv) is not 2 then error number 64
    set mutationPhase to item 1 of argv
    set targetID to item 2 of argv
    tell application "Things3"
        if not (exists area id targetID) then
            set stateJSON to my jsonArray({"area-absent:" & targetID})
            return "{\"status\":\"skipped\",\"affectedCount\":0,\"cascadeCount\":0,\"cascadeObserved\":true,\"targetState\":" & stateJSON & ",\"readbackVerified\":true,\"messageCode\":\"area_absent\"}"
        end if
        set targetArea to area id targetID
        set childCount to count of to dos of targetArea
        set stateRecords to {"area:" & targetID & ":" & (name of targetArea)}
        repeat with childItem in (to dos of targetArea)
            set childID to id of childItem
            set childModified to modification date of childItem as text
            set end of stateRecords to "todo:" & childID & ":" & childModified
        end repeat
        set stateJSON to my jsonArray(stateRecords)
        if mutationPhase is "preview" then
            return "{\"status\":\"previewed\",\"affectedCount\":1,\"cascadeCount\":" & childCount & ",\"cascadeObserved\":true,\"targetState\":" & stateJSON & ",\"readbackVerified\":false,\"messageCode\":\"delete_area_preview\"}"
        end if
        if mutationPhase is not "execute" then error number 64
        delete targetArea
        set removed to not (exists area id targetID)
        set postStateJSON to my jsonArray({"area-absent:" & targetID})
        if removed then
            return "{\"status\":\"changed\",\"affectedCount\":1,\"cascadeCount\":" & childCount & ",\"cascadeObserved\":true,\"targetState\":" & postStateJSON & ",\"readbackVerified\":true,\"messageCode\":\"delete_area_changed\"}"
        end if
        return "{\"status\":\"ambiguous\",\"affectedCount\":1,\"cascadeCount\":" & childCount & ",\"cascadeObserved\":true,\"targetState\":" & postStateJSON & ",\"readbackVerified\":false,\"messageCode\":\"delete_area_ambiguous\"}"
    end tell
end run

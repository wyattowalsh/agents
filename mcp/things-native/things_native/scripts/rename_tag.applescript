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
    if (count of argv) is not 3 then error number 64
    set mutationPhase to item 1 of argv
    set targetID to item 2 of argv
    set replacementName to item 3 of argv
    tell application "Things3"
        if not (exists tag id targetID) then
            set stateJSON to my jsonArray({"tag-absent:" & targetID})
            return "{\"status\":\"skipped\",\"affectedCount\":0,\"cascadeCount\":0,\"cascadeObserved\":false,\"targetState\":" & stateJSON & ",\"readbackVerified\":true,\"messageCode\":\"tag_absent\"}"
        end if
        set targetTag to tag id targetID
        set parentID to "none"
        try
            set parentID to id of parent tag of targetTag
        end try
        set stateJSON to my jsonArray({"tag:" & targetID & ":" & (name of targetTag) & ":parent:" & parentID})
        if mutationPhase is "preview" then
            return "{\"status\":\"previewed\",\"affectedCount\":1,\"cascadeCount\":0,\"cascadeObserved\":false,\"targetState\":" & stateJSON & ",\"readbackVerified\":false,\"messageCode\":\"rename_tag_preview\"}"
        end if
        if mutationPhase is not "execute" then error number 64
        set name of targetTag to replacementName
        set verified to (name of (tag id targetID) is replacementName)
        set postStateJSON to my jsonArray({"tag:" & targetID & ":" & (name of (tag id targetID)) & ":parent:" & parentID})
        if verified then
            return "{\"status\":\"changed\",\"affectedCount\":1,\"cascadeCount\":0,\"cascadeObserved\":false,\"targetState\":" & postStateJSON & ",\"readbackVerified\":true,\"messageCode\":\"rename_tag_changed\"}"
        end if
        return "{\"status\":\"ambiguous\",\"affectedCount\":1,\"cascadeCount\":0,\"cascadeObserved\":false,\"targetState\":" & postStateJSON & ",\"readbackVerified\":false,\"messageCode\":\"rename_tag_ambiguous\"}"
    end tell
end run

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
    if (count of argv) is not 1 then error number 64
    set mutationPhase to item 1 of argv
    tell application "Things3"
        set completedItems to to dos whose status is completed
        set affectedCount to count of completedItems
        set stateRecords to {}
        repeat with completedItem in completedItems
            set itemID to id of completedItem
            set itemModified to modification date of completedItem as text
            set end of stateRecords to "completed-todo:" & itemID & ":" & itemModified
        end repeat
        if affectedCount is 0 then set stateRecords to {"completed-none"}
        set stateJSON to my jsonArray(stateRecords)
        if mutationPhase is "preview" then
            return "{\"status\":\"previewed\",\"affectedCount\":" & affectedCount & ",\"cascadeCount\":0,\"cascadeObserved\":false,\"targetState\":" & stateJSON & ",\"readbackVerified\":false,\"messageCode\":\"log_completed_preview\"}"
        end if
        if mutationPhase is not "execute" then error number 64
        log completed now
        -- The command has no result and the public SDEF exposes no definitive
        -- logged-state predicate. Report ambiguity instead of claiming a
        -- verified mutation from command completion alone.
        return "{\"status\":\"ambiguous\",\"affectedCount\":" & affectedCount & ",\"cascadeCount\":0,\"cascadeObserved\":false,\"targetState\":" & stateJSON & ",\"readbackVerified\":false,\"messageCode\":\"log_completed_unverified\"}"
    end tell
end run

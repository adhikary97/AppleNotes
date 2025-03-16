import html
import json
import os
import re
import subprocess
import time
from datetime import datetime

import pyrebase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase configuration
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()


def process_notes_in_batches(total_notes=1134):
    """Process notes in smaller batches to avoid buffer issues"""
    batch_size = 50  # Process 50 notes at a time
    all_notes = []

    for batch_start in range(1, total_notes + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, total_notes)
        print(f"Processing notes {batch_start} to {batch_end}...")

        # The updated AppleScript to process a batch of notes with the new date format
        script = f"""
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
            set allNotes to every note
            
            -- Log the start of the batch
            log "BATCH_START"
            
            set noteCounter to {batch_start} - 1
            
            repeat with i from {batch_start} to {batch_end}
                if i <= (count of allNotes) then
                    set theNote to item i of allNotes
                    set noteCounter to noteCounter + 1
                    
                    -- Format the dates using our helper function
                    set formattedCreationDate to my formatDateAsISO(creation date of theNote)
                    set formattedModificationDate to my formatDateAsISO(modification date of theNote)
                    
                    -- Note header
                    log "------- Note " & noteCounter & " -------"
                    
                    -- Get note properties with error handling
                    try
                        log "Title: " & name of theNote
                    on error
                        log "Title: [Untitled]"
                    end try
                    
                    try
                        log "ID: " & id of theNote
                    on error
                        log "ID: unknown-id-" & i
                    end try
                    
                    try
                        log "Body: " & body of theNote
                    on error
                        log "Body: [No content]"
                    end try
                    
                    try
                        log "Date Created: " & formattedCreationDate
                    on error
                        log "Date Created: unknown"
                    end try
                    
                    try
                        log "Date Updated: " & formattedModificationDate
                    on error
                        log "Date Updated: unknown"
                    end try
                    
                    -- Note footer
                    log "----------------"
                end if
            end repeat
            
            -- Log the end of the batch
            log "BATCH_END"
            
            return "Processed notes " & {batch_start} & " to " & {batch_end}
        end tell
        """

        try:
            # Execute the AppleScript
            process = subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout, stderr = process.communicate()

            if process.returncode != 0:
                print(f"Error processing batch: {stderr}")
                continue

            # Combine stdout and stderr since AppleScript's "log" command outputs to stderr
            combined_output = stdout + "\n" + stderr

            # Verify the batch has proper markers
            if "BATCH_START" in combined_output and "BATCH_END" in combined_output:
                # Parse this batch of notes
                batch_notes = parse_notes(combined_output)
                if batch_notes:
                    print(f"Parsed {len(batch_notes)} notes in this batch")
                    all_notes.extend(batch_notes)
                else:
                    print("No notes parsed in this batch")
            else:
                print("Batch markers not found in output")

        except Exception as e:
            print(f"Error processing batch {batch_start}-{batch_end}: {e}")

        # Add a small delay between batches
        time.sleep(1)

    return all_notes


def parse_notes(output):
    """Parse the AppleScript output into structured data"""
    notes = []

    # Split the output into individual note blocks
    note_blocks = re.split(r"------- Note \d+ -------", output)

    # Skip the first element (before the first note marker)
    if len(note_blocks) > 1:
        note_blocks = note_blocks[1:]

    for block in note_blocks:
        # Verify this is a complete note block
        if "----------------" not in block:
            continue

        # Extract note information using regex
        title_match = re.search(r"Title: (.*?)(?:\n|$)", block)
        id_match = re.search(r"ID: (.*?)(?:\n|$)", block)

        # More robust body extraction - handle potential HTML content better
        # Look for the body section and capture everything until the Date Created line
        body_match = re.search(r"Body: (.*?)(?=Date Created:)", block, re.DOTALL)
        created_match = re.search(r"Date Created: (.*?)(?:\n|$)", block)
        updated_match = re.search(r"Date Updated: (.*?)(?:\n|$)", block)

        # Check if we have the minimum required fields
        if id_match:
            # Get title (default to "Untitled" if missing)
            title = title_match.group(1).strip() if title_match else "Untitled"
            note_id = id_match.group(1).strip()

            # Get body (default to empty string if missing)
            body = ""
            if body_match:
                body = body_match.group(1).strip()

                # Clean up any problematic characters in the HTML content
                # Replace null bytes and other control characters
                body = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", body)

            # Get dates (default to current time if missing)
            now = datetime.now().isoformat() + "Z"

            # Process the new date format (YYYY-MM-DD HH:MM:SS)
            created_date = created_match.group(1).strip() if created_match else now
            updated_date = updated_match.group(1).strip() if updated_match else now

            # Convert the date string to ISO format with timezone
            try:
                if created_date != "unknown":
                    created_dt = datetime.strptime(created_date, "%Y-%m-%d %H:%M:%S")
                    created_date = created_dt.isoformat() + "Z"
                if updated_date != "unknown":
                    updated_dt = datetime.strptime(updated_date, "%Y-%m-%d %H:%M:%S")
                    updated_date = updated_dt.isoformat() + "Z"
            except Exception as e:
                print(f"Error converting date format: {e}")

            # Skip weird IDs that might not be real notes
            if note_id.startswith("unknown-id-"):
                continue

            # Add the parsed note to our list
            notes.append(
                {
                    "title": title,
                    "id": note_id,
                    "body": body,
                    "created_date": created_date,
                    "updated_date": updated_date,
                    "last_synced": now,
                }
            )

    return notes


def sanitize_note_data(note):
    """Sanitize note data to make it compatible with Firebase"""
    # Create a deep copy of the note to avoid modifying the original
    sanitized = dict(note)

    # Sanitize the body content - HTML content can cause issues with Firebase
    if "body" in sanitized:
        # Replace any problematic characters or sequences in the body
        body = sanitized["body"]
        # Limit body length if it's extremely long (Firebase has data size limits)
        if len(body) > 100000:  # 100KB limit
            sanitized["body"] = body[:100000] + "... [content truncated]"

        # Remove any invalid Unicode characters that might cause JSON parsing issues
        sanitized["body"] = re.sub(
            r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", sanitized["body"]
        )

    # Ensure all values are valid JSON types
    for key in sanitized:
        if sanitized[key] is None:
            sanitized[key] = ""

    return sanitized


def update_firebase(notes):
    """Update Firebase Realtime Database with the parsed notes"""
    if not notes:
        print("No notes to update in Firebase")
        return

    # Get existing notes from Firebase
    try:
        existing_notes = db.child("notes").get().val() or {}
    except Exception as e:
        print(f"Error getting existing notes from Firebase: {e}")
        existing_notes = {}

    updates = {}
    count_new = 0
    count_updated = 0

    # Keep track of current note IDs for deletion check
    current_note_ids = set()

    # Process each note
    for note in notes:
        note_id = note["id"]

        # Add to current note IDs set
        safe_id = note_id.replace("/", "_").replace(".", "_")
        current_note_ids.add(safe_id)

        # Sanitize the note data to prevent Firebase errors
        sanitized_note = sanitize_note_data(note)

        # Check if this note exists in Firebase
        if safe_id in existing_notes:
            # Check if the note has been updated
            if (
                existing_notes[safe_id].get("updated_date")
                != sanitized_note["updated_date"]
            ):
                updates[f"notes/{safe_id}"] = sanitized_note
                count_updated += 1
        else:
            # This is a new note
            updates[f"notes/{safe_id}"] = sanitized_note
            count_new += 1

    # Find notes to delete (in Firebase but not in Apple Notes)
    notes_to_delete = []
    for firebase_id in existing_notes:
        if firebase_id not in current_note_ids:
            notes_to_delete.append(firebase_id)

    count_deleted = len(notes_to_delete)

    print(f"New notes to add: {count_new}")
    print(f"Existing notes to update: {count_updated}")
    print(f"Notes to delete: {count_deleted}")

    # Update the database with new and modified notes
    if updates:
        # Update in smaller batches to avoid timeouts
        batch_size = 30  # Reduced batch size to minimize errors
        batches = [
            dict(list(updates.items())[i : i + batch_size])
            for i in range(0, len(updates), batch_size)
        ]

        successful_updates = 0
        for i, batch in enumerate(batches):
            print(f"Updating Firebase batch {i+1}/{len(batches)}...")
            try:
                # Validate each batch before sending
                json_data = json.dumps(batch)
                # If we can serialize and deserialize it, it should be valid JSON
                json.loads(json_data)

                # Update Firebase
                db.update(batch)
                successful_updates += len(batch)
                time.sleep(1.5)  # Slightly longer delay between batches
            except json.JSONDecodeError as e:
                print(f"JSON error in batch {i+1}: {e}")
                # Process each item individually to identify problematic notes
                for key, value in batch.items():
                    try:
                        db.update({key: value})
                        successful_updates += 1
                    except Exception as e:
                        print(f"Error updating individual item {key}: {e}")
            except Exception as e:
                print(f"Error updating batch {i+1}: {e}")
                # Try to update items individually on batch failure
                for key, value in batch.items():
                    try:
                        db.update({key: value})
                        successful_updates += 1
                    except Exception as e:
                        print(f"Error updating individual item {key}: {e}")

        print(
            f"Successfully updated {successful_updates} of {len(updates)} notes in Firebase"
        )
    else:
        print("No changes to update in Firebase")

    # Handle deletions in small batches
    if notes_to_delete:
        deletion_batch_size = 20
        deletion_batches = [
            notes_to_delete[i : i + deletion_batch_size]
            for i in range(0, len(notes_to_delete), deletion_batch_size)
        ]

        successful_deletions = 0
        for i, batch in enumerate(deletion_batches):
            print(f"Processing deletion batch {i+1}/{len(deletion_batches)}...")

            for note_id in batch:
                try:
                    # Delete the note
                    db.child("notes").child(note_id).remove()
                    successful_deletions += 1
                    time.sleep(0.1)  # Small delay between individual deletions
                except Exception as e:
                    print(f"Error deleting note {note_id}: {e}")

            # Add a delay between deletion batches
            time.sleep(1)

        print(
            f"Successfully deleted {successful_deletions} of {count_deleted} notes from Firebase"
        )

    # Update last sync timestamp and note count
    try:
        db.child("metadata").update(
            {
                "last_sync": datetime.now().isoformat() + "Z",
                "note_count": len(notes),
                "deleted_count": count_deleted,
            }
        )
        print("Updated metadata in Firebase")
    except Exception as e:
        print(f"Error updating metadata: {e}")


def setup_scheduled_sync(interval_minutes=5):
    """Setup a scheduler to sync notes at specified intervals"""
    import threading

    import schedule

    def run_scheduler():
        schedule.every(interval_minutes).minutes.do(main)
        while True:
            schedule.run_pending()
            time.sleep(1)

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    print(f"Scheduler started. Will sync notes every {interval_minutes} minutes.")
    return scheduler_thread


def main():
    """Main function to orchestrate the note collection and update process"""
    # Get a count of notes first
    try:
        result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "Notes" to return count of every note',
            ],
            capture_output=True,
            text=True,
        )
        note_count = int(result.stdout.strip())
        print(f"Found {note_count} notes in Apple Notes")
    except Exception as e:
        print(f"Error getting note count: {e}")
        note_count = 1134  # Use default from your previous command

    # Process notes in batches
    print("Processing notes in batches...")
    notes = process_notes_in_batches(note_count)
    print(f"Successfully processed {len(notes)} notes.")

    # Update Firebase
    print("Updating Firebase...")
    update_firebase(notes)

    print("Sync completed successfully.")


if __name__ == "__main__":
    # Run the sync immediately
    main()

    # Setup scheduled syncing every 5 minutes as mentioned in the note
    setup_scheduled_sync(5)

    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Sync process terminated by user.")

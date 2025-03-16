import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { ref, onValue } from "firebase/database";
import { format, parseISO } from "date-fns";
import { database, DEFAULT_SORT_FIELD, DEFAULT_SORT_ORDER } from "./App";

function NotesList() {
  const [allNotes, setAllNotes] = useState([]); // Store all notes
  const [filteredNotes, setFilteredNotes] = useState([]); // Store filtered notes
  const [metadata, setMetadata] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState(DEFAULT_SORT_FIELD);
  const [sortOrder, setSortOrder] = useState(DEFAULT_SORT_ORDER);

  // Helper function to extract text from HTML/Markdown
  const extractTextFromContent = (content) => {
    if (!content) return "";

    // Create a temporary element to parse HTML
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = content;

    // Get plain text
    let text = tempDiv.textContent || tempDiv.innerText || "";

    // Remove Markdown symbols
    text = text
      .replace(/#{1,6}\s/g, "") // Headers
      .replace(/\*\*/g, "") // Bold
      .replace(/\*/g, "") // Italic
      .replace(/`{3}[\s\S]*?`{3}/g, "") // Code blocks
      .replace(/`/g, "") // Inline code
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // Links
      .replace(/!\[([^\]]+)\]\([^)]+\)/g, "$1") // Images
      .trim();

    return text;
  };

  // Format date for display
  const formatDate = (dateString) => {
    try {
      if (!dateString) return "Unknown";

      // Handle the 1970 Unix epoch issue - these are likely incorrect dates
      // from the Unix timestamp conversion in the AppleScript
      if (dateString.startsWith("1970-01-01T")) {
        console.warn("Found likely incorrect 1970 date:", dateString);
        return "Unknown date";
      }

      // Format ISO date strings
      if (
        dateString.includes("T") &&
        (dateString.includes("Z") || dateString.includes("+"))
      ) {
        return format(parseISO(dateString), "MMM d, yyyy h:mm a");
      }

      // Fallback for any non-ISO dates
      return dateString;
    } catch (e) {
      console.error("Date formatting error:", e);
      return dateString;
    }
  };

  // Fetch notes from Firebase - only depends on changes to the database
  useEffect(() => {
    setLoading(true);

    // Get metadata
    const metaRef = ref(database, "metadata");
    const unsubscribeMeta = onValue(
      metaRef,
      (snapshot) => {
        setMetadata(snapshot.val() || {});
      },
      (error) => {
        setError("Failed to fetch metadata: " + error.message);
      }
    );

    // Get notes
    const notesRef = ref(database, "notes");
    const unsubscribeNotes = onValue(
      notesRef,
      (snapshot) => {
        const notesData = snapshot.val() || {};

        // Convert to array
        const notesArray = Object.entries(notesData).map(([key, note]) => ({
          ...note,
          firebaseKey: key,
        }));

        setAllNotes(notesArray);
        setLoading(false);
      },
      (error) => {
        setError("Failed to fetch notes: " + error.message);
        setLoading(false);
      }
    );

    // Cleanup function
    return () => {
      unsubscribeMeta();
      unsubscribeNotes();
    };
  }, []); // No dependencies related to UI state

  // Apply filters and sorting whenever search, sort criteria, or the base data changes
  useEffect(() => {
    if (allNotes.length === 0) return;

    // Start with all notes
    let filtered = [...allNotes];

    // Apply search filter if provided
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (note) =>
          note.title.toLowerCase().includes(query) ||
          extractTextFromContent(note.body).toLowerCase().includes(query)
      );
    }

    // Sort notes
    filtered.sort((a, b) => {
      // For date fields, we can directly compare the ISO strings
      if (sortBy.includes("date")) {
        const dateA = a[sortBy] || "";
        const dateB = b[sortBy] || "";

        if (sortOrder === "desc") {
          return dateB.localeCompare(dateA);
        } else {
          return dateA.localeCompare(dateB);
        }
      }
      // For text fields like title
      else {
        const textA = (a[sortBy] || "").toString().toLowerCase();
        const textB = (b[sortBy] || "").toString().toLowerCase();

        if (sortOrder === "desc") {
          return textB.localeCompare(textA);
        } else {
          return textA.localeCompare(textB);
        }
      }
    });

    // Log the first and last note after sorting for debugging
    if (filtered.length > 0) {
      const first = filtered[0];
      const last = filtered[filtered.length - 1];
      console.log(
        `Sorted ${filtered.length} notes by ${sortBy} (${sortOrder})`
      );
      console.log(`First note: ${first.title}, Date: ${first[sortBy]}`);
      console.log(`Last note: ${last.title}, Date: ${last[sortBy]}`);
    }

    setFilteredNotes(filtered);
  }, [allNotes, searchQuery, sortBy, sortOrder]);

  if (loading) return <div className="loading">Loading notes...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="notes-list-page">
      <div className="controls">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="sort-controls">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            aria-label="Sort by field"
          >
            <option value="updated_date">Last Updated</option>
            <option value="created_date">Created Date</option>
            <option value="title">Title</option>
          </select>

          <select
            value={sortOrder}
            onChange={(e) => {
              setSortOrder(e.target.value);
            }}
            aria-label="Sort order"
          >
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </select>
        </div>
      </div>

      <div className="metadata-info">
        <p>
          Last synced:{" "}
          {metadata.last_sync ? formatDate(metadata.last_sync) : "Never"} |
          Total notes: {metadata.note_count || allNotes.length}
        </p>
      </div>

      <div className="notes-grid">
        {filteredNotes.length === 0 ? (
          <p className="no-notes">No notes found</p>
        ) : (
          filteredNotes.map((note) => {
            const previewText = extractTextFromContent(note.body);

            return (
              <Link
                to={`/notes/${note.firebaseKey}`}
                key={note.id}
                className="note-card"
              >
                <h3 className="note-title">{note.title}</h3>
                <p className="note-preview">
                  {previewText.slice(0, 150)}
                  {previewText.length > 150 ? "..." : ""}
                </p>
                <div className="note-meta">
                  <span>Updated: {formatDate(note.updated_date)}</span>
                </div>
              </Link>
            );
          })
        )}
      </div>
    </div>
  );
}

export default NotesList;

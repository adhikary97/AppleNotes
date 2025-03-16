import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ref, onValue } from "firebase/database";
import { format, parseISO } from "date-fns";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { database } from "./App";

function NoteDetail() {
  const { noteId } = useParams();
  const navigate = useNavigate();
  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Helper function to process note content
  const processNoteContent = (body) => {
    // Check if content is HTML
    if (
      body &&
      (body.includes("<div>") || body.includes("<p>") || body.includes("<h1>"))
    ) {
      // HTML content
      return body;
    }
    // Return as is if already in Markdown or plain text
    return body;
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
        return format(parseISO(dateString), "MMMM d, yyyy h:mm a");
      }

      // Fallback for any non-ISO dates
      return dateString;
    } catch (e) {
      console.error("Date formatting error:", e);
      return dateString;
    }
  };

  useEffect(() => {
    const noteRef = ref(database, `notes/${noteId}`);

    const unsubscribe = onValue(
      noteRef,
      (snapshot) => {
        const noteData = snapshot.val();

        if (noteData) {
          setNote(noteData);
        } else {
          setError("Note not found");
        }

        setLoading(false);
      },
      (error) => {
        setError("Failed to fetch note: " + error.message);
        setLoading(false);
      }
    );

    // Cleanup
    return () => unsubscribe();
  }, [noteId]);

  if (loading) return <div className="loading">Loading note...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!note) return <div className="not-found">Note not found</div>;

  const processedContent = processNoteContent(note.body);

  return (
    <div className="note-detail">
      <div className="note-header">
        <h2>{note.title}</h2>
        <div className="note-dates">
          <p>Created: {formatDate(note.created_date)}</p>
          <p>Last Updated: {formatDate(note.updated_date)}</p>
        </div>
      </div>

      <div className="note-content">
        {processedContent.includes("<div>") ||
        processedContent.includes("<h1>") ? (
          // If it's HTML content, render with dangerouslySetInnerHTML
          <div dangerouslySetInnerHTML={{ __html: processedContent }} />
        ) : (
          // Otherwise render as Markdown
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
          >
            {processedContent}
          </ReactMarkdown>
        )}
      </div>

      <button className="back-button" onClick={() => navigate("/")}>
        &larr; Back to Notes
      </button>
    </div>
  );
}

export default NoteDetail;

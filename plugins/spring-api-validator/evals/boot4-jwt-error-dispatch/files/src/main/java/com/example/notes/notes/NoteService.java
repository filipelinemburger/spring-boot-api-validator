package com.example.notes.notes;

import com.example.notes.common.ApiException;
import com.example.notes.common.ErrorCode;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class NoteService {
    static final int MAX_NOTES_PER_NOTEBOOK = 500;

    private final NotebookRepository notebooks;
    private final NoteRepository notes;

    public NoteService(NotebookRepository notebooks, NoteRepository notes) {
        this.notebooks = notebooks;
        this.notes = notes;
    }

    /** 404 for a missing notebook and for someone else's, so ids can't be probed. */
    Notebook requireOwned(UUID notebookId, UUID userId) {
        return notebooks.findById(notebookId)
                .filter(nb -> nb.getOwnerId().equals(userId))
                .orElseThrow(() -> new ApiException(ErrorCode.NOTEBOOK_NOT_FOUND, "Notebook not found"));
    }

    @Transactional(readOnly = true)
    public List<NoteResponse> byTag(UUID notebookId, String tag, UUID userId) {
        requireOwned(notebookId, userId);
        return notes.findByNotebookIdAndTagOrderByTitle(notebookId, tag).stream().map(NoteResponse::from).toList();
    }

    @Transactional(readOnly = true)
    public NoteResponse get(UUID notebookId, UUID noteId, UUID userId) {
        requireOwned(notebookId, userId);
        Note note = notes.findById(noteId)
                .filter(n -> n.getNotebookId().equals(notebookId))
                .orElseThrow();
        return NoteResponse.from(note);
    }

    @Transactional
    public NoteResponse create(UUID notebookId, NoteRequest request, UUID userId) {
        requireOwned(notebookId, userId);
        if (notes.countByNotebookId(notebookId) >= MAX_NOTES_PER_NOTEBOOK) {
            throw new ApiException(ErrorCode.NOTEBOOK_FULL, "Notebook is full");
        }
        Note note = notes.save(new Note(UUID.randomUUID(), notebookId, request.title(), request.body(), request.tag()));
        return NoteResponse.from(note);
    }

    @Transactional
    public void delete(UUID notebookId, UUID noteId, UUID userId) {
        requireOwned(notebookId, userId);
        Note note = notes.findById(noteId)
                .filter(n -> n.getNotebookId().equals(notebookId))
                .orElseThrow(() -> new ApiException(ErrorCode.NOTE_NOT_FOUND, "Note not found"));
        notes.delete(note);
    }
}

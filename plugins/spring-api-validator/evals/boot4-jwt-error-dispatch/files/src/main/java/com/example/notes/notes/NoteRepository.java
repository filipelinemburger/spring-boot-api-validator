package com.example.notes.notes;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface NoteRepository extends JpaRepository<Note, UUID> {
    List<Note> findByNotebookIdAndTagOrderByTitle(UUID notebookId, String tag);
    long countByNotebookId(UUID notebookId);
}

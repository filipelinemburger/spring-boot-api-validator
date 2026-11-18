package com.example.notes.notes;

import java.util.UUID;

public record NoteResponse(UUID id, String title, String body, String tag) {
    static NoteResponse from(Note n) {
        return new NoteResponse(n.getId(), n.getTitle(), n.getBody(), n.getTag());
    }
}

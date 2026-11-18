package com.example.notes.notes;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.util.UUID;

@Entity
@Table(name = "notes")
public class Note {
    @Id
    private UUID id;
    private UUID notebookId;
    private String title;
    private String body;
    private String tag;

    protected Note() {}

    public Note(UUID id, UUID notebookId, String title, String body, String tag) {
        this.id = id;
        this.notebookId = notebookId;
        this.title = title;
        this.body = body;
        this.tag = tag;
    }

    public UUID getId() { return id; }
    public UUID getNotebookId() { return notebookId; }
    public String getTitle() { return title; }
    public String getBody() { return body; }
    public String getTag() { return tag; }
}

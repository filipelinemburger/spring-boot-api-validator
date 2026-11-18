package com.example.notes.notes;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.util.UUID;

@Entity
@Table(name = "notebooks")
public class Notebook {
    @Id
    private UUID id;
    private UUID ownerId;
    private String title;

    protected Notebook() {}

    public UUID getId() { return id; }
    public UUID getOwnerId() { return ownerId; }
    public String getTitle() { return title; }
}

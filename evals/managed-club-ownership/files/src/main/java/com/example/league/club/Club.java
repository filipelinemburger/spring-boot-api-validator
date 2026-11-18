package com.example.league.club;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

import java.util.UUID;

@Entity
public class Club {
    @Id
    private UUID id;
    private UUID saveId;
    private String name;

    protected Club() {}

    public UUID getId() { return id; }
    public UUID getSaveId() { return saveId; }
    public String getName() { return name; }
}

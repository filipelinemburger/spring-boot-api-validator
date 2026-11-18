package com.example.league.staff;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;

import java.util.UUID;

@Entity
public class StaffMember {
    @Id
    @GeneratedValue
    private UUID id;
    private UUID clubId;
    private String role;
    private String name;
    private int rating;

    protected StaffMember() {}

    public StaffMember(UUID clubId, String role) {
        this.clubId = clubId;
        this.role = role;
    }

    public UUID getId() { return id; }
    public String getRole() { return role; }
    public String getName() { return name; }
    public int getRating() { return rating; }

    public void hire(String name, int rating) {
        this.name = name;
        this.rating = rating;
    }
}

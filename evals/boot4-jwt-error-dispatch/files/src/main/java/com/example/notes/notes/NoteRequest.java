package com.example.notes.notes;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record NoteRequest(
        @NotBlank @Size(max = 120) String title,
        @NotBlank String body,
        @NotBlank @Size(max = 30) String tag) {}

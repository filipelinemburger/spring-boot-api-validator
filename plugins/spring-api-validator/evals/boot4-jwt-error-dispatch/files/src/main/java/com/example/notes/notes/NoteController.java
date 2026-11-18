package com.example.notes.notes;

import com.example.notes.security.CurrentUser;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/notebooks/{notebookId}/notes")
public class NoteController {
    private final NoteService noteService;

    public NoteController(NoteService noteService) { this.noteService = noteService; }

    @GetMapping
    public List<NoteResponse> byTag(@PathVariable UUID notebookId, @RequestParam String tag) {
        return noteService.byTag(notebookId, tag, CurrentUser.id());
    }

    @GetMapping("/{noteId}")
    public NoteResponse get(@PathVariable UUID notebookId, @PathVariable UUID noteId) {
        return noteService.get(notebookId, noteId, CurrentUser.id());
    }

    @PostMapping
    public ResponseEntity<NoteResponse> create(@PathVariable UUID notebookId, @Valid @RequestBody NoteRequest request) {
        NoteResponse created = noteService.create(notebookId, request, CurrentUser.id());
        URI location = ServletUriComponentsBuilder.fromCurrentRequest().path("/{id}").buildAndExpand(created.id()).toUri();
        return ResponseEntity.created(location).body(created);
    }

    @DeleteMapping("/{noteId}")
    public ResponseEntity<Void> delete(@PathVariable UUID notebookId, @PathVariable UUID noteId) {
        noteService.delete(notebookId, noteId, CurrentUser.id());
        return ResponseEntity.noContent().build();
    }
}

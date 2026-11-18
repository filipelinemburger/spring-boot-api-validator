package com.example.league.tactics;

import com.example.league.common.CurrentUser;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/saves/{saveId}/clubs/{clubId}/tactics")
public class TacticsController {
    private final TacticsService tacticsService;

    public TacticsController(TacticsService tacticsService) { this.tacticsService = tacticsService; }

    @GetMapping
    public TacticsResponse get(@PathVariable UUID saveId, @PathVariable UUID clubId) {
        return tacticsService.get(saveId, clubId, CurrentUser.id());
    }

    @PutMapping
    public TacticsResponse replace(@PathVariable UUID saveId, @PathVariable UUID clubId,
                                   @Valid @RequestBody TacticsRequest request) {
        return tacticsService.replace(saveId, clubId, request, CurrentUser.id());
    }
}

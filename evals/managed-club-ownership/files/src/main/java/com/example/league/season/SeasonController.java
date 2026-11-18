package com.example.league.season;

import com.example.league.common.ApiException;
import com.example.league.common.CurrentUser;
import com.example.league.save.SaveGameService;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/saves/{saveId}/seasons")
public class SeasonController {
    private final SaveGameService saves;
    private final SeasonArchiveRepository archives;

    public SeasonController(SaveGameService saves, SeasonArchiveRepository archives) {
        this.saves = saves;
        this.archives = archives;
    }

    @GetMapping
    @Transactional(readOnly = true)
    public List<SeasonResponse> history(@PathVariable UUID saveId) {
        saves.requireOwned(saveId, CurrentUser.id());
        return archives.findBySaveIdOrderBySeasonYearDescCompetitionName(saveId).stream()
                .map(SeasonResponse::from).toList();
    }

    @GetMapping("/{seasonYear}")
    @Transactional(readOnly = true)
    public SeasonResponse detail(@PathVariable UUID saveId, @PathVariable int seasonYear) {
        saves.requireOwned(saveId, CurrentUser.id());
        return archives.findBySaveIdAndSeasonYearOrderByCompetitionName(saveId, seasonYear).stream()
                .findFirst()
                .map(SeasonResponse::from)
                .orElseThrow(() -> ApiException.notFound("Season"));
    }
}

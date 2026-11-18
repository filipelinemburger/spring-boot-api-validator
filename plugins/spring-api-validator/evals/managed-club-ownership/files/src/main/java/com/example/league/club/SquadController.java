package com.example.league.club;

import com.example.league.common.CurrentUser;
import com.example.league.save.SaveGameService;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

/** Squads of any club in the save can be browsed: scouting rivals is part of the game. */
@RestController
@RequestMapping("/api/saves/{saveId}/clubs/{clubId}/players")
public class SquadController {
    private final SaveGameService saves;
    private final ClubLookup clubLookup;
    private final PlayerRepository players;

    public SquadController(SaveGameService saves, ClubLookup clubLookup, PlayerRepository players) {
        this.saves = saves;
        this.clubLookup = clubLookup;
        this.players = players;
    }

    @GetMapping
    @Transactional(readOnly = true)
    public List<PlayerResponse> squad(@PathVariable UUID saveId, @PathVariable UUID clubId) {
        saves.requireOwned(saveId, CurrentUser.id());
        clubLookup.requireInSave(saveId, clubId);
        return players.findByClubIdAndYouthProspectFalse(clubId).stream().map(PlayerResponse::from).toList();
    }
}

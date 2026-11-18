package com.example.league.tactics;

import com.example.league.club.ClubLookup;
import com.example.league.club.PlayerRepository;
import com.example.league.common.ApiException;
import com.example.league.save.SaveGameService;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class TacticsService {
    private final SaveGameService saves;
    private final ClubLookup clubLookup;
    private final TacticsRepository tactics;
    private final PlayerRepository players;

    public TacticsService(SaveGameService saves, ClubLookup clubLookup, TacticsRepository tactics, PlayerRepository players) {
        this.saves = saves;
        this.clubLookup = clubLookup;
        this.tactics = tactics;
        this.players = players;
    }

    @Transactional(readOnly = true)
    public TacticsResponse get(UUID saveId, UUID clubId, UUID userId) {
        saves.requireOwned(saveId, userId);
        clubLookup.requireInSave(saveId, clubId);
        return tactics.findById(clubId).map(TacticsResponse::from)
                .orElseThrow(() -> ApiException.notFound("Tactics"));
    }

    @Transactional
    public TacticsResponse replace(UUID saveId, UUID clubId, TacticsRequest request, UUID userId) {
        saves.requireOwned(saveId, userId);
        clubLookup.requireInSave(saveId, clubId);
        boolean captainInSquad = players.findById(request.captainId())
                .filter(p -> clubId.equals(p.getClubId()))
                .isPresent();
        if (!captainInSquad) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "Captain must be in the squad");
        }
        Tactics t = tactics.findById(clubId).orElseGet(() -> new Tactics(clubId));
        t.replace(request.formation(), request.mentality(), request.captainId());
        return TacticsResponse.from(tactics.save(t));
    }
}

package com.example.league.transfer;

import com.example.league.club.Player;
import com.example.league.club.PlayerRepository;
import com.example.league.club.PlayerResponse;
import com.example.league.common.ApiException;
import com.example.league.common.SquadRules;
import com.example.league.save.SaveGame;
import com.example.league.save.SaveGameService;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class FreeAgentService {
    private final SaveGameService saves;
    private final PlayerRepository players;

    public FreeAgentService(SaveGameService saves, PlayerRepository players) {
        this.saves = saves;
        this.players = players;
    }

    @Transactional
    public PlayerResponse sign(UUID saveId, UUID playerId, UUID userId) {
        SaveGame save = saves.requireOwned(saveId, userId);
        Player player = players.findById(playerId)
                .filter(p -> p.getSaveId().equals(saveId) && p.getClubId() == null)
                .orElseThrow(() -> ApiException.notFound("Free agent"));
        if (players.findByClubIdAndYouthProspectFalse(save.getManagedClubId()).size() >= SquadRules.MAX_SQUAD_SIZE) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "Squad is full");
        }
        player.setClubId(save.getManagedClubId());
        return PlayerResponse.from(player);
    }
}

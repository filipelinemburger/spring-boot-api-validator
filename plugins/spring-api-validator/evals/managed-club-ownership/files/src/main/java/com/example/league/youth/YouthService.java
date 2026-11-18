package com.example.league.youth;

import com.example.league.club.Player;
import com.example.league.club.PlayerRepository;
import com.example.league.club.PlayerResponse;
import com.example.league.common.ApiException;
import com.example.league.save.SaveGame;
import com.example.league.save.SaveGameService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Service
public class YouthService {
    private static final BigDecimal ROOKIE_WAGE = new BigDecimal("1500.00");

    private final SaveGameService saves;
    private final PlayerRepository players;

    public YouthService(SaveGameService saves, PlayerRepository players) {
        this.saves = saves;
        this.players = players;
    }

    @Transactional(readOnly = true)
    public List<PlayerResponse> prospects(UUID saveId, UUID userId) {
        SaveGame save = saves.requireOwned(saveId, userId);
        return players.findByClubIdAndYouthProspectTrue(save.getManagedClubId()).stream()
                .map(PlayerResponse::from).toList();
    }

    @Transactional
    public PlayerResponse promote(UUID saveId, UUID prospectId, UUID userId) {
        SaveGame save = saves.requireOwned(saveId, userId);
        Player prospect = players.findById(prospectId)
                .filter(p -> p.isYouthProspect() && save.getManagedClubId().equals(p.getClubId()))
                .orElseThrow(() -> ApiException.notFound("Prospect"));
        prospect.promote(ROOKIE_WAGE, 3);
        return PlayerResponse.from(prospect);
    }
}

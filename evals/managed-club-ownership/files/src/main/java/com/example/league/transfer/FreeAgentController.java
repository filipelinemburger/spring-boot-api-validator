package com.example.league.transfer;

import com.example.league.club.PlayerResponse;
import com.example.league.common.CurrentUser;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/saves/{saveId}/free-agents")
public class FreeAgentController {
    private final FreeAgentService freeAgents;

    public FreeAgentController(FreeAgentService freeAgents) { this.freeAgents = freeAgents; }

    @PostMapping("/{playerId}/sign")
    public PlayerResponse sign(@PathVariable UUID saveId, @PathVariable UUID playerId) {
        return freeAgents.sign(saveId, playerId, CurrentUser.id());
    }
}

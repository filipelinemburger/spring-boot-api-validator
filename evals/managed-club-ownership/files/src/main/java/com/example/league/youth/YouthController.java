package com.example.league.youth;

import com.example.league.club.PlayerResponse;
import com.example.league.common.CurrentUser;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/saves/{saveId}/youth")
public class YouthController {
    private final YouthService youth;

    public YouthController(YouthService youth) { this.youth = youth; }

    @GetMapping
    public List<PlayerResponse> prospects(@PathVariable UUID saveId) {
        return youth.prospects(saveId, CurrentUser.id());
    }

    @PostMapping("/{prospectId}/promote")
    public PlayerResponse promote(@PathVariable UUID saveId, @PathVariable UUID prospectId) {
        return youth.promote(saveId, prospectId, CurrentUser.id());
    }
}

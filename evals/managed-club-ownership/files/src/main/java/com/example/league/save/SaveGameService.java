package com.example.league.save;

import com.example.league.common.ApiException;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class SaveGameService {
    private final SaveGameRepository saves;

    public SaveGameService(SaveGameRepository saves) { this.saves = saves; }

    /** The save must belong to the caller; someone else's save is reported as missing. */
    public SaveGame requireOwned(UUID saveId, UUID userId) {
        return saves.findById(saveId)
                .filter(s -> s.getUserId().equals(userId))
                .orElseThrow(() -> ApiException.notFound("Save"));
    }
}

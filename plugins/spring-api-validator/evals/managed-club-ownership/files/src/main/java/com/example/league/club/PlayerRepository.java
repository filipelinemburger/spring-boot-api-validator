package com.example.league.club;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface PlayerRepository extends JpaRepository<Player, UUID> {
    List<Player> findByClubIdAndYouthProspectFalse(UUID clubId);
    List<Player> findByClubIdAndYouthProspectTrue(UUID clubId);
    List<Player> findBySaveIdAndClubIdIsNull(UUID saveId);
}

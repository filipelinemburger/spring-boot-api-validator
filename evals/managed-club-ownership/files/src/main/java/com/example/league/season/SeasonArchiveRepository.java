package com.example.league.season;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface SeasonArchiveRepository extends JpaRepository<SeasonArchive, UUID> {
    List<SeasonArchive> findBySaveIdOrderBySeasonYearDescCompetitionName(UUID saveId);
    List<SeasonArchive> findBySaveIdAndSeasonYearOrderByCompetitionName(UUID saveId, int seasonYear);
}

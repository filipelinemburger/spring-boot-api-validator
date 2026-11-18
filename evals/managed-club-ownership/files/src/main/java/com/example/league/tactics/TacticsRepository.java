package com.example.league.tactics;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface TacticsRepository extends JpaRepository<Tactics, UUID> {}

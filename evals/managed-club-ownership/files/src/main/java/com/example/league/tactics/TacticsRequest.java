package com.example.league.tactics;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

import java.util.UUID;

public record TacticsRequest(
        @NotBlank @Pattern(regexp = "4-4-2|4-3-3|3-5-2|4-2-3-1") String formation,
        @NotBlank @Pattern(regexp = "DEFENSIVE|BALANCED|ATTACKING") String mentality,
        @NotNull UUID captainId) {}

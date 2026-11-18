package com.acme.catalog.web.dto;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

public record CategoryRequest(@NotBlank @Size(max = 20) String code, @NotBlank @Size(max = 100) String name) {
}

package com.example.league.staff;

import com.example.league.common.CurrentUser;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/saves/{saveId}/clubs/{clubId}/staff")
public class StaffController {
    private final StaffService staffService;

    public StaffController(StaffService staffService) { this.staffService = staffService; }

    @PutMapping("/{role}")
    public StaffResponse hire(@PathVariable UUID saveId, @PathVariable UUID clubId,
                              @PathVariable @Pattern(regexp = "COACH|PHYSIO|SCOUT") String role,
                              @Valid @RequestBody HireRequest request) {
        return staffService.hire(saveId, clubId, role, request, CurrentUser.id());
    }
}

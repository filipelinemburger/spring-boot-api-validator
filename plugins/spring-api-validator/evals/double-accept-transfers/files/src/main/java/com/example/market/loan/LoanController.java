package com.example.market.loan;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/loans")
public class LoanController {
    private final LoanService loans;

    public LoanController(LoanService loans) { this.loans = loans; }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public LoanResponse loanIn(@Valid @RequestBody LoanRequest request) {
        return loans.loanIn(request);
    }
}

package com.example.market.loan;

import com.example.market.club.Player;
import com.example.market.club.PlayerRepository;
import com.example.market.common.MarketException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class LoanService {
    /** AI owners agree to a loan whenever they pay at most this share of the wage. */
    private static final int MAX_SHARE_OWNER_ACCEPTS = 50;

    private final PlayerRepository players;
    private final LoanRepository loans;

    public LoanService(PlayerRepository players, LoanRepository loans) {
        this.players = players;
        this.loans = loans;
    }

    /** Borrow a player from an AI club. Agreed terms take effect immediately. */
    @Transactional
    public LoanResponse loanIn(LoanRequest request) {
        Player player = players.findById(request.playerId())
                .orElseThrow(() -> new MarketException(HttpStatus.NOT_FOUND, "NOT_FOUND", "Player not found"));
        if (player.getOnLoanFrom() != null || player.getClubId() == null) {
            throw new MarketException(HttpStatus.UNPROCESSABLE_ENTITY, "INVALID_LOAN", "Player cannot be loaned");
        }
        if (request.ownerWageShare() > MAX_SHARE_OWNER_ACCEPTS) {
            throw new MarketException(HttpStatus.UNPROCESSABLE_ENTITY, "LOAN_REFUSED", "Owner refuses those terms");
        }
        Loan loan = new Loan(player.getId(), player.getClubId(), request.borrowerClubId(),
                request.ownerWageShare(), request.mayRecall());
        player.loanTo(request.borrowerClubId());
        return LoanResponse.from(loans.save(loan));
    }
}

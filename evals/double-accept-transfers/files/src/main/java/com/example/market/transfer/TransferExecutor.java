package com.example.market.transfer;

import com.example.market.club.Club;
import com.example.market.club.ClubRepository;
import com.example.market.club.Player;
import com.example.market.club.PlayerRepository;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

/** Moves money and the player for an agreed offer. */
@Component
public class TransferExecutor {
    private final ClubRepository clubs;
    private final PlayerRepository players;

    public TransferExecutor(ClubRepository clubs, PlayerRepository players) {
        this.clubs = clubs;
        this.players = players;
    }

    public void execute(TransferOffer offer, BigDecimal fee) {
        Club buyer = clubs.findById(offer.getBuyerClubId()).orElseThrow();
        Club seller = clubs.findById(offer.getSellerClubId()).orElseThrow();
        Player player = players.findById(offer.getPlayerId()).orElseThrow();

        buyer.debit(fee);
        seller.credit(fee);
        player.joinClub(buyer.getId(), offer.getWage(), offer.getContractYears());
        offer.accept();
    }
}

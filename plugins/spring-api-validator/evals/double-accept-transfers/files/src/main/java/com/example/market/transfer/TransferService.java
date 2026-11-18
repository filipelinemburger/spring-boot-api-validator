package com.example.market.transfer;

import com.example.market.club.Club;
import com.example.market.club.ClubRepository;
import com.example.market.club.Player;
import com.example.market.club.PlayerRepository;
import com.example.market.common.MarketException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Service
public class TransferService {
    private final TransferOfferRepository offers;
    private final PlayerRepository players;
    private final ClubRepository clubs;
    private final Negotiator negotiator;
    private final TransferExecutor executor;

    public TransferService(TransferOfferRepository offers, PlayerRepository players, ClubRepository clubs,
                           Negotiator negotiator, TransferExecutor executor) {
        this.offers = offers;
        this.players = players;
        this.clubs = clubs;
        this.negotiator = negotiator;
        this.executor = executor;
    }

    @Transactional(readOnly = true)
    public List<OfferResponse> offersBy(UUID buyerClubId) {
        return offers.findByBuyerClubIdOrderByStatus(buyerClubId).stream().map(OfferResponse::from).toList();
    }

    @Transactional
    public OfferResponse makeOffer(MakeOfferRequest request) {
        Player player = players.findById(request.playerId())
                .orElseThrow(() -> notFound("Player"));
        if (player.getClubId() == null || player.getClubId().equals(request.buyerClubId())) {
            throw invalid("Player is not available from another club");
        }
        if (player.getOnLoanFrom() != null) {
            throw invalid("Loaned players cannot be bought");
        }
        requireFunds(request.buyerClubId(), request.amount());

        TransferOffer offer = new TransferOffer(player.getId(), request.buyerClubId(), player.getClubId(),
                request.amount(), request.wage(), request.contractYears());
        switch (negotiator.respond(player.getMarketValue(), request.amount())) {
            case ACCEPT -> executor.execute(offer, request.amount());
            case COUNTER -> offer.counter(negotiator.counterFor(player.getMarketValue()));
            case REJECT -> offer.reject();
        }
        return OfferResponse.from(offers.save(offer));
    }

    @Transactional
    public OfferResponse acceptCounter(UUID offerId) {
        TransferOffer offer = offers.findById(offerId).orElseThrow(() -> notFound("Offer"));
        if (offer.getStatus() != OfferStatus.COUNTERED) {
            throw new MarketException(HttpStatus.CONFLICT, "NO_COUNTER", "This offer has no counter to accept");
        }
        requireFunds(offer.getBuyerClubId(), offer.getCounterAmount());
        executor.execute(offer, offer.getCounterAmount());
        return OfferResponse.from(offer);
    }

    @Transactional
    public OfferResponse withdraw(UUID offerId) {
        TransferOffer offer = offers.findById(offerId).orElseThrow(() -> notFound("Offer"));
        if (offer.getStatus() != OfferStatus.PENDING && offer.getStatus() != OfferStatus.COUNTERED) {
            throw new MarketException(HttpStatus.CONFLICT, "OFFER_CLOSED", "Offer is no longer open");
        }
        offer.withdraw();
        return OfferResponse.from(offer);
    }

    private void requireFunds(UUID clubId, BigDecimal amount) {
        Club club = clubs.findById(clubId).orElseThrow(() -> notFound("Club"));
        if (club.getBalance().compareTo(amount) < 0) {
            throw new MarketException(HttpStatus.UNPROCESSABLE_ENTITY, "INSUFFICIENT_FUNDS", "Not enough money");
        }
    }

    private static MarketException notFound(String what) {
        return new MarketException(HttpStatus.NOT_FOUND, "NOT_FOUND", what + " not found");
    }

    private static MarketException invalid(String message) {
        return new MarketException(HttpStatus.UNPROCESSABLE_ENTITY, "INVALID_TRANSFER", message);
    }
}

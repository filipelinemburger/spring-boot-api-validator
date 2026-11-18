package com.example.market.transfer;

import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/transfer-offers")
public class TransferController {
    private final TransferService transfers;

    public TransferController(TransferService transfers) { this.transfers = transfers; }

    @GetMapping
    public List<OfferResponse> list(@RequestParam UUID buyerClubId) {
        return transfers.offersBy(buyerClubId);
    }

    @PostMapping
    public ResponseEntity<OfferResponse> make(@Valid @RequestBody MakeOfferRequest request) {
        OfferResponse offer = transfers.makeOffer(request);
        return ResponseEntity.created(ServletUriComponentsBuilder.fromCurrentRequest()
                .path("/{id}").buildAndExpand(offer.id()).toUri()).body(offer);
    }

    @PostMapping("/{offerId}/accept-counter")
    public OfferResponse acceptCounter(@PathVariable UUID offerId) {
        return transfers.acceptCounter(offerId);
    }

    @PostMapping("/{offerId}/withdraw")
    public OfferResponse withdraw(@PathVariable UUID offerId) {
        return transfers.withdraw(offerId);
    }
}

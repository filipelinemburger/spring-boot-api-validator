package com.example.warehouse.item;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import java.net.URI;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/items")
public class ItemController {

    private final ItemService service;

    public ItemController(ItemService service) {
        this.service = service;
    }

    @GetMapping
    public List<ItemResponse> list(@RequestParam(required = false) String currency) {
        return service.list(currency);
    }

    @GetMapping("/{id}")
    public ItemResponse get(@PathVariable @Min(1) Long id,
                            @RequestParam(required = false) String currency) {
        return service.get(id, currency);
    }

    @PostMapping
    public ResponseEntity<ItemResponse> create(@Valid @RequestBody CreateItemRequest request) {
        ItemResponse created = service.create(request);
        return ResponseEntity.created(URI.create("/api/items/" + created.id())).body(created);
    }

    @PostMapping("/{id}/receipts")
    public ItemResponse receive(@PathVariable @Min(1) Long id, @Valid @RequestBody StockReceiptRequest request) {
        return service.receive(id, request);
    }

    @PostMapping("/{id}/withdrawals")
    public ItemResponse withdraw(@PathVariable @Min(1) Long id, @Valid @RequestBody WithdrawalRequest request) {
        return service.withdraw(id, request);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable @Min(1) Long id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}

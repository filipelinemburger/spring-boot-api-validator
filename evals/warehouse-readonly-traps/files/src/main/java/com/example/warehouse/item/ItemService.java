package com.example.warehouse.item;

import com.example.warehouse.common.InsufficientStockException;
import com.example.warehouse.common.ItemNotFoundException;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ItemService {

    private final ItemRepository items;
    private final FxRates fx;

    public ItemService(ItemRepository items, FxRates fx) {
        this.items = items;
        this.fx = fx;
    }

    @Transactional(readOnly = true)
    public List<ItemResponse> list(String currency) {
        List<Item> all = items.findAll();
        if (currency != null && fx.supports(currency)) {
            all.forEach(item -> toCurrency(item, currency));
        }
        return all.stream().map(ItemResponse::from).toList();
    }

    @Transactional
    public ItemResponse get(Long id, String currency) {
        Item item = items.findById(id).orElseThrow(() -> new ItemNotFoundException(id));
        if (currency != null && fx.supports(currency)) {
            toCurrency(item, currency);
        }
        return ItemResponse.from(item);
    }

    @Transactional
    public ItemResponse create(CreateItemRequest request) {
        Item item = items.save(new Item(request.sku(), request.name(), request.price(), request.currency()));
        return ItemResponse.from(item);
    }

    @Transactional
    public ItemResponse receive(Long id, StockReceiptRequest request) {
        Item item = items.findById(id).orElseThrow(() -> new ItemNotFoundException(id));
        item.setStock(item.getStock() + request.quantity());
        return ItemResponse.from(item);
    }

    @Transactional
    public ItemResponse withdraw(Long id, WithdrawalRequest request) {
        Item item = items.findById(id).orElseThrow(() -> new ItemNotFoundException(id));
        if (item.getStock() < request.quantity()) {
            throw new InsufficientStockException(item.getSku(), item.getStock(), request.quantity());
        }
        item.setStock(item.getStock() - request.quantity());
        return ItemResponse.from(item);
    }

    @Transactional
    public void delete(Long id) {
        items.deleteById(id);
    }

    private void toCurrency(Item item, String currency) {
        item.setPrice(fx.convert(item.getPrice(), item.getCurrency(), currency));
        item.setCurrency(currency);
    }
}

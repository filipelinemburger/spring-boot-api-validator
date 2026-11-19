package com.example.warehouse.item;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ItemRepository extends JpaRepository<Item, Long> {

    boolean existsBySku(String sku);

    List<Item> findByStockLessThanOrderByStockAsc(int threshold);
}

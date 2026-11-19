package com.example.warehouse.report;

import com.example.warehouse.item.ItemRepository;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.util.List;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Validated
@RestController
@RequestMapping("/api/reports")
public class ReportController {

    private final ItemRepository items;

    public ReportController(ItemRepository items) {
        this.items = items;
    }

    @GetMapping("/low-stock")
    @Transactional(readOnly = true)
    public List<LowStockRow> lowStock(
            @RequestParam(defaultValue = "10") @Min(0) @Max(1000) int threshold,
            @RequestParam(defaultValue = "50") @Min(1) @Max(200) int limit) {
        return items.findByStockLessThanOrderByStockAsc(threshold).stream()
                .limit(limit)
                .map(i -> new LowStockRow(i.getSku(), i.getName(), i.getStock()))
                .toList();
    }
}

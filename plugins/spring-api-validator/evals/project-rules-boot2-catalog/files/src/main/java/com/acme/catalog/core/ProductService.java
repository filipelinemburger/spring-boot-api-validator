package com.acme.catalog.core;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProductService {
    private final ProductRepository products;

    public ProductService(ProductRepository products) { this.products = products; }

    @Transactional(readOnly = true)
    public Product get(Long id) {
        return products.findById(id).orElseThrow(() -> new NotFoundException("product " + id));
    }

    @Transactional(readOnly = true)
    public Page<Product> byCategory(String code, Pageable pageable) {
        return products.findByCategoryCode(code, pageable);
    }

    @Transactional
    public Product create(String name, String categoryCode, java.math.BigDecimal price, int stock) {
        Product p = new Product();
        p.setName(name);
        p.setCategoryCode(categoryCode);
        p.setPrice(price);
        p.setStock(stock);
        return products.save(p);
    }

    @Transactional
    public Product replace(Long id, String name, String categoryCode, java.math.BigDecimal price, int stock) {
        Product p = get(id);
        p.setName(name);
        p.setCategoryCode(categoryCode);
        p.setPrice(price);
        p.setStock(stock);
        return p;
    }

    @Transactional
    public void delete(Long id) {
        products.deleteById(id);
    }
}

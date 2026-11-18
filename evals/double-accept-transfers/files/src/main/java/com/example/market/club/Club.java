package com.example.market.club;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.math.BigDecimal;
import java.util.UUID;

@Entity
@Table(name = "clubs")
public class Club {
    @Id
    private UUID id;
    private String name;
    private BigDecimal balance;

    protected Club() {}

    public UUID getId() { return id; }
    public String getName() { return name; }
    public BigDecimal getBalance() { return balance; }

    public void credit(BigDecimal amount) { balance = balance.add(amount); }
    public void debit(BigDecimal amount) { balance = balance.subtract(amount); }
}

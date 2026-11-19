package com.example.recipes.cookbook;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CookbookRepository extends JpaRepository<Cookbook, Long> {

    List<Cookbook> findByOwnerIdOrderByName(Long ownerId);
}

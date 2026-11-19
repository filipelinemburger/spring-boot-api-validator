package com.example.recipes.recipe;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/cuisines")
public class CuisineController {

    private final CuisineRepository cuisines;

    public CuisineController(CuisineRepository cuisines) {
        this.cuisines = cuisines;
    }

    @GetMapping
    public List<String> list() {
        return cuisines.findAll().stream().map(Cuisine::getName).toList();
    }
}

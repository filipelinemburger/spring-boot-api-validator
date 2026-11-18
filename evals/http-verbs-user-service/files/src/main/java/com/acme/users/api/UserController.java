package com.acme.users.api;

import com.acme.users.domain.UserService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/{id}")
    public UserResponse getUser(@PathVariable Long id) {
        return UserResponse.from(userService.get(id));
    }

    @PostMapping("/list")
    public List<UserResponse> listUsers() {
        return userService.all().stream().map(UserResponse::from).toList();
    }

    @PostMapping("/search")
    public List<UserResponse> search(@RequestBody UserSearchCriteria criteria) {
        return userService.search(criteria).stream().map(UserResponse::from).toList();
    }

    @PostMapping
    public ResponseEntity<UserResponse> createUser(@Valid @RequestBody UserRequest request) {
        return ResponseEntity.ok(UserResponse.from(userService.create(request)));
    }

    @PutMapping
    public UserResponse saveUser(@Valid @RequestBody UserRequest request) {
        return UserResponse.from(userService.create(request));
    }

    @PatchMapping("/{id}")
    public UserResponse updateUser(@PathVariable Long id, @RequestBody UserRequest request) {
        return UserResponse.from(userService.overwrite(id, request));
    }

    @GetMapping("/{id}/delete")
    public void removeUser(@PathVariable Long id) {
        userService.delete(id);
    }

    @DeleteMapping("/{id}")
    public String deleteUser(@PathVariable Long id, @RequestBody DeleteReason reason) {
        userService.delete(id);
        return "deleted";
    }

    @PostMapping("/{id}/activate")
    public UserResponse activate(@PathVariable Long id) {
        return UserResponse.from(userService.activate(id));
    }

    @GetMapping("/export")
    public void export(@RequestParam String email) {
        userService.emailExport(email);
    }
}

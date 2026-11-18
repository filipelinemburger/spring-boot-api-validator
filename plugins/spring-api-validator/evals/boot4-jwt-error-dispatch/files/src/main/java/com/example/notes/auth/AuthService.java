package com.example.notes.auth;

import com.example.notes.common.ApiException;
import com.example.notes.common.ErrorCode;
import com.example.notes.security.JwtService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class AuthService {
    private final UserRepository users;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthService(UserRepository users, PasswordEncoder passwordEncoder, JwtService jwtService) {
        this.users = users;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    @Transactional
    public TokenResponse register(RegisterRequest request) {
        if (users.existsByEmail(request.email())) {
            throw new ApiException(ErrorCode.EMAIL_TAKEN, "Email already registered");
        }
        User user = users.save(new User(UUID.randomUUID(), request.email(), passwordEncoder.encode(request.password())));
        return new TokenResponse(jwtService.issue(user.getId()), user.getId());
    }

    @Transactional(readOnly = true)
    public TokenResponse login(LoginRequest request) {
        User user = users.findByEmail(request.email())
                .filter(u -> passwordEncoder.matches(request.password(), u.getPasswordHash()))
                .orElseThrow(() -> new ApiException(ErrorCode.INVALID_CREDENTIALS, "Wrong email or password"));
        return new TokenResponse(jwtService.issue(user.getId()), user.getId());
    }
}

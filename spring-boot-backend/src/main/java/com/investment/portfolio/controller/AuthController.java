package com.investment.portfolio.controller;

import com.investment.portfolio.dto.AuthResponse;
import com.investment.portfolio.dto.LoginRequest;
import com.investment.portfolio.dto.RegisterRequest;
import com.investment.portfolio.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Authentication Controller providing login and registration endpoints.
 * Replaces the COBOL SECMGR entry point (PROCEDURE DIVISION USING SECURITY-REQUEST-AREA)
 * which dispatched SEC-VALIDATE and SEC-AUTHORIZE requests.
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest loginRequest,
                                               HttpServletRequest request) {
        AuthResponse response = authService.login(loginRequest, getClientIpAddress(request));
        return ResponseEntity.ok(response);
    }

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest registerRequest,
                                                  HttpServletRequest request) {
        AuthResponse response = authService.register(registerRequest, getClientIpAddress(request));
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    private String getClientIpAddress(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (xForwardedFor != null && !xForwardedFor.isEmpty()) {
            return xForwardedFor.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }
}

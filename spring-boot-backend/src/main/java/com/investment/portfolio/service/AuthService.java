package com.investment.portfolio.service;

import com.investment.portfolio.audit.AuditService;
import com.investment.portfolio.dto.AuthResponse;
import com.investment.portfolio.dto.LoginRequest;
import com.investment.portfolio.dto.RegisterRequest;
import com.investment.portfolio.entity.Role;
import com.investment.portfolio.entity.User;
import com.investment.portfolio.repository.RoleRepository;
import com.investment.portfolio.repository.UserRepository;
import com.investment.portfolio.security.JwtTokenProvider;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Authentication Service orchestrating the security flow.
 * Replaces the COBOL SECMGR EVALUATE dispatch logic that routed
 * between P100-VALIDATE-USER, P200-CHECK-AUTH, and P300-LOG-ACCESS.
 */
@Service
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final AuditService auditService;

    public AuthService(AuthenticationManager authenticationManager,
                       UserRepository userRepository,
                       RoleRepository roleRepository,
                       PasswordEncoder passwordEncoder,
                       JwtTokenProvider jwtTokenProvider,
                       AuditService auditService) {
        this.authenticationManager = authenticationManager;
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
        this.auditService = auditService;
    }

    @Transactional
    public AuthResponse login(LoginRequest loginRequest, String ipAddress) {
        Authentication authentication;
        try {
            authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(
                            loginRequest.getUsername(),
                            loginRequest.getPassword()
                    )
            );
        } catch (BadCredentialsException ex) {
            auditService.logLoginFailure(loginRequest.getUsername(), ipAddress, ex.getMessage());
            throw ex;
        }

        String token = jwtTokenProvider.generateToken(authentication);

        List<String> roles = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList());

        auditService.logLogin(loginRequest.getUsername(), ipAddress);

        return new AuthResponse(token, loginRequest.getUsername(), roles);
    }

    @Transactional
    public AuthResponse register(RegisterRequest registerRequest, String ipAddress) {
        if (userRepository.existsByUsername(registerRequest.getUsername())) {
            throw new IllegalArgumentException("Username is already taken");
        }

        if (userRepository.existsByEmail(registerRequest.getEmail())) {
            throw new IllegalArgumentException("Email is already in use");
        }

        User user = new User(
                registerRequest.getUsername(),
                passwordEncoder.encode(registerRequest.getPassword()),
                registerRequest.getEmail(),
                registerRequest.getFullName()
        );

        Role userRole = roleRepository.findByName("USER")
                .orElseThrow(() -> new RuntimeException("Default role USER not found"));
        user.setRoles(Collections.singleton(userRole));

        userRepository.save(user);

        auditService.logRegistration(registerRequest.getUsername(), ipAddress);

        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        registerRequest.getUsername(),
                        registerRequest.getPassword()
                )
        );

        String token = jwtTokenProvider.generateToken(authentication);
        List<String> roles = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList());

        return new AuthResponse(token, registerRequest.getUsername(), roles);
    }
}

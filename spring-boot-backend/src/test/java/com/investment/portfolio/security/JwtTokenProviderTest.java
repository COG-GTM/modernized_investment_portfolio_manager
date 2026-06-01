package com.investment.portfolio.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Unit tests for JwtTokenProvider.
 * Validates token generation, parsing, and validation logic
 * that replaces COBOL SECMGR P100-VALIDATE-USER.
 */
class JwtTokenProviderTest {

    private JwtTokenProvider jwtTokenProvider;

    private static final String SECRET = "ThisIsATestSecretKeyForJWTTokenGenerationThatShouldBeAtLeast256BitsLongForHS256Algo!!";
    private static final long EXPIRATION = 86400000L;
    private static final String ISSUER = "test-issuer";

    @BeforeEach
    void setUp() {
        jwtTokenProvider = new JwtTokenProvider(SECRET, EXPIRATION, ISSUER);
    }

    @Test
    @DisplayName("Should generate a valid JWT token from authentication")
    void generateToken_shouldReturnValidToken() {
        Authentication authentication = createAuthentication("testuser", "ROLE_USER");

        String token = jwtTokenProvider.generateToken(authentication);

        assertNotNull(token);
        assertFalse(token.isEmpty());
    }

    @Test
    @DisplayName("Should extract username from valid token")
    void getUsernameFromToken_shouldReturnCorrectUsername() {
        Authentication authentication = createAuthentication("testuser", "ROLE_USER");
        String token = jwtTokenProvider.generateToken(authentication);

        String username = jwtTokenProvider.getUsernameFromToken(token);

        assertEquals("testuser", username);
    }

    @Test
    @DisplayName("Should extract roles from valid token")
    void getRolesFromToken_shouldReturnCorrectRoles() {
        Authentication authentication = createAuthentication("testuser", "ROLE_USER");
        String token = jwtTokenProvider.generateToken(authentication);

        String roles = jwtTokenProvider.getRolesFromToken(token);

        assertEquals("ROLE_USER", roles);
    }

    @Test
    @DisplayName("Should validate a correct token successfully")
    void validateToken_shouldReturnTrueForValidToken() {
        Authentication authentication = createAuthentication("testuser", "ROLE_USER");
        String token = jwtTokenProvider.generateToken(authentication);

        boolean isValid = jwtTokenProvider.validateToken(token);

        assertTrue(isValid);
    }

    @Test
    @DisplayName("Should reject an invalid token")
    void validateToken_shouldReturnFalseForInvalidToken() {
        boolean isValid = jwtTokenProvider.validateToken("invalid.jwt.token");

        assertFalse(isValid);
    }

    @Test
    @DisplayName("Should reject an empty token")
    void validateToken_shouldReturnFalseForEmptyToken() {
        boolean isValid = jwtTokenProvider.validateToken("");

        assertFalse(isValid);
    }

    @Test
    @DisplayName("Should reject a tampered token")
    void validateToken_shouldReturnFalseForTamperedToken() {
        Authentication authentication = createAuthentication("testuser", "ROLE_USER");
        String token = jwtTokenProvider.generateToken(authentication);
        String tamperedToken = token + "tampered";

        boolean isValid = jwtTokenProvider.validateToken(tamperedToken);

        assertFalse(isValid);
    }

    @Test
    @DisplayName("Should generate token with multiple roles")
    void generateToken_shouldHandleMultipleRoles() {
        List<SimpleGrantedAuthority> authorities = List.of(
                new SimpleGrantedAuthority("ROLE_USER"),
                new SimpleGrantedAuthority("ROLE_ADMIN")
        );
        Authentication authentication = new UsernamePasswordAuthenticationToken(
                "adminuser", "password", authorities);

        String token = jwtTokenProvider.generateToken(authentication);
        String roles = jwtTokenProvider.getRolesFromToken(token);

        assertNotNull(roles);
        assertTrue(roles.contains("ROLE_USER"));
        assertTrue(roles.contains("ROLE_ADMIN"));
    }

    @Test
    @DisplayName("Should generate token using generateTokenForUser method")
    void generateTokenForUser_shouldReturnValidToken() {
        String token = jwtTokenProvider.generateTokenForUser("testuser", "ROLE_USER");

        assertNotNull(token);
        assertTrue(jwtTokenProvider.validateToken(token));
        assertEquals("testuser", jwtTokenProvider.getUsernameFromToken(token));
    }

    @Test
    @DisplayName("Should reject token signed with different key")
    void validateToken_shouldRejectTokenFromDifferentKey() {
        JwtTokenProvider otherProvider = new JwtTokenProvider(
                "AnotherCompletelyDifferentSecretKeyThatIsAlsoAtLeast256BitsLongForHS256Algorithm!!", EXPIRATION, ISSUER);

        Authentication authentication = createAuthentication("testuser", "ROLE_USER");
        String token = otherProvider.generateToken(authentication);

        boolean isValid = jwtTokenProvider.validateToken(token);
        assertFalse(isValid);
    }

    @Test
    @DisplayName("Should reject expired token")
    void validateToken_shouldRejectExpiredToken() {
        // Create provider with 0ms expiration (token expires immediately)
        JwtTokenProvider expiredProvider = new JwtTokenProvider(SECRET, 0L, ISSUER);
        Authentication authentication = createAuthentication("testuser", "ROLE_USER");
        String token = expiredProvider.generateToken(authentication);

        // Small delay to ensure expiration
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        boolean isValid = jwtTokenProvider.validateToken(token);
        assertFalse(isValid);
    }

    private Authentication createAuthentication(String username, String role) {
        List<SimpleGrantedAuthority> authorities = List.of(
                new SimpleGrantedAuthority(role));
        return new UsernamePasswordAuthenticationToken(username, "password", authorities);
    }
}

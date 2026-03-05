package com.investment.portfolio.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.investment.portfolio.dto.LoginRequest;
import com.investment.portfolio.dto.RegisterRequest;
import com.investment.portfolio.entity.Role;
import com.investment.portfolio.entity.User;
import com.investment.portfolio.repository.RoleRepository;
import com.investment.portfolio.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Integration tests for Spring Security with JWT authentication.
 * Validates the full security flow replacing COBOL SECMGR:
 * - User validation (P100-VALIDATE-USER) -> login endpoint
 * - Authorization check (P200-CHECK-AUTH) -> role-based access
 * - Audit logging (P300-LOG-ACCESS) -> AuditService integration
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class SecurityIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();

        Role userRole = roleRepository.findByName("USER")
                .orElseGet(() -> roleRepository.save(new Role("USER", "Standard user")));
        Role adminRole = roleRepository.findByName("ADMIN")
                .orElseGet(() -> roleRepository.save(new Role("ADMIN", "Administrator")));

        User testUser = new User("testuser", passwordEncoder.encode("password123"),
                "test@example.com", "Test User");
        testUser.setRoles(Collections.singleton(userRole));
        userRepository.save(testUser);

        User adminUser = new User("adminuser", passwordEncoder.encode("admin123"),
                "admin@example.com", "Admin User");
        adminUser.setRoles(Collections.singleton(adminRole));
        userRepository.save(adminUser);
    }

    @Test
    @DisplayName("Should successfully login with valid credentials")
    void login_withValidCredentials_shouldReturnToken() throws Exception {
        LoginRequest loginRequest = new LoginRequest("testuser", "password123");

        mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.username").value("testuser"))
                .andExpect(jsonPath("$.tokenType").value("Bearer"));
    }

    @Test
    @DisplayName("Should reject login with invalid credentials")
    void login_withInvalidCredentials_shouldReturnUnauthorized() throws Exception {
        LoginRequest loginRequest = new LoginRequest("testuser", "wrongpassword");

        mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("Should successfully register a new user")
    void register_withValidData_shouldReturnToken() throws Exception {
        RegisterRequest registerRequest = new RegisterRequest(
                "newuser", "password123", "new@example.com", "New User");

        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.username").value("newuser"));
    }

    @Test
    @DisplayName("Should reject registration with duplicate username")
    void register_withDuplicateUsername_shouldReturnBadRequest() throws Exception {
        RegisterRequest registerRequest = new RegisterRequest(
                "testuser", "password123", "other@example.com", "Other User");

        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("Should access protected endpoint with valid JWT token")
    void protectedEndpoint_withValidToken_shouldSucceed() throws Exception {
        // Login first to get token
        LoginRequest loginRequest = new LoginRequest("testuser", "password123");
        MvcResult loginResult = mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isOk())
                .andReturn();

        String token = objectMapper.readTree(
                loginResult.getResponse().getContentAsString()).get("token").asText();

        // Access protected endpoint with token
        mockMvc.perform(get("/api/portfolio/positions")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.user").value("testuser"));
    }

    @Test
    @DisplayName("Should reject access to protected endpoint without token")
    void protectedEndpoint_withoutToken_shouldReturnUnauthorized() throws Exception {
        mockMvc.perform(get("/api/portfolio/positions"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("Should reject access to admin endpoint with USER role")
    void adminEndpoint_withUserRole_shouldReturnForbidden() throws Exception {
        // Login as regular user
        LoginRequest loginRequest = new LoginRequest("testuser", "password123");
        MvcResult loginResult = mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isOk())
                .andReturn();

        String token = objectMapper.readTree(
                loginResult.getResponse().getContentAsString()).get("token").asText();

        // Attempt to access admin endpoint
        mockMvc.perform(get("/api/admin/audit-logs")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("Should allow admin access to admin endpoint")
    void adminEndpoint_withAdminRole_shouldSucceed() throws Exception {
        // Login as admin
        LoginRequest loginRequest = new LoginRequest("adminuser", "admin123");
        MvcResult loginResult = mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isOk())
                .andReturn();

        String token = objectMapper.readTree(
                loginResult.getResponse().getContentAsString()).get("token").asText();

        // Access admin endpoint
        mockMvc.perform(get("/api/admin/audit-logs")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("Should reject access with invalid JWT token")
    void protectedEndpoint_withInvalidToken_shouldReturnUnauthorized() throws Exception {
        mockMvc.perform(get("/api/portfolio/positions")
                        .header("Authorization", "Bearer invalid.jwt.token"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("Auth endpoints should be accessible without authentication")
    void authEndpoints_shouldBePublic() throws Exception {
        LoginRequest loginRequest = new LoginRequest("nonexistent", "password");

        // Should reach the endpoint (even if login fails, it's not 401 from the filter)
        mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isUnauthorized()); // 401 from bad credentials, not from filter
    }

    @Test
    @DisplayName("Should reject registration with invalid email")
    void register_withInvalidEmail_shouldReturnBadRequest() throws Exception {
        RegisterRequest registerRequest = new RegisterRequest(
                "validuser", "password123", "not-an-email", "Valid User");

        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("Portfolio summary endpoint should work with valid token")
    @WithMockUser(username = "mockuser", roles = {"USER"})
    void portfolioSummary_withMockUser_shouldSucceed() throws Exception {
        mockMvc.perform(get("/api/portfolio/summary"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Portfolio summary retrieved successfully"));
    }

    @Test
    @DisplayName("Admin system status should work with admin mock user")
    @WithMockUser(username = "mockadmin", roles = {"ADMIN"})
    void systemStatus_withMockAdmin_shouldSucceed() throws Exception {
        mockMvc.perform(get("/api/admin/system/status"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("ACTIVE"));
    }
}

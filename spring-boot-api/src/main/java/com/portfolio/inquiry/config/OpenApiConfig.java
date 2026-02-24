package com.portfolio.inquiry.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI portfolioInquiryOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Portfolio Inquiry API")
                        .description("""
                                REST API for the Investment Portfolio Management System.
                                
                                Migrated from COBOL/CICS online inquiry programs:
                                - INQONLN (Main CICS controller) -> InquiryController
                                - INQPORT (Portfolio position inquiry) -> GET /api/portfolios/{id}
                                - INQHIST (Transaction history inquiry) -> GET /api/portfolios/{id}/history
                                - CURSMGR (Cursor management) -> Spring Data Pageable
                                - DB2ONLN (DB2 connection pool) -> Spring Data JPA / HikariCP
                                - ERRHNDL (Error handler) -> @ControllerAdvice GlobalExceptionHandler
                                """)
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("Portfolio Management Team"))
                        .license(new License()
                                .name("MIT")))
                .servers(List.of(
                        new Server().url("http://localhost:8080").description("Local development")
                ));
    }
}

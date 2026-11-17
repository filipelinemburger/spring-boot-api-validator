package com.acme.users.api;

import java.util.List;

public record UserSearchCriteria(String email, Boolean active, List<String> roles, List<String> countries,
                                 String createdAfter, String createdBefore) {
}

package com.acme.users.domain;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface UserRepository extends JpaRepository<User, Long> {
    @Query("select u from User u where (:email is null or u.email = :email) and (:active is null or u.active = :active)")
    List<User> search(String email, Boolean active);
}

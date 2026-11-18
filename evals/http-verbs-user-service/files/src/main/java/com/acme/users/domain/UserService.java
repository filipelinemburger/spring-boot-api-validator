package com.acme.users.domain;

import com.acme.users.api.UserRequest;
import com.acme.users.api.UserSearchCriteria;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@Service
public class UserService {
    private final UserRepository users;
    private final JavaMailSender mail;

    public UserService(UserRepository users, JavaMailSender mail) {
        this.users = users;
        this.mail = mail;
    }

    @Transactional(readOnly = true)
    public User get(Long id) {
        return users.findById(id).orElseThrow(() -> new ResponseStatusException(NOT_FOUND));
    }

    @Transactional(readOnly = true)
    public List<User> all() {
        return users.findAll();
    }

    @Transactional(readOnly = true)
    public List<User> search(UserSearchCriteria criteria) {
        return users.search(criteria.email(), criteria.active());
    }

    @Transactional
    public User create(UserRequest request) {
        User user = new User();
        apply(user, request);
        return users.save(user);
    }

    /** Overwrites every field with the request values (nulls included). */
    @Transactional
    public User overwrite(Long id, UserRequest request) {
        User user = get(id);
        apply(user, request);
        return users.save(user);
    }

    @Transactional
    public void delete(Long id) {
        users.deleteById(id);
    }

    @Transactional
    public User activate(Long id) {
        User user = get(id);
        user.setActive(true);
        return user;
    }

    public void emailExport(String to) {
        StringBuilder csv = new StringBuilder("id,email\n");
        users.findAll().forEach(u -> csv.append(u.getId()).append(',').append(u.getEmail()).append('\n'));
        SimpleMailMessage message = new SimpleMailMessage();
        message.setTo(to);
        message.setSubject("User export");
        message.setText(csv.toString());
        mail.send(message);
    }

    private void apply(User user, UserRequest request) {
        user.setEmail(request.email());
        user.setDisplayName(request.displayName());
        user.setPhone(request.phone());
    }
}
